"""Compiled SPy-backed Ethereum SSZ types."""

from importlib import import_module
from typing import Any

from .schema import module_for_codec, schema_definitions


_SCHEMA_EXPORTS: dict[str, str] = {}
for _definition in schema_definitions():
    _module = module_for_codec(_definition.codec)
    _SCHEMA_EXPORTS[_definition.python_type] = _module
    for _preset in _definition.presets:
        _SCHEMA_EXPORTS[f"{_definition.python_type}{_preset.title()}"] = _module

__all__ = [
    "Fork",
    "Checkpoint",
    "SszObject",
    "ObjectKind",
    "Preset",
    "PresetConfig",
    "TypeDefinition",
    "decode_json",
    "decode_ssz",
    "get_type_definition",
    "get_type_shape",
    "get_ssz_type",
    "iter_type_definitions",
    "load_preset",
] + sorted(_SCHEMA_EXPORTS)


def __getattr__(name: str) -> Any:
    if name == "Checkpoint":
        from .projections import Checkpoint

        return Checkpoint
    if name in {
        "TypeDefinition",
        "get_type_definition",
        "get_type_shape",
        "iter_type_definitions",
    }:
        from . import consensus_types

        return getattr(consensus_types, name)
    if name in {
        "Fork",
        "SszObject",
        "ObjectKind",
        "decode_json",
        "decode_ssz",
        "get_ssz_type",
    }:
        from . import ssz

        return getattr(ssz, name)
    if name in {"Preset", "PresetConfig", "load_preset"}:
        from . import preset

        return getattr(preset, name)
    module_name = _SCHEMA_EXPORTS.get(name)
    if module_name is not None:
        module = import_module(f"{__name__}.{module_name}")
        return getattr(module, name)
    raise AttributeError(name)
