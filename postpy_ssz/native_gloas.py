"""Gloas native SSZ types."""

from . import _native
from .native_object import (
    Fork,
    NativeSszObject,
    ObjectKind,
    register_decoder,
    register_ssz_decoder,
)


class NativeGloasAttestation(NativeSszObject):
    """A typed native progressive Gloas ``Attestation``."""

    expected_fork = Fork.GLOAS
    expected_kind = ObjectKind.ATTESTATION


register_decoder(
    Fork.GLOAS,
    ObjectKind.ATTESTATION,
    _native.lib.spy_schema_gloas_decode_attestation_owned,
)
register_ssz_decoder(
    Fork.GLOAS,
    ObjectKind.ATTESTATION,
    _native.lib.spy_schema_gloas_decode_attestation_ssz_owned,
)
