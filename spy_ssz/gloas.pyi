"""Generated from spy_ssz/schemas.yaml; do not edit."""

from . import projections
from .ssz import Bitfield, SszObject

class GloasAttestation(SszObject):
    @property
    def aggregation_bits(self) -> Bitfield: ...
    @property
    def data(self) -> projections.AttestationData: ...
    @property
    def signature(self) -> bytes: ...
    @property
    def committee_bits(self) -> Bitfield: ...

GloasAttestationMainnet = GloasAttestation
