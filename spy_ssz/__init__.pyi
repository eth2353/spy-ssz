"""Generated from spy_ssz/schemas.yaml; do not edit."""

from ._schema_enums import (
    Fork as Fork,
    ObjectKind as ObjectKind,
)
from .consensus_types import (
    TypeDefinition as TypeDefinition,
    get_type_definition as get_type_definition,
    get_type_shape as get_type_shape,
    iter_type_definitions as iter_type_definitions,
)
from .preset import (
    Preset as Preset,
    PresetConfig as PresetConfig,
    load_preset as load_preset,
)
from .projections import Checkpoint as Checkpoint
from .ssz import (
    SszObject as SszObject,
    decode_json as decode_json,
    decode_ssz as decode_ssz,
)

from .blocks import (
    ElectraBeaconBlockContents as ElectraBeaconBlockContents,
    ElectraBeaconBlockContentsMainnet as ElectraBeaconBlockContentsMainnet,
    ElectraBeaconBlockContentsMinimal as ElectraBeaconBlockContentsMinimal,
    ElectraBeaconBlockContentsGnosis as ElectraBeaconBlockContentsGnosis,
    ElectraSignedBeaconBlockContents as ElectraSignedBeaconBlockContents,
    ElectraSignedBeaconBlockContentsMainnet as ElectraSignedBeaconBlockContentsMainnet,
    ElectraSignedBeaconBlockContentsMinimal as ElectraSignedBeaconBlockContentsMinimal,
    ElectraSignedBeaconBlockContentsGnosis as ElectraSignedBeaconBlockContentsGnosis,
    ElectraBlindedBeaconBlock as ElectraBlindedBeaconBlock,
    ElectraBlindedBeaconBlockMainnet as ElectraBlindedBeaconBlockMainnet,
    ElectraBlindedBeaconBlockMinimal as ElectraBlindedBeaconBlockMinimal,
    ElectraBlindedBeaconBlockGnosis as ElectraBlindedBeaconBlockGnosis,
    ElectraSignedBlindedBeaconBlock as ElectraSignedBlindedBeaconBlock,
    ElectraSignedBlindedBeaconBlockMainnet as ElectraSignedBlindedBeaconBlockMainnet,
    ElectraSignedBlindedBeaconBlockMinimal as ElectraSignedBlindedBeaconBlockMinimal,
    ElectraSignedBlindedBeaconBlockGnosis as ElectraSignedBlindedBeaconBlockGnosis,
)

from .deneb import (
    DenebSignedBeaconBlock as DenebSignedBeaconBlock,
    DenebSignedBeaconBlockMainnet as DenebSignedBeaconBlockMainnet,
    DenebAttestation as DenebAttestation,
    DenebAttestationMainnet as DenebAttestationMainnet,
)

from .electra import (
    ElectraSignedBeaconBlock as ElectraSignedBeaconBlock,
    ElectraSignedBeaconBlockMainnet as ElectraSignedBeaconBlockMainnet,
    ElectraSignedBeaconBlockMinimal as ElectraSignedBeaconBlockMinimal,
    ElectraSignedBeaconBlockGnosis as ElectraSignedBeaconBlockGnosis,
)

from .fulu import (
    FuluSignedBeaconBlock as FuluSignedBeaconBlock,
    FuluSignedBeaconBlockMainnet as FuluSignedBeaconBlockMainnet,
    FuluSignedBeaconBlockMinimal as FuluSignedBeaconBlockMinimal,
    FuluSignedBeaconBlockGnosis as FuluSignedBeaconBlockGnosis,
)

from .gloas import (
    GloasAttestation as GloasAttestation,
    GloasAttestationMainnet as GloasAttestationMainnet,
)

from .signing import (
    Attestation as Attestation,
    AttestationMainnet as AttestationMainnet,
    AttestationMinimal as AttestationMinimal,
    AttestationGnosis as AttestationGnosis,
    AttestationData as AttestationData,
    AttestationDataMainnet as AttestationDataMainnet,
    AttestationDataMinimal as AttestationDataMinimal,
    AttestationDataGnosis as AttestationDataGnosis,
    AggregateAndProof as AggregateAndProof,
    AggregateAndProofMainnet as AggregateAndProofMainnet,
    AggregateAndProofMinimal as AggregateAndProofMinimal,
    AggregateAndProofGnosis as AggregateAndProofGnosis,
    SyncCommitteeContribution as SyncCommitteeContribution,
    SyncCommitteeContributionMainnet as SyncCommitteeContributionMainnet,
    SyncCommitteeContributionMinimal as SyncCommitteeContributionMinimal,
    SyncCommitteeContributionGnosis as SyncCommitteeContributionGnosis,
    ContributionAndProof as ContributionAndProof,
    ContributionAndProofMainnet as ContributionAndProofMainnet,
    ContributionAndProofMinimal as ContributionAndProofMinimal,
    ContributionAndProofGnosis as ContributionAndProofGnosis,
)
