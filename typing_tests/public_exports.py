"""Static regression coverage for the public lazy type exports."""

from typing import assert_type

from spy_ssz import (
    AggregateAndProof,
    Attestation,
    AttestationData,
    AttestationMainnet,
    ContributionAndProof,
    ElectraBeaconBlockContentsMainnet,
    ElectraSignedBeaconBlockContentsMainnet,
    SyncCommitteeContribution,
)
from spy_ssz.signing import Attestation as ModuleAttestation


def verify_public_export_types(data: bytes) -> None:
    assert_type(Attestation.from_json(data), Attestation)
    assert_type(AttestationMainnet.from_ssz(data), AttestationMainnet)
    assert_type(AttestationData.from_json(data), AttestationData)
    assert_type(AggregateAndProof.from_json(data), AggregateAndProof)
    assert_type(
        SyncCommitteeContribution.from_json(data),
        SyncCommitteeContribution,
    )
    assert_type(ContributionAndProof.from_json(data), ContributionAndProof)
    assert_type(ModuleAttestation.from_json(data), ModuleAttestation)

    block = ElectraBeaconBlockContentsMainnet.from_ssz(data)
    assert_type(block, ElectraBeaconBlockContentsMainnet)
    assert_type(
        block.sign(bytes(96)),
        ElectraSignedBeaconBlockContentsMainnet,
    )
