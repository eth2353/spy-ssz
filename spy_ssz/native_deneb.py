"""Deneb native SSZ types."""

from __future__ import annotations

from . import _native
from .native_object import (
    Fork,
    NativeSszObject,
    ObjectKind,
    register_json_decoder,
    register_ssz_decoder,
)


class NativeDenebBlock(NativeSszObject):
    """A typed native Deneb ``SignedBeaconBlock``."""

    expected_fork = Fork.DENEB
    expected_kind = ObjectKind.SIGNED_BEACON_BLOCK


class NativeDenebAttestation(NativeSszObject):
    """A typed native Deneb ``Attestation``."""

    expected_fork = Fork.DENEB
    expected_kind = ObjectKind.ATTESTATION


register_json_decoder(
    Fork.DENEB,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_deneb_decode_owned,
)
register_ssz_decoder(
    Fork.DENEB,
    ObjectKind.SIGNED_BEACON_BLOCK,
    _native.lib.spy_schema_deneb_decode_ssz_owned,
)
register_json_decoder(
    Fork.DENEB,
    ObjectKind.ATTESTATION,
    _native.lib.spy_schema_deneb_decode_attestation_owned,
)
register_ssz_decoder(
    Fork.DENEB,
    ObjectKind.ATTESTATION,
    _native.lib.spy_schema_deneb_decode_attestation_ssz_owned,
)
