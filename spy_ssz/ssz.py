"""Python ownership layer for opaque typed SPy SSZ objects."""

from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from importlib import import_module
from typing import Any, Callable, ClassVar, Iterable, Self, TypeVar

import msgspec

from . import _spy
from ._repr import format_container
from .preset import Preset
from .schema import (
    Fork,
    ObjectKind,
    get_schema,
    module_for_codec,
    schema_definitions,
)


def _spy_bytes(buffer: bytes | bytearray) -> tuple[Any, Any]:
    view = _spy.ffi.from_buffer(buffer)
    value = _spy.ffi.new("spy_BytesObject *")
    value.length = len(buffer)
    value.hash = 0
    value.data.p = _spy.ffi.cast("uint8_t *", view)
    return value, view


def _compose_typed_fields(cls: type[SszObject], fields: dict[str, Any]) -> Any | None:
    from . import signing

    composer = getattr(signing, "_compose_fields")
    return composer(cls, fields)


Decoder = Callable[[Any], Any]
Sizer = Callable[[Any], int]
Encoder = Callable[[Any, Any], int]
CodecKey = tuple[Fork, ObjectKind, Preset]
Codec = TypeVar("Codec")


class _DecodeStatus(IntEnum):
    UNRECOGNIZED_FIELD = _spy.lib.SPY_SSZ_DECODE_UNRECOGNIZED_FIELD
    MALFORMED_INPUT = _spy.lib.SPY_SSZ_DECODE_MALFORMED_INPUT
    VALID = _spy.lib.SPY_SSZ_DECODE_VALID


# The largest decoder arena is ``input_length * 3 + 16 KiB`` and all native
# lengths and offsets are signed 32-bit integers.
_MAX_NATIVE_INPUT_LENGTH = ((1 << 31) - 1 - 16 * 1024) // 3
_JSON_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}
_JSON_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}


def bind_decoder(decoder: Callable[..., Any], *arguments: int) -> Decoder:
    """Bind integer schema metadata after a compiled decoder's source argument."""

    def bound(source: Any) -> Any:
        return decoder(source, *arguments)

    return bound


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

    __slots__ = ("_handle", "_obj_cache", "_value_key_cache")
    _handle: Any
    _obj_cache: Any
    _value_key_cache: tuple[int, Preset, bytes] | None
    expected_fork: ClassVar[Fork | None] = None
    expected_kind: ClassVar[ObjectKind | None] = None
    expected_preset: ClassVar[Preset] = Preset.MAINNET
    json_input_envelope_key: ClassVar[str | None] = "data"
    json_output_envelope_key: ClassVar[str | None] = "data"

    def __init__(self, handle: Any = None, **fields: Any):
        self._obj_cache: Any = None
        self._value_key_cache = None
        if handle is None:
            if not fields:
                raise TypeError("SPy SSZ containers require field values")
            if any(isinstance(value, SszObject) for value in fields.values()):
                composed = _compose_typed_fields(type(self), fields)
                if composed is not None:
                    self._handle = composed
                    return
            decoded = type(self).from_obj(fields)
            self._handle = decoded._handle
            decoded._handle = None
        elif fields:
            raise TypeError("cannot combine a SPy handle with field values")
        else:
            self._handle = handle

    @classmethod
    def from_obj(cls, value: Any) -> Self:
        if isinstance(value, dict) and any(
            isinstance(item, SszObject) for item in value.values()
        ):
            composed = _compose_typed_fields(cls, value)
            if composed is not None:
                return cls(composed)
        value = _json_compatible(value)
        if cls.json_input_envelope_key is not None:
            value = {cls.json_input_envelope_key: value}
        return cls.from_json(msgspec.json.encode(value))

    def _decoded_obj(self) -> Any:
        if self._obj_cache is None:
            value = msgspec.json.decode(self.to_json())
            if self.json_output_envelope_key is not None:
                value = value[self.json_output_envelope_key]
            self._obj_cache = value
        return self._obj_cache

    def to_obj(self) -> Any:
        return deepcopy(self._decoded_obj())

    def __getattr__(self, name: str) -> Any:
        value = self._decoded_obj()
        if isinstance(value, dict) and name in value:
            raw = value[name]
            if name in {"aggregation_bits", "committee_bits"}:
                is_bitlist = (
                    name == "aggregation_bits"
                    and self.object_kind is ObjectKind.ATTESTATION
                )
                return Bitfield.from_hex(raw, bitlist=is_bitlist)
            from .projections import project_field
            from .schema import get_schema

            definition = get_schema(self.fork, self.object_kind)
            if definition.consensus_type is not None:
                return project_field(
                    self.fork,
                    definition.consensus_type,
                    name,
                    raw,
                )
            return _project_value(raw)
        raise AttributeError(name)

    @classmethod
    def from_json(cls, data: bytes | bytearray | memoryview) -> Self:
        return cls._decode(data, _JSON_DECODERS, "JSON")

    @classmethod
    def from_ssz(cls, data: bytes | bytearray | memoryview) -> Self:
        return cls._decode(data, _SSZ_DECODERS, "SSZ")

    @classmethod
    def _decode(
        cls,
        data: bytes | bytearray | memoryview,
        decoders: dict[CodecKey, Decoder],
        encoding: str,
    ) -> Self:
        if cls.expected_fork is None or cls.expected_kind is None:
            raise TypeError("use a registered concrete SPy SSZ class")
        if len(data) > _MAX_NATIVE_INPUT_LENGTH:
            raise ValueError(
                f"{encoding} input exceeds the {_MAX_NATIVE_INPUT_LENGTH}-byte "
                "implementation limit"
            )
        source = bytes(data)
        source_obj, source_view = _spy_bytes(source)
        key = (cls.expected_fork, cls.expected_kind, cls.expected_preset)
        decoder = _lookup_codec(decoders, key, f"{encoding} decoder")
        handle = decoder(source_obj)
        assert source_view
        raw_status = (
            int(_spy.lib.spy_ssz_object_decode_status(handle))
            if handle.p
            else int(_DecodeStatus.MALFORMED_INPUT)
        )
        if raw_status != _DecodeStatus.VALID:
            error_start = _spy.lib.spy_ssz_object_error_start(handle)
            error_end = _spy.lib.spy_ssz_object_error_end(handle)
            if handle.p:
                _spy.lib.spy_ssz_object_destroy(handle)
            try:
                status = _DecodeStatus(raw_status)
            except ValueError:
                raise ValueError(f"unknown native decode status {raw_status}") from None
            if (
                encoding == "JSON"
                and status is _DecodeStatus.UNRECOGNIZED_FIELD
                and 1 <= error_start <= error_end < len(source)
            ):
                field = msgspec.json.decode(source[error_start - 1 : error_end + 1])
                raise ValueError(
                    f"unrecognized JSON object field {field!r} "
                    f"(status={status.name}, "
                    f"byte_range={error_start}:{error_end + 1})"
                )
            detail = f"status={status.name}"
            if 0 <= error_start <= error_end < len(source):
                detail += f", byte_range={error_start}:{error_end + 1}"
            raise ValueError(f"invalid {encoding} object ({detail})")
        try:
            return cls(handle)
        except BaseException:
            _spy.lib.spy_ssz_object_destroy(handle)
            raise

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

    def _value_key(self) -> tuple[int, Preset, bytes]:
        if self._value_key_cache is None:
            self._value_key_cache = (
                self.schema_id,
                self.preset,
                self.hash_tree_root(),
            )
        return self._value_key_cache

    def __repr__(self) -> str:
        definition = get_schema(self.fork, self.object_kind)
        if definition.consensus_type is not None:
            from .consensus_types import get_type_definition

            consensus_type = get_type_definition(self.fork, definition.consensus_type)
            names = (name for name, _ in consensus_type.descriptor["fields"])
            return format_container(
                type(self).__name__,
                ((name, getattr(self, name)) for name in names),
            )
        value = self._decoded_obj()
        values = value.items() if isinstance(value, dict) else (("value", value),)
        return format_container(type(self).__name__, values)

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SszObject):
            return NotImplemented
        if self is other:
            return True
        return self._value_key() == other._value_key()

    def __hash__(self) -> int:
        return hash(self._value_key())

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
        fork = type(self).expected_fork
        kind = type(self).expected_kind
        if fork is None or kind is None:
            raise TypeError("use a registered concrete SPy SSZ class")
        key = (fork, kind, type(self).expected_preset)
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

    def close(self) -> None:
        try:
            handle = object.__getattribute__(self, "_handle")
        except AttributeError:
            return
        if handle is not None:
            self._handle = None
            self._obj_cache = None
            _spy.lib.spy_ssz_object_destroy(handle)

    def __enter__(self) -> Self:
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

    def __repr__(self) -> str:
        return format_container(
            type(self).__name__,
            (("length", self._length), ("data", self._data)),
        )

    __str__ = __repr__

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
        return deepcopy(self._value)


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
    return get_ssz_type(fork, kind, preset).from_json(data)


def decode_ssz(
    data: bytes | bytearray | memoryview,
    fork: Fork,
    kind: ObjectKind,
    preset: Preset = Preset.MAINNET,
) -> SszObject:
    return get_ssz_type(fork, kind, preset).from_ssz(data)


def encode_json_array(values: Iterable[SszObject]) -> bytes:
    """Encode same-type bare JSON objects into one JSON array buffer."""
    items = tuple(values)
    if not items:
        return b"[]"
    first = items[0]
    if not isinstance(first, SszObject):
        raise TypeError("JSON array values must be concrete SPy SSZ objects")
    concrete_type = type(first)
    fork = concrete_type.expected_fork
    kind = concrete_type.expected_kind
    preset = concrete_type.expected_preset
    if fork is None or kind is None:
        raise TypeError("use registered concrete SPy SSZ objects")
    if concrete_type.json_output_envelope_key is not None:
        raise TypeError("JSON array encoding requires bare-object JSON types")
    key = (fork, kind, preset)
    for item in items:
        if not isinstance(item, SszObject):
            raise TypeError("JSON array values must be concrete SPy SSZ objects")
        item_type = type(item)
        item_key = (
            item_type.expected_fork,
            item_type.expected_kind,
            item_type.expected_preset,
        )
        if item_key != key:
            raise TypeError("JSON array values must have the same concrete SSZ type")
        item._require_handle()
    sizer, encoder = _lookup_codec(_JSON_ENCODERS, key, "JSON encoder")
    sizes = [sizer(item._require_handle()) for item in items]
    total = 2 + sum(sizes) + len(items) - 1
    if total > (1 << 31) - 1:
        raise ValueError("JSON array output exceeds the signed 32-bit size limit")
    output = bytearray(total)
    output[0] = ord("[")
    output[-1] = ord("]")
    output_view = _spy.ffi.from_buffer(output)
    output_pointer = _spy.ffi.cast("uint8_t *", output_view)
    position = 1
    for item, expected in zip(items, sizes, strict=True):
        encoded = _spy.ffi.new("spy_BytesObject *")
        encoded.length = expected
        encoded.hash = 0
        encoded.data.p = output_pointer + position
        written = encoder(item._require_handle(), encoded)
        if written != expected:
            raise ValueError("SPy JSON array encoding failed")
        position += written
        if position < total - 1:
            output[position] = ord(",")
            position += 1
    assert output_view
    return bytes(output)


def get_ssz_type(
    fork: Fork, kind: ObjectKind, preset: Preset = Preset.MAINNET
) -> type[SszObject]:
    """Resolve a registered fork/object-kind/preset to its concrete class."""
    try:
        definition = get_schema(fork, kind)
    except KeyError:
        raise NotImplementedError(
            f"no SPy schema for {fork.name}/{kind.name}/{preset.name}"
        ) from None
    preset_name = preset.name.lower()
    if preset_name not in definition.presets:
        raise NotImplementedError(
            f"no SPy schema for {fork.name}/{kind.name}/{preset.name}"
        )
    module = import_module(f"{__package__}.{module_for_codec(definition.codec)}")
    name = f"{definition.python_type}{preset.name.title()}"
    return getattr(module, name)
