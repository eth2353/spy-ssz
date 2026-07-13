"""Fulu native SSZ block types, reusing the Electra block schema."""

from . import _native
from .native_object import (
    Fork,
    NativeSszObject,
    ObjectKind,
    register_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)


class NativeFuluBlock(NativeSszObject):
    """A native Fulu ``SignedBeaconBlock`` backed by the Electra schema."""

    expected_fork = Fork.FULU
    expected_kind = ObjectKind.SIGNED_BEACON_BLOCK


register_decoder(
    Fork.FULU,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_fulu_decode_owned,
)
register_ssz_decoder(
    Fork.FULU,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_fulu_decode_ssz_owned,
)
register_ssz_encoder(
    Fork.FULU,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_electra_ssz_size,
    _native.lib.spy_schema_electra_encode_ssz,
)
register_json_encoder(
    Fork.FULU,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_electra_json_size,
    _native.lib.spy_schema_electra_encode_json,
)
