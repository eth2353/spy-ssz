"""Fast SSZ proof-of-concept types and optional SPy kernels."""

from typing import Any

from .deneb import DenebSignedBeaconBlock, decode_deneb_block

__all__ = [
    "DenebSignedBeaconBlock",
    "NativeDenebBlock",
    "NativeDenebAttestation",
    "NativeElectraBlock",
    "NativeFuluBlock",
    "NativeGloasAttestation",
    "TypeDefinition",
    "decode_deneb_block",
    "decode_native_json",
    "decode_native_ssz",
    "get_type_definition",
    "iter_type_definitions",
    "hash_pair",
    "merkleize",
    "merkleize_python",
]


def __getattr__(name: str) -> Any:
    if name in {"TypeDefinition", "get_type_definition", "iter_type_definitions"}:
        from . import consensus_types

        return getattr(consensus_types, name)
    if name in {"decode_native_json", "decode_native_ssz"}:
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
    if name in {"hash_pair", "merkleize", "merkleize_python"}:
        from . import kernels

        return getattr(kernels, name)
    raise AttributeError(name)
