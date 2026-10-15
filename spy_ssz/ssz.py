"""Python ownership layer for opaque typed SPy SSZ objects."""

from __future__ import annotations

from collections.abc import Buffer, Iterable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from importlib import import_module
from threading import RLock
from typing import Any, ClassVar, Self

import msgspec

from . import _spy
from ._codecs import get_codec
from ._composition import _compose_fields
from ._json_policy import json_input, json_output
from ._native import (
    _MAX_NATIVE_INPUT_LENGTH,
    _MAX_NATIVE_SIZE,
    _spy_bytes,
    decode_owned,
    input_bytes,
)
from ._repr import format_container
from ._projection import project_native_field
from ._values import Bitfield as Bitfield
from ._values import _json_compatible, _project_value
from .preset import Preset
from .schema import (
    Fork,
    ObjectKind,
    get_schema,
    module_for_codec,
)


class SszObject:
    """An opaque Python owner for a typed SPy SSZ value graph."""

    __slots__ = (
        "_handle",
        "_json_size_cache",
        "_lock",
        "_obj_cache",
        "_projection_cache",
        "_ssz_size_cache",
        "_value_key_cache",
    )
    _handle: Any
    _json_size_cache: int | None
    _lock: RLock
    _obj_cache: Any
    _projection_cache: dict[str, Any] | None
    _ssz_size_cache: int | None
    _value_key_cache: tuple[int, Preset, bytes] | None
    expected_fork: ClassVar[Fork | None] = None
    expected_kind: ClassVar[ObjectKind | None] = None
    expected_preset: ClassVar[Preset] = Preset.MAINNET
    json_input_envelope_key: ClassVar[str | None] = "data"
    json_output_envelope_key: ClassVar[str | None] = "data"
    json_decoder_handles_envelope: ClassVar[bool] = True
    json_encoder_handles_envelope: ClassVar[bool] = True
    json_output_metadata: ClassVar[Mapping[str, Any] | None] = None

    def _initialize_owner(self, handle: Any) -> None:
        self._lock = RLock()
        self._handle = None
        self._json_size_cache = None
        self._obj_cache = None
        self._projection_cache = None
        self._ssz_size_cache = None
        self._value_key_cache = None
        self._handle = handle

    def __init__(self, handle: Any = None, **fields: Any):
        SszObject._initialize_owner(self, None)
        if handle is None:
            if not fields:
                raise TypeError("SPy SSZ containers require field values")
            if any(isinstance(value, SszObject) for value in fields.values()):
                composed = _compose_fields(type(self), fields)
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
    def _from_owned_handle(cls, handle: Any) -> Self:
        """Adopt a new allocation without invoking public field constructors."""
        result = None
        try:
            result = object.__new__(cls)
            SszObject._initialize_owner(result, handle)
            return result
        except BaseException:
            # A partially initialized owner may already have adopted the handle.
            try:
                adopted = (
                    result is not None
                    and object.__getattribute__(result, "_handle") is handle
                )
            except AttributeError:
                adopted = False
            if adopted:
                assert result is not None
                result.close()
            else:
                _spy.lib.spy_ssz_object_destroy(handle)
            raise

    @classmethod
    def from_obj(cls, value: Any) -> Self:
        if isinstance(value, dict) and any(
            isinstance(item, SszObject) for item in value.values()
        ):
            composed = _compose_fields(cls, value)
            if composed is not None:
                return cls._from_owned_handle(composed)
        value = _json_compatible(value)
        if cls.json_input_envelope_key is not None:
            value = {cls.json_input_envelope_key: value}
        return cls.from_json(msgspec.json.encode(value))

    def _decoded_obj(self) -> Any:
        with self._lock:
            if self._obj_cache is None:
                value = msgspec.json.decode(self.to_json())
                if self.json_output_envelope_key is not None:
                    value = value[self.json_output_envelope_key]
                self._obj_cache = value
            return self._obj_cache

    def to_obj(self) -> Any:
        return deepcopy(self._decoded_obj())

    def __getattr__(self, name: str) -> Any:
        with self._use_handle() as handle:
            if self._projection_cache is not None and name in self._projection_cache:
                return self._projection_cache[name]
            fork = Fork(_spy.lib.spy_ssz_object_fork(handle))
            kind = ObjectKind(_spy.lib.spy_ssz_object_kind(handle))
            definition = get_schema(fork, kind)
            if definition.consensus_type is not None:
                try:
                    result = project_native_field(
                        handle, fork, definition.consensus_type, name
                    )
                except KeyError:
                    raise AttributeError(name) from None
                if name in {"aggregation_bits", "committee_bits"}:
                    result = Bitfield.from_hex(
                        f"0x{result.hex()}",
                        bitlist=name == "aggregation_bits"
                        and kind is ObjectKind.ATTESTATION,
                    )
                if self._projection_cache is None:
                    self._projection_cache = {}
                self._projection_cache[name] = result
                return result
        # API-only containers have no consensus descriptor in the catalog.
        value = self._decoded_obj()
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
    def from_json(cls, data: Buffer) -> Self:
        return cls._decode(data, "JSON")

    @classmethod
    def from_ssz(cls, data: Buffer) -> Self:
        return cls._decode(data, "SSZ")

    @classmethod
    def _decode(
        cls,
        data: Buffer,
        encoding: str,
    ) -> Self:
        if cls.expected_fork is None or cls.expected_kind is None:
            raise TypeError("use a registered concrete SPy SSZ class")
        source = input_bytes(data, encoding, _MAX_NATIVE_INPUT_LENGTH)
        if encoding == "JSON":
            source = json_input(cls, source)
        key = (cls.expected_fork, cls.expected_kind, cls.expected_preset)
        codec = get_codec(key)
        decoder = codec.json_decoder if encoding == "JSON" else codec.ssz_decoder
        handle = decode_owned(source, decoder, encoding)
        result = cls._from_owned_handle(handle)
        # Canonical SSZ input already gives the exact immutable output size.
        if encoding == "SSZ":
            result._ssz_size_cache = len(source)
        return result

    @property
    def fork(self) -> Fork:
        with self._use_handle() as handle:
            return Fork(_spy.lib.spy_ssz_object_fork(handle))

    @property
    def object_kind(self) -> ObjectKind:
        with self._use_handle() as handle:
            return ObjectKind(_spy.lib.spy_ssz_object_kind(handle))

    @property
    def preset(self) -> Preset:
        with self._use_handle() as handle:
            return Preset(_spy.lib.spy_ssz_object_preset(handle))

    @property
    def schema_id(self) -> int:
        with self._use_handle() as handle:
            return _spy.lib.spy_ssz_object_schema(handle)

    @property
    def node_count(self) -> int:
        with self._use_handle() as handle:
            return _spy.lib.spy_ssz_object_node_count(handle)

    def _require_handle(self) -> Any:
        if self._handle is None:
            raise RuntimeError("SPy SSZ object is closed")
        return self._handle

    @contextmanager
    def _use_handle(self) -> Iterator[Any]:
        """Keep this object's native allocation alive for one operation."""
        with self._lock:
            yield self._require_handle()

    def hash_tree_root(self) -> bytes:
        return self._hash_tree_root_path(0, 0, 0)

    def _value_key(self) -> tuple[int, Preset, bytes]:
        with self._lock:
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

    def __copy__(self) -> Self:
        """Copy the value into an independently owned native allocation."""
        return type(self).from_ssz(self.to_ssz())

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        result = self.__copy__()
        memo[id(self)] = result
        return result

    def _hash_tree_root_path(self, first: int, second: int, depth: int) -> bytes:
        output = bytearray(32)
        output_obj, output_view = _spy_bytes(output)
        with self._use_handle() as handle:
            if depth == 0:
                valid = _spy.lib.spy_ssz_object_hash_tree_root(handle, output_obj)
            else:
                valid = _spy.lib.spy_ssz_object_hash_tree_root_path(
                    handle, first, second, depth, output_obj
                )
        assert output_view
        if not valid:
            raise ValueError("SPy SSZ hashing failed")
        return bytes(output)

    def to_ssz(self) -> bytes:
        return self._encode("SSZ")

    def to_json(self) -> bytes:
        """Encode the compact Beacon API JSON representation for this object."""
        encoded = self._encode("JSON")
        return json_output(type(self), encoded)

    def _encode(
        self,
        encoding: str,
    ) -> bytes:
        fork = type(self).expected_fork
        kind = type(self).expected_kind
        if fork is None or kind is None:
            raise TypeError("use a registered concrete SPy SSZ class")
        key = (fork, kind, type(self).expected_preset)
        codec = get_codec(key)
        sizer, encoder = codec.json_encoder if encoding == "JSON" else codec.ssz_encoder
        with self._use_handle() as handle:
            size_cache = "_ssz_size_cache" if encoding == "SSZ" else "_json_size_cache"
            expected = getattr(self, size_cache)
            if expected is None:
                expected = sizer(handle)
                setattr(self, size_cache, expected)
            if expected < 0:
                raise ValueError(f"SPy {encoding} sizing failed")
            output = bytearray(expected)
            output_obj, output_view = _spy_bytes(output)
            written = encoder(handle, output_obj)
        assert output_view
        if written != expected:
            raise ValueError(f"SPy {encoding} encoding failed")
        return bytes(output)

    def close(self) -> None:
        try:
            lock = object.__getattribute__(self, "_lock")
        except AttributeError:
            return
        with lock:
            try:
                handle = object.__getattribute__(self, "_handle")
            except AttributeError:
                return
            if handle is not None:
                self._handle = None
                self._obj_cache = None
                self._projection_cache = None
                _spy.lib.spy_ssz_object_destroy(handle)

    def __enter__(self) -> Self:
        with self._lock:
            self._require_handle()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


def decode_json(
    data: Buffer,
    fork: Fork,
    kind: ObjectKind,
    preset: Preset = Preset.MAINNET,
) -> SszObject:
    return get_ssz_type(fork, kind, preset).from_json(data)


def decode_ssz(
    data: Buffer,
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
    if len(items) > _MAX_NATIVE_SIZE:
        raise ValueError("JSON array exceeds the signed 32-bit item-count limit")
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
    codec = get_codec(key)
    batch_codec = codec.json_array_encoder
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

    # CFFI releases the GIL during native calls. Lock every distinct owner in a
    # stable order so no item can be closed while its pointer is in the batch.
    unique_items = {id(item): item for item in items}
    with ExitStack() as stack:
        owned_handles = {
            item_id: stack.enter_context(item._use_handle())
            for item_id, item in sorted(unique_items.items())
        }
        item_handles = [owned_handles[id(item)] for item in items]
        if batch_codec is not None:
            handles = _spy.ffi.new("spy_raw_ssz_ptr[]", item_handles)
            batch_sizer, batch_encoder = batch_codec
            total = batch_sizer(handles, len(items))
            if total < 0:
                raise ValueError(
                    "JSON array output exceeds the signed 32-bit size limit"
                )
            output = bytearray(total)
            output_obj, output_view = _spy_bytes(output)
            written = batch_encoder(handles, len(items), output_obj)
            assert output_view
            if written != total:
                raise ValueError("SPy JSON array encoding failed")
            return bytes(output)

        item_sizer, item_encoder = codec.json_encoder
        sizes = [item_sizer(handle) for handle in item_handles]
        if any(size < 0 for size in sizes):
            raise ValueError("SPy JSON array sizing failed")
        total = len(items) + 1 + sum(sizes)
        if total > _MAX_NATIVE_SIZE:
            raise ValueError("JSON array output exceeds the signed 32-bit size limit")
        output = bytearray(total)
        output[0] = ord("[")
        output[-1] = ord("]")
        output_view = _spy.ffi.from_buffer(output)
        output_pointer = _spy.ffi.cast("uint8_t *", output_view)
        position = 1
        for handle, expected in zip(item_handles, sizes, strict=True):
            encoded = _spy.ffi.new("spy_BytesObject *")
            encoded.length = expected
            encoded.hash = 0
            encoded.data.p = output_pointer + position
            written = item_encoder(handle, encoded)
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
