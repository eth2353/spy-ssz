"""Fulu native SSZ block types, reusing the Electra block schema."""

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


class NativeFuluBlock(NativeSszObject):
    """A native Fulu ``SignedBeaconBlock`` backed by the Electra schema."""

    expected_fork = Fork.FULU
    expected_kind = ObjectKind.SIGNED_BEACON_BLOCK


NativeFuluBlockMainnet = NativeFuluBlock


class NativeFuluBlockMinimal(NativeFuluBlock):
    expected_preset = Preset.MINIMAL


class NativeFuluBlockGnosis(NativeFuluBlock):
    expected_preset = Preset.GNOSIS


for _preset in Preset:
    register_json_decoder(
        Fork.FULU,
        ObjectKind.SIGNED_BEACON_BLOCK,
        lambda source, preset=_preset: (
            _native.lib.spy_schema_fulu_decode_preset_owned(source, preset)
        ),
        _preset,
    )
    register_ssz_decoder(
        Fork.FULU,
        ObjectKind.SIGNED_BEACON_BLOCK,
        lambda source, preset=_preset: (
            _native.lib.spy_schema_fulu_decode_ssz_preset_owned(source, preset)
        ),
        _preset,
    )
    register_ssz_encoder(
        Fork.FULU,
        ObjectKind.SIGNED_BEACON_BLOCK,
        _native.lib.spy_schema_electra_ssz_size,
        _native.lib.spy_schema_electra_encode_ssz,
        _preset,
    )
    register_json_encoder(
        Fork.FULU,
        ObjectKind.SIGNED_BEACON_BLOCK,
        _native.lib.spy_schema_electra_json_size,
        _native.lib.spy_schema_electra_encode_json,
        _preset,
    )
