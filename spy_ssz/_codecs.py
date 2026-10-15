"""Immutable native codec descriptors, independent of public Python types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from . import _spy
from .preset import Preset
from .schema import Fork, ObjectKind, SchemaDefinition, schema_definitions

Decoder = Callable[[Any], Any]
Sizer = Callable[[Any], int]
Encoder = Callable[[Any, Any], int]
ArraySizer = Callable[[Any, int], int]
ArrayEncoder = Callable[[Any, int, Any], int]
CodecKey = tuple[Fork, ObjectKind, Preset]


@dataclass(frozen=True)
class Codec:
    """All operations for one fork, object kind, and preset."""

    json_decoder: Decoder
    ssz_decoder: Decoder
    json_encoder: tuple[Sizer, Encoder]
    ssz_encoder: tuple[Sizer, Encoder]
    json_array_encoder: tuple[ArraySizer, ArrayEncoder] | None


def bind_decoder(decoder: Callable[..., Any], *arguments: int) -> Decoder:
    def bound(source: Any) -> Any:
        return decoder(source, *arguments)

    return bound


@dataclass(frozen=True)
class _NativeCodec:
    """C symbol families and the two ABI differences between codec families."""

    decoder: str
    encoder: str
    takes_kind: bool = True
    json_array: bool = False


_BLOCK = _NativeCodec("block", "electra", takes_kind=False)
_SIGNING = _NativeCodec("signing", "signing", json_array=True)
_BLOCK_CONTAINERS = _NativeCodec(
    "block_containers", "block_containers", json_array=True
)
_NATIVE_CODECS = {
    "electra_block": _BLOCK,
    "fulu_block": _BLOCK,
    "signing": _SIGNING,
    "fulu_signing": _SIGNING,
    "block_containers": _BLOCK_CONTAINERS,
    "fulu_block_containers": _BLOCK_CONTAINERS,
    "gloas_block": _NativeCodec("gloas_block", "gloas"),
    "gloas_signing": _NativeCodec("gloas_signing", "signing", json_array=True),
    "gloas_payload_envelope": _NativeCodec(
        "gloas_payload_envelope", "gloas_payload_envelope"
    ),
}


def _build_codec(definition: SchemaDefinition, preset: Preset) -> Codec:
    native = _NATIVE_CODECS[definition.codec]
    arguments = (
        (definition.fork, definition.kind, definition.schema_id, preset)
        if native.takes_kind
        else (definition.fork, definition.schema_id, preset)
    )

    def symbol(family: str, operation: str) -> Any:
        return getattr(_spy.lib, f"spy_schema_{family}_{operation}")

    return Codec(
        json_decoder=bind_decoder(
            symbol(native.decoder, "decode_json_owned"), *arguments
        ),
        ssz_decoder=bind_decoder(
            symbol(native.decoder, "decode_ssz_owned"), *arguments
        ),
        json_encoder=(
            symbol(native.encoder, "json_size"),
            symbol(native.encoder, "encode_json"),
        ),
        ssz_encoder=(
            symbol(native.encoder, "ssz_size"),
            symbol(native.encoder, "encode_ssz"),
        ),
        json_array_encoder=(
            (
                symbol(native.encoder, "json_array_size"),
                symbol(native.encoder, "encode_json_array"),
            )
            if native.json_array
            else None
        ),
    )


_CODECS: dict[CodecKey, Codec] = {
    (definition.fork, definition.kind, preset): _build_codec(definition, preset)
    for definition in schema_definitions()
    for preset_name in definition.presets
    for preset in (Preset[preset_name.upper()],)
}


def get_codec(key: CodecKey) -> Codec:
    try:
        return _CODECS[key]
    except KeyError:
        fork, kind, preset = key
        raise NotImplementedError(
            f"no SPy codec for {fork.name}/{kind.name}/{preset.name}"
        ) from None
