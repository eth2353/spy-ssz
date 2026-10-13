"""Native codec registration and lazy dispatch, independent of Python owners."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, TypeVar

from . import _spy
from .preset import Preset
from .schema import (
    Fork,
    ObjectKind,
    SchemaDefinition,
    module_for_codec,
    schema_definitions,
)


Decoder = Callable[[Any], Any]
Sizer = Callable[[Any], int]
Encoder = Callable[[Any, Any], int]
ArraySizer = Callable[[Any, int], int]
ArrayEncoder = Callable[[Any, int, Any], int]
CodecKey = tuple[Fork, ObjectKind, Preset]
Codec = TypeVar("Codec")


_JSON_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_DECODERS: dict[CodecKey, Decoder] = {}
_SSZ_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}
_JSON_ENCODERS: dict[CodecKey, tuple[Sizer, Encoder]] = {}
_JSON_ARRAY_ENCODERS: dict[CodecKey, tuple[ArraySizer, ArrayEncoder]] = {}


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


def register_json_array_encoder(
    fork: Fork,
    kind: ObjectKind,
    sizer: ArraySizer,
    encoder: ArrayEncoder,
    preset: Preset = Preset.MAINNET,
) -> None:
    _register(
        _JSON_ARRAY_ENCODERS,
        (fork, kind, preset),
        (sizer, encoder),
        "JSON array",
    )


def _load_builtin_codecs(fork: Fork) -> None:
    modules = {
        module_for_codec(value.codec)
        for value in schema_definitions()
        if value.fork is fork
    }
    for module in modules:
        import_module(f"{__package__}.{module}")


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


def register_schema(definition: SchemaDefinition) -> None:
    """Bind one schema's supported presets to its explicit native codec family.

    Fork modules retain responsibility for public types and JSON envelopes.
    This table only describes the native ABI; unknown families fail at import.
    """
    native = _NATIVE_CODECS[definition.codec]
    json_decoder = getattr(_spy.lib, f"spy_schema_{native.decoder}_decode_json_owned")
    ssz_decoder = getattr(_spy.lib, f"spy_schema_{native.decoder}_decode_ssz_owned")
    json_sizer = getattr(_spy.lib, f"spy_schema_{native.encoder}_json_size")
    json_encoder = getattr(_spy.lib, f"spy_schema_{native.encoder}_encode_json")
    ssz_sizer = getattr(_spy.lib, f"spy_schema_{native.encoder}_ssz_size")
    ssz_encoder = getattr(_spy.lib, f"spy_schema_{native.encoder}_encode_ssz")
    for preset_name in definition.presets:
        preset = Preset[preset_name.upper()]
        arguments = (
            (definition.fork, definition.kind, definition.schema_id, preset)
            if native.takes_kind
            else (definition.fork, definition.schema_id, preset)
        )
        register_json_decoder(
            definition.fork,
            definition.kind,
            bind_decoder(json_decoder, *arguments),
            preset,
        )
        register_ssz_decoder(
            definition.fork,
            definition.kind,
            bind_decoder(ssz_decoder, *arguments),
            preset,
        )
        register_json_encoder(
            definition.fork, definition.kind, json_sizer, json_encoder, preset
        )
        register_ssz_encoder(
            definition.fork, definition.kind, ssz_sizer, ssz_encoder, preset
        )
        if native.json_array:
            register_json_array_encoder(
                definition.fork,
                definition.kind,
                getattr(_spy.lib, f"spy_schema_{native.encoder}_json_array_size"),
                getattr(_spy.lib, f"spy_schema_{native.encoder}_encode_json_array"),
                preset,
            )
