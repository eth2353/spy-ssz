"""Python ownership layer for opaque typed native SSZ objects."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Callable, ClassVar

import msgspec

from . import _native
from .preset import Preset


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
    ATTESTATION_DATA = 4
    AGGREGATE_AND_PROOF = 5
    SYNC_COMMITTEE_CONTRIBUTION = 6
    CONTRIBUTION_AND_PROOF = 7
    BEACON_BLOCK_CONTENTS = 8
    SIGNED_BEACON_BLOCK_CONTENTS = 9
    BLINDED_BEACON_BLOCK = 10
    SIGNED_BLINDED_BEACON_BLOCK = 11


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
CodecKey = tuple[Fork, ObjectKind, Preset]
_JSON_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}
_JSON_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}


def _register(
    registry: dict[Any, Any],
    key: CodecKey,
    value: Any,
    encoding: str,
) -> None:
    if key in registry:
        fork, kind, preset = key
        raise ValueError(
            f"{encoding} codec already registered for "
            f"{fork.name}/{kind.name}/{preset.name}"
        )
    registry[key] = value


def register_json_decoder(
    fork: Fork, kind: ObjectKind, decoder: Decoder, preset: Preset = Preset.MAINNET
) -> None:
    key = (fork, kind, preset)
    _register(_JSON_DECODERS, key, decoder, "JSON")


def register_ssz_decoder(
    fork: Fork, kind: ObjectKind, decoder: Decoder, preset: Preset = Preset.MAINNET
) -> None:
    _register(_SSZ_DECODERS, (fork, kind, preset), decoder, "SSZ")


def register_ssz_encoder(
    fork: Fork,
    kind: ObjectKind,
    sizer: Sizer,
    encoder: Encoder,
    preset: Preset = Preset.MAINNET,
) -> None:
    _register(_SSZ_ENCODERS, (fork, kind, preset), (sizer, encoder), "SSZ")


def register_json_encoder(
    fork: Fork,
    kind: ObjectKind,
    sizer: Sizer,
    encoder: Encoder,
    preset: Preset = Preset.MAINNET,
) -> None:
    _register(_JSON_ENCODERS, (fork, kind, preset), (sizer, encoder), "JSON")


def _load_builtin_codecs(fork: Fork) -> None:
    if fork is Fork.DENEB:
        from . import native_deneb  # noqa: F401
    elif fork is Fork.ELECTRA:
        from . import (  # noqa: F401
            native_blocks,
            native_electra,
            native_signing,
        )
    elif fork is Fork.FULU:
        from . import native_fulu  # noqa: F401
    elif fork is Fork.GLOAS:
        from . import native_gloas  # noqa: F401


class NativeSszObject:
    """An opaque Python owner for a typed native SSZ value graph."""

    __slots__ = ("_handle", "_obj_cache")
    expected_fork: ClassVar[Fork | None] = None
    expected_kind: ClassVar[ObjectKind | None] = None
    expected_preset: ClassVar[Preset] = Preset.MAINNET
    json_input_envelope_key: ClassVar[str | None] = "data"
    json_output_envelope_key: ClassVar[str | None] = "data"

    def __init__(self, handle: Any = None, **fields: Any):
        self._obj_cache: Any = None
        if handle is None:
            if not fields:
                raise TypeError("native SSZ containers require field values")
            decoded = type(self).from_obj(fields)
            self._handle = decoded._handle
            decoded._handle = None
        elif fields:
            raise TypeError("cannot combine a native handle with field values")
        else:
            self._handle = handle

    @classmethod
    def from_obj(cls, value: Any) -> "NativeSszObject":
        value = _json_compatible(value)
        if cls.json_input_envelope_key is not None:
            value = {cls.json_input_envelope_key: value}
        return cls.from_json(msgspec.json.encode(value))

    def to_obj(self) -> Any:
        if self._obj_cache is None:
            value = msgspec.json.decode(self.to_json())
            if self.json_output_envelope_key is not None:
                value = value[self.json_output_envelope_key]
            self._obj_cache = value
        return self._obj_cache

    def __getattr__(self, name: str) -> Any:
        value = self.to_obj()
        if isinstance(value, dict) and name in value:
            raw = value[name]
            if name in {"aggregation_bits", "committee_bits"}:
                is_bitlist = (
                    name == "aggregation_bits"
                    and self.object_kind is ObjectKind.ATTESTATION
                )
                return Bitfield.from_hex(raw, bitlist=is_bitlist)
            return _project_value(raw)
        raise AttributeError(name)

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
        decoders: dict[CodecKey, Decoder],
        encoding: str,
    ) -> "NativeSszObject":
        if cls.expected_fork is None or cls.expected_kind is None:
            raise TypeError("use a registered concrete native SSZ class")
        source = bytes(data)
        source_obj, source_view = _spy_bytes(source)
        key = (cls.expected_fork, cls.expected_kind, cls.expected_preset)
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
    def preset(self) -> Preset:
        return Preset(_native.lib.spy_ssz_object_preset(self._require_handle()))

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
        return self._hash_tree_root_path(0, 0, 0)

    def _hash_tree_root_path(self, first: int, second: int, depth: int) -> bytes:
        output = bytearray(32)
        output_obj, output_view = _spy_bytes(output)
        if depth == 0:
            valid = _native.lib.spy_ssz_object_hash_tree_root(
                self._require_handle(), output_obj
            )
        else:
            valid = _native.lib.spy_ssz_object_hash_tree_root_path(
                self._require_handle(), first, second, depth, output_obj
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
        encoders: dict[CodecKey, tuple[Sizer, Encoder]],
        encoding: str,
    ) -> bytes:
        key = (self.fork, self.object_kind, self.preset)
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
        expected = sizer(handle)
        output = bytearray(expected)
        output_obj, output_view = _spy_bytes(output)
        written = encoder(handle, output_obj)
        assert output_view
        if written != expected:
            raise ValueError(f"native {encoding} encoding failed")
        return bytes(output)

    def encode_json(self) -> bytes:
        return self.to_json()

    def encode_bytes(self) -> bytes:
        """eth-remerkleable-compatible alias for native SSZ output."""
        return self.to_ssz()

    def close(self) -> None:
        try:
            handle = object.__getattribute__(self, "_handle")
        except AttributeError:
            return
        if handle is not None:
            self._handle = None
            self._obj_cache = None
            _native.lib.spy_ssz_object_destroy(handle)

    def __enter__(self) -> "NativeSszObject":
        self._require_handle()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


class Bitfield:
    """Small immutable sequence view over Beacon API bitfield hex."""

    __slots__ = ("_data", "_length")

    def __init__(self, data: bytes, length: int):
        self._data = data
        self._length = length

    @classmethod
    def from_hex(cls, value: str, *, bitlist: bool) -> "Bitfield":
        data = bytearray.fromhex(value.removeprefix("0x"))
        length = len(data) * 8
        if bitlist:
            if not data or data[-1] == 0:
                raise ValueError("bitlist is missing its termination bit")
            marker = data[-1].bit_length() - 1
            length = (len(data) - 1) * 8 + marker
            data[-1] &= (1 << marker) - 1
        return cls(bytes(data), length)

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> bool:
        if index < 0:
            index += self._length
        if index < 0 or index >= self._length:
            raise IndexError(index)
        return bool(self._data[index // 8] & (1 << (index % 8)))

    def __iter__(self):
        for index in range(self._length):
            yield self[index]

    def count(self, value: bool = True) -> int:
        ones = sum(byte.bit_count() for byte in self._data)
        return ones if value else self._length - ones


def _project_value(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("0x"):
            return bytes.fromhex(value[2:])
        if value.isdecimal():
            return int(value)
    if isinstance(value, dict):
        return _FrozenView(value)
    if isinstance(value, list):
        return tuple(_project_value(item) for item in value)
    return value


class _FrozenView:
    __slots__ = ("_value",)

    def __init__(self, value: dict[str, Any]):
        self._value = value

    def __getattr__(self, name: str) -> Any:
        try:
            return _project_value(self._value[name])
        except KeyError:
            raise AttributeError(name) from None

    def to_obj(self) -> dict[str, Any]:
        return self._value


def _json_compatible(value: Any) -> Any:
    if isinstance(value, NativeSszObject):
        return value.to_obj()
    if hasattr(value, "to_obj"):
        return _json_compatible(value.to_obj())
    if isinstance(value, bytes):
        return f"0x{value.hex()}"
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


def decode_native_json(
    data: bytes | bytearray | memoryview,
    fork: Fork,
    kind: ObjectKind,
    preset: Preset = Preset.MAINNET,
) -> NativeSszObject:
    class RegisteredObject(NativeSszObject):
        expected_fork = fork
        expected_kind = kind
        expected_preset = preset

    return RegisteredObject.from_json(data)


def decode_native_ssz(
    data: bytes | bytearray | memoryview,
    fork: Fork,
    kind: ObjectKind,
    preset: Preset = Preset.MAINNET,
) -> NativeSszObject:
    class RegisteredObject(NativeSszObject):
        expected_fork = fork
        expected_kind = kind
        expected_preset = preset

    return RegisteredObject.from_ssz(data)
