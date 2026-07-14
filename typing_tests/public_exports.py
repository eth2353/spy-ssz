"""Static regression coverage for the public lazy type exports."""

from typing import assert_type

from spy_ssz import (
    AggregateAndProof,
    Attestation,
    AttestationData,
    AttestationMainnet,
    AttesterSlashing,
    BeaconBlockHeader,
    ContributionAndProof,
    ElectraBeaconBlockContentsMainnet,
    ElectraSignedBeaconBlockContentsMainnet,
    IndexedAttestation,
    ProposerSlashing,
    SignedAggregateAndProof,
    SignedBeaconBlockHeader,
    SignedContributionAndProof,
    SingleAttestation,
    SyncCommitteeContribution,
    SyncCommitteeMessage,
    get_ssz_type,
)
from spy_ssz.ssz import Fork, ObjectKind, SszObject
from spy_ssz.signing import Attestation as ModuleAttestation


def verify_public_export_types(data: bytes) -> None:
    assert_type(
        get_ssz_type(Fork.ELECTRA, ObjectKind.ATTESTATION),
        type[SszObject],
    )
    assert_type(Attestation.from_json(data), Attestation)
    assert_type(AttestationMainnet.from_ssz(data), AttestationMainnet)
    assert_type(AttestationData.from_json(data), AttestationData)
    assert_type(AggregateAndProof.from_json(data), AggregateAndProof)
    assert_type(
        SyncCommitteeContribution.from_json(data),
        SyncCommitteeContribution,
    )
    assert_type(ContributionAndProof.from_json(data), ContributionAndProof)
    assert_type(SingleAttestation.from_json(data), SingleAttestation)
    assert_type(SyncCommitteeMessage.from_json(data), SyncCommitteeMessage)
    assert_type(SignedAggregateAndProof.from_json(data), SignedAggregateAndProof)
    assert_type(
        SignedContributionAndProof.from_json(data),
        SignedContributionAndProof,
    )
    assert_type(IndexedAttestation.from_json(data), IndexedAttestation)
    assert_type(AttesterSlashing.from_json(data), AttesterSlashing)
    assert_type(BeaconBlockHeader.from_json(data), BeaconBlockHeader)
    assert_type(SignedBeaconBlockHeader.from_json(data), SignedBeaconBlockHeader)
    assert_type(ProposerSlashing.from_json(data), ProposerSlashing)
    assert_type(ModuleAttestation.from_json(data), ModuleAttestation)

    block = ElectraBeaconBlockContentsMainnet.from_ssz(data)
    assert_type(block, ElectraBeaconBlockContentsMainnet)
    assert_type(
        block.sign(bytes(96)),
        ElectraSignedBeaconBlockContentsMainnet,
    )
