"""Python ownership layer for opaque typed SPy SSZ objects."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, ClassVar, TypeVar

import msgspec

from . import _spy
from .preset import Preset
from .schema import Fork, ObjectKind, module_for_codec, schema_definitions


def _spy_bytes(buffer: bytes | bytearray) -> tuple[Any, Any]:
    view = _spy.ffi.from_buffer(buffer)
    value = _spy.ffi.new("spy_BytesObject *")
    value.length = len(buffer)
    value.hash = 0
    value.data.p = _spy.ffi.cast("uint8_t *", view)
    return value, view


Decoder = Callable[[Any], Any]
Sizer = Callable[[Any], int]
Encoder = Callable[[Any, Any], int]
CodecKey = tuple[Fork, ObjectKind, Preset]
Codec = TypeVar("Codec")
_JSON_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}
_JSON_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}


def _register(
    registry: dict[CodecKey, Codec],
    key: CodecKey,
    value: Codec,
    encoding: str,
) -> None:
    if key in registry:
        fork, kind, preset = key
        raise ValueError(
            f"{encoding} codec already registered for "
            f"{fork.name}/{kind.name}/{preset.name}"
        )
    registry[key] = value


def _lookup_codec(
    registry: dict[CodecKey, Codec], key: CodecKey, operation: str
) -> Codec:
    codec = registry.get(key)
    if codec is None:
        fork, _, _ = key
        _load_builtin_codecs(fork)
        codec = registry.get(key)
    if codec is None:
        fork, kind, preset = key
        raise NotImplementedError(
            f"no SPy {operation} for {fork.name}/{kind.name}/{preset.name}"
        )
    return codec


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
    modules = {
        module_for_codec(value.codec)
        for value in schema_definitions()
        if value.fork is fork
    }
    for module in modules:
        import_module(f"{__package__}.{module}")


class SszObject:
    """An opaque Python owner for a typed SPy SSZ value graph."""

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
                raise TypeError("SPy SSZ containers require field values")
            decoded = type(self).from_obj(fields)
            self._handle = decoded._handle
            decoded._handle = None
        elif fields:
            raise TypeError("cannot combine a SPy handle with field values")
        else:
            self._handle = handle

    @classmethod
    def from_obj(cls, value: Any) -> "SszObject":
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
    def from_json(cls, data: bytes | bytearray | memoryview) -> "SszObject":
        return cls._decode(data, _JSON_DECODERS, "JSON")

    @classmethod
    def from_ssz(cls, data: bytes | bytearray | memoryview) -> "SszObject":
        return cls._decode(data, _SSZ_DECODERS, "SSZ")

    @classmethod
    def decode_bytes(cls, data: bytes | bytearray | memoryview) -> "SszObject":
        """Compatibility alias for the eth-remerkleable SSZ decoder name."""
        return cls.from_ssz(data)

    @classmethod
    def _decode(
        cls,
        data: bytes | bytearray | memoryview,
        decoders: dict[CodecKey, Decoder],
        encoding: str,
    ) -> "SszObject":
        if cls.expected_fork is None or cls.expected_kind is None:
            raise TypeError("use a registered concrete SPy SSZ class")
        source = bytes(data)
        source_obj, source_view = _spy_bytes(source)
        key = (cls.expected_fork, cls.expected_kind, cls.expected_preset)
        decoder = _lookup_codec(decoders, key, f"{encoding} decoder")
        handle = decoder(source_obj)
        assert source_view
        if not handle.p or not _spy.lib.spy_ssz_object_is_valid(handle):
            if handle.p:
                _spy.lib.spy_ssz_object_destroy(handle)
            raise ValueError(f"invalid {encoding} object")
        return cls(handle)

    @property
    def fork(self) -> Fork:
        return Fork(_spy.lib.spy_ssz_object_fork(self._require_handle()))

    @property
    def object_kind(self) -> ObjectKind:
        return ObjectKind(_spy.lib.spy_ssz_object_kind(self._require_handle()))

    @property
    def preset(self) -> Preset:
        return Preset(_spy.lib.spy_ssz_object_preset(self._require_handle()))

    @property
    def schema_id(self) -> int:
        return _spy.lib.spy_ssz_object_schema(self._require_handle())

    @property
    def node_count(self) -> int:
        return _spy.lib.spy_ssz_object_node_count(self._require_handle())

    def _require_handle(self) -> Any:
        if self._handle is None:
            raise RuntimeError("SPy SSZ object is closed")
        return self._handle

    def hash_tree_root(self) -> bytes:
        return self._hash_tree_root_path(0, 0, 0)

    def _hash_tree_root_path(self, first: int, second: int, depth: int) -> bytes:
        output = bytearray(32)
        output_obj, output_view = _spy_bytes(output)
        if depth == 0:
            valid = _spy.lib.spy_ssz_object_hash_tree_root(
                self._require_handle(), output_obj
            )
        else:
            valid = _spy.lib.spy_ssz_object_hash_tree_root_path(
                self._require_handle(), first, second, depth, output_obj
            )
        assert output_view
        if not valid:
            raise ValueError("SPy SSZ hashing failed")
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
        codec = _lookup_codec(encoders, key, f"{encoding} encoder")
        sizer, encoder = codec
        handle = self._require_handle()
        expected = sizer(handle)
        output = bytearray(expected)
        output_obj, output_view = _spy_bytes(output)
        written = encoder(handle, output_obj)
        assert output_view
        if written != expected:
            raise ValueError(f"SPy {encoding} encoding failed")
        return bytes(output)

    def encode_json(self) -> bytes:
        return self.to_json()

    def encode_bytes(self) -> bytes:
        """eth-remerkleable-compatible alias for SPy SSZ output."""
        return self.to_ssz()

    def close(self) -> None:
        try:
            handle = object.__getattribute__(self, "_handle")
        except AttributeError:
            return
        if handle is not None:
            self._handle = None
            self._obj_cache = None
            _spy.lib.spy_ssz_object_destroy(handle)

    def __enter__(self) -> "SszObject":
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
    if isinstance(value, SszObject):
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


def decode_json(
    data: bytes | bytearray | memoryview,
    fork: Fork,
    kind: ObjectKind,
    preset: Preset = Preset.MAINNET,
) -> SszObject:
    class RegisteredObject(SszObject):
        expected_fork = fork
        expected_kind = kind
        expected_preset = preset

    return RegisteredObject.from_json(data)


def decode_ssz(
    data: bytes | bytearray | memoryview,
    fork: Fork,
    kind: ObjectKind,
    preset: Preset = Preset.MAINNET,
) -> SszObject:
    class RegisteredObject(SszObject):
        expected_fork = fork
        expected_kind = kind
        expected_preset = preset

    return RegisteredObject.from_ssz(data)
