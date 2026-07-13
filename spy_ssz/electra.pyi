"""Generated from spy_ssz/schemas.yaml; do not edit."""

from . import projections
from .ssz import SszObject

class ElectraSignedBeaconBlock(SszObject):
    @property
    def message(self) -> projections.BeaconBlock: ...
    @property
    def signature(self) -> bytes: ...

ElectraSignedBeaconBlockMainnet = ElectraSignedBeaconBlock

class ElectraSignedBeaconBlockMinimal(ElectraSignedBeaconBlock): ...
class ElectraSignedBeaconBlockGnosis(ElectraSignedBeaconBlock): ...
