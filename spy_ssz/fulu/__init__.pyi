"""Generated from spy_ssz/schemas.yaml; do not edit."""

from .. import projections
from ..ssz import SszObject

class FuluSignedBeaconBlock(SszObject):
    @property
    def message(self) -> projections.BeaconBlock: ...
    @property
    def signature(self) -> bytes: ...

FuluSignedBeaconBlockMainnet = FuluSignedBeaconBlock

class FuluSignedBeaconBlockMinimal(FuluSignedBeaconBlock): ...
class FuluSignedBeaconBlockGnosis(FuluSignedBeaconBlock): ...
