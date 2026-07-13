"""Native SPy-backed Ethereum SSZ types."""

from typing import Any

__all__ = [
    "Fork",
    "Attestation",
    "AttestationData",
    "AggregateAndProof",
    "ContributionAndProof",
    "NativeDenebBlock",
    "NativeDenebAttestation",
    "NativeElectraBlock",
    "NativeFuluBlock",
    "NativeGloasAttestation",
    "NativeSszObject",
    "ObjectKind",
    "Preset",
    "PresetConfig",
    "SyncCommitteeContribution",
    "ElectraBeaconBlockContentsMainnet",
    "ElectraBeaconBlockContentsMinimal",
    "ElectraBeaconBlockContentsGnosis",
    "ElectraBlindedBeaconBlockMainnet",
    "ElectraBlindedBeaconBlockMinimal",
    "ElectraBlindedBeaconBlockGnosis",
    "TypeDefinition",
    "decode_native_json",
    "decode_native_ssz",
    "get_type_definition",
    "get_type_shape",
    "iter_type_definitions",
    "load_preset",
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
    if name in {"Preset", "PresetConfig", "load_preset"}:
        from . import preset

        return getattr(preset, name)
    if name in {
        "Attestation",
        "AttestationData",
        "AggregateAndProof",
        "ContributionAndProof",
        "SyncCommitteeContribution",
    } or name.endswith(("Mainnet", "Minimal", "Gnosis")):
        from . import native_signing

        if hasattr(native_signing, name):
            return getattr(native_signing, name)
    if name.startswith("Electra") and (
        "BeaconBlockContents" in name or "BlindedBeaconBlock" in name
    ):
        from . import native_blocks

        if hasattr(native_blocks, name):
            return getattr(native_blocks, name)
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
