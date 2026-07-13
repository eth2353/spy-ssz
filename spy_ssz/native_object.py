"""Python ownership layer for opaque typed native SSZ objects."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Callable, ClassVar

from . import _native


class Fork(IntEnum):
    """Chronological consensus-fork identifiers; keep in sync with metadata.spy."""

    PHASE0 = 0
    ALTAIR = 1
    BELLATRIX = 2
    CAPELLA = 3
    DENEB = 4
    ELECTRA = 5
    FULU = 6
    GLOAS = 7
    HEZE = 8


class ObjectKind(IntEnum):
    SIGNED_BEACON_BLOCK = 1
    BEACON_BLOCK = 2
    ATTESTATION = 3


def _spy_bytes(buffer: bytes | bytearray) -> tuple[Any, Any]:
    view = _native.ffi.from_buffer(buffer)
    value = _native.ffi.new("spy_BytesObject *")
    value.length = len(buffer)
    value.hash = 0
    value.data.p = _native.ffi.cast("uint8_t *", view)
    return value, view


Decoder = Callable[[Any], Any]
Sizer = Callable[[Any], int]
Encoder = Callable[[Any, Any], int]
_JSON_DECODERS: dict[tuple[Fork, ObjectKind], Decoder] = {}
_SSZ_DECODERS: dict[tuple[Fork, ObjectKind], Decoder] = {}
_SSZ_ENCODERS: dict[tuple[Fork, ObjectKind], tuple[Sizer, Encoder]] = {}
_JSON_ENCODERS: dict[tuple[Fork, ObjectKind], tuple[Sizer, Encoder]] = {}


def _register(
    registry: dict[Any, Any],
    key: tuple[Fork, ObjectKind],
    value: Any,
    encoding: str,
) -> None:
    if key in registry:
        fork, kind = key
        raise ValueError(
            f"{encoding} codec already registered for {fork.name}/{kind.name}"
        )
    registry[key] = value


def register_json_decoder(fork: Fork, kind: ObjectKind, decoder: Decoder) -> None:
    key = (fork, kind)
    _register(_JSON_DECODERS, key, decoder, "JSON")


def register_ssz_decoder(fork: Fork, kind: ObjectKind, decoder: Decoder) -> None:
    _register(_SSZ_DECODERS, (fork, kind), decoder, "SSZ")


def register_ssz_encoder(
    fork: Fork, kind: ObjectKind, sizer: Sizer, encoder: Encoder
) -> None:
    _register(_SSZ_ENCODERS, (fork, kind), (sizer, encoder), "SSZ")


def register_json_encoder(
    fork: Fork, kind: ObjectKind, sizer: Sizer, encoder: Encoder
) -> None:
    _register(_JSON_ENCODERS, (fork, kind), (sizer, encoder), "JSON")


def _load_builtin_codecs(fork: Fork) -> None:
    if fork is Fork.DENEB:
        from . import native_deneb  # noqa: F401
    elif fork is Fork.ELECTRA:
        from . import native_electra  # noqa: F401
    elif fork is Fork.FULU:
        from . import native_fulu  # noqa: F401
    elif fork is Fork.GLOAS:
        from . import native_gloas  # noqa: F401


class NativeSszObject:
    """An opaque Python owner for a typed native SSZ value graph."""

    __slots__ = ("_handle",)
    expected_fork: ClassVar[Fork | None] = None
    expected_kind: ClassVar[ObjectKind | None] = None

    def __init__(self, handle: Any):
        self._handle = handle

    @classmethod
    def from_json(cls, data: bytes | bytearray | memoryview) -> "NativeSszObject":
        return cls._decode(data, _JSON_DECODERS, "JSON")

    @classmethod
    def from_ssz(cls, data: bytes | bytearray | memoryview) -> "NativeSszObject":
        return cls._decode(data, _SSZ_DECODERS, "SSZ")

    @classmethod
    def decode_bytes(cls, data: bytes | bytearray | memoryview) -> "NativeSszObject":
        """Compatibility alias for the eth-remerkleable SSZ decoder name."""
        return cls.from_ssz(data)

    @classmethod
    def _decode(
        cls,
        data: bytes | bytearray | memoryview,
        decoders: dict[tuple[Fork, ObjectKind], Decoder],
        encoding: str,
    ) -> "NativeSszObject":
        if cls.expected_fork is None or cls.expected_kind is None:
            raise TypeError("use a registered concrete native SSZ class")
        source = bytes(data)
        source_obj, source_view = _spy_bytes(source)
        key = (cls.expected_fork, cls.expected_kind)
        decoder = decoders.get(key)
        if decoder is None:
            _load_builtin_codecs(cls.expected_fork)
            decoder = decoders.get(key)
        if decoder is None:
            raise NotImplementedError(
                f"no native {encoding} decoder for "
                f"{cls.expected_fork.name}/{cls.expected_kind.name}"
            )
        handle = decoder(source_obj)
        assert source_view
        if not handle.p or not _native.lib.spy_ssz_object_is_valid(handle):
            if handle.p:
                _native.lib.spy_ssz_object_destroy(handle)
            raise ValueError(f"invalid {encoding} object")
        return cls(handle)

    @property
    def fork(self) -> Fork:
        return Fork(_native.lib.spy_ssz_object_fork(self._require_handle()))

    @property
    def object_kind(self) -> ObjectKind:
        return ObjectKind(_native.lib.spy_ssz_object_kind(self._require_handle()))

    @property
    def schema_id(self) -> int:
        return _native.lib.spy_ssz_object_schema(self._require_handle())

    @property
    def node_count(self) -> int:
        return _native.lib.spy_ssz_object_node_count(self._require_handle())

    def _require_handle(self) -> Any:
        if self._handle is None:
            raise RuntimeError("native SSZ object is closed")
        return self._handle

    def hash_tree_root(self) -> bytes:
        output = bytearray(32)
        output_obj, output_view = _spy_bytes(output)
        valid = _native.lib.spy_ssz_object_hash_tree_root(
            self._require_handle(), output_obj
        )
        assert output_view
        if not valid:
            raise ValueError("native SSZ hashing failed")
        return bytes(output)

    def to_ssz(self) -> bytes:
        return self._encode(_SSZ_ENCODERS, "SSZ")

    def to_json(self) -> bytes:
        """Encode a compact Beacon API ``{\"data\": ...}`` JSON response."""
        return self._encode(_JSON_ENCODERS, "JSON")

    def _encode(
        self,
        encoders: dict[tuple[Fork, ObjectKind], tuple[Sizer, Encoder]],
        encoding: str,
    ) -> bytes:
        key = (self.fork, self.object_kind)
        codec = encoders.get(key)
        if codec is None:
            _load_builtin_codecs(self.fork)
            codec = encoders.get(key)
        if codec is None:
            raise NotImplementedError(
                f"no native {encoding} encoder for "
                f"{self.fork.name}/{self.object_kind.name}"
            )
        sizer, encoder = codec
        handle = self._require_handle()
        output = bytearray(sizer(handle))
        output_obj, output_view = _spy_bytes(output)
        written = encoder(handle, output_obj)
        assert output_view
        if written != len(output):
            raise ValueError(f"native {encoding} encoding failed")
        return bytes(output)

    def encode_json(self) -> bytes:
        return self.to_json()

    def encode_bytes(self) -> bytes:
        """eth-remerkleable-compatible alias for native SSZ output."""
        return self.to_ssz()

    def close(self) -> None:
        handle = self._handle
        if handle is not None:
            self._handle = None
            _native.lib.spy_ssz_object_destroy(handle)

    def __enter__(self) -> "NativeSszObject":
        self._require_handle()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


def decode_native_json(
    data: bytes | bytearray | memoryview, fork: Fork, kind: ObjectKind
) -> NativeSszObject:
    class RegisteredObject(NativeSszObject):
        expected_fork = fork
        expected_kind = kind

    return RegisteredObject.from_json(data)


def decode_native_ssz(
    data: bytes | bytearray | memoryview, fork: Fork, kind: ObjectKind
) -> NativeSszObject:
    class RegisteredObject(NativeSszObject):
        expected_fork = fork
        expected_kind = kind

    return RegisteredObject.from_ssz(data)
