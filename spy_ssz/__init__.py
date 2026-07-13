"""Native SPy-backed Ethereum SSZ types."""

from typing import Any

__all__ = [
    "Fork",
    "NativeDenebBlock",
    "NativeDenebAttestation",
    "NativeElectraBlock",
    "NativeFuluBlock",
    "NativeGloasAttestation",
    "NativeSszObject",
    "ObjectKind",
    "TypeDefinition",
    "decode_native_json",
    "decode_native_ssz",
    "get_type_definition",
    "get_type_shape",
    "iter_type_definitions",
]


def __getattr__(name: str) -> Any:
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
        "NativeSszObject",
        "ObjectKind",
        "decode_native_json",
        "decode_native_ssz",
    }:
        from . import native_object

        return getattr(native_object, name)
    if name in {"NativeDenebBlock", "NativeDenebAttestation"}:
        from . import native_deneb

        return getattr(native_deneb, name)
    if name == "NativeElectraBlock":
        from .native_electra import NativeElectraBlock

        return NativeElectraBlock
    if name == "NativeFuluBlock":
        from .native_fulu import NativeFuluBlock

        return NativeFuluBlock
    if name == "NativeGloasAttestation":
        from .native_gloas import NativeGloasAttestation

        return NativeGloasAttestation
    raise AttributeError(name)
