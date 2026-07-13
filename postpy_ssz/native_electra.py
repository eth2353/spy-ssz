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


class NativeElectraBlock(NativeSszObject):
    """A native Electra ``SignedBeaconBlock``."""

    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.SIGNED_BEACON_BLOCK


register_json_decoder(
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_electra_decode_owned,
)
register_ssz_decoder(
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_electra_decode_ssz_owned,
)
register_ssz_encoder(
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_electra_ssz_size,
    _native.lib.spy_schema_electra_encode_ssz,
)
register_json_encoder(
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_electra_json_size,
    _native.lib.spy_schema_electra_encode_json,
)
