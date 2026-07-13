"""Electra native SSZ block types."""

from . import _native
from .native_object import (
    Fork,
    NativeSszObject,
    ObjectKind,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)
from .preset import Preset


class NativeElectraBlock(NativeSszObject):
    """A native Electra ``SignedBeaconBlock``."""

    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.SIGNED_BEACON_BLOCK


NativeElectraBlockMainnet = NativeElectraBlock


class NativeElectraBlockMinimal(NativeElectraBlock):
    expected_preset = Preset.MINIMAL


class NativeElectraBlockGnosis(NativeElectraBlock):
    expected_preset = Preset.GNOSIS


for _preset in Preset:
    register_json_decoder(
        Fork.ELECTRA,
        ObjectKind.SIGNED_BEACON_BLOCK,
        lambda source, preset=_preset: (
            _native.lib.spy_schema_electra_decode_preset_owned(source, preset)
        ),
        _preset,
    )
    register_ssz_decoder(
        Fork.ELECTRA,
        ObjectKind.SIGNED_BEACON_BLOCK,
        lambda source, preset=_preset: (
            _native.lib.spy_schema_electra_decode_ssz_preset_owned(source, preset)
        ),
        _preset,
    )
    register_ssz_encoder(
        Fork.ELECTRA,
        ObjectKind.SIGNED_BEACON_BLOCK,
        _native.lib.spy_schema_electra_ssz_size,
        _native.lib.spy_schema_electra_encode_ssz,
        _preset,
    )
    register_json_encoder(
        Fork.ELECTRA,
        ObjectKind.SIGNED_BEACON_BLOCK,
        _native.lib.spy_schema_electra_json_size,
        _native.lib.spy_schema_electra_encode_json,
        _preset,
    )
