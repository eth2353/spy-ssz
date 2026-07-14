"""Static regression coverage for the public lazy type exports."""

from typing import assert_type

from spy_ssz import signing
from spy_ssz import (
    AggregateAndProofElectra,
    AttestationElectra,
    AttestationDataElectra,
    AttestationElectraMainnet,
    AttesterSlashingElectra,
    BeaconBlockHeaderElectra,
    ContributionAndProofElectra,
    BeaconBlockContentsElectraMainnet,
    SignedBeaconBlockContentsElectraMainnet,
    IndexedAttestationElectra,
    ProposerSlashingElectra,
    SignedAggregateAndProofElectra,
    SignedBeaconBlockHeaderElectra,
    SignedContributionAndProofElectra,
    SingleAttestationElectra,
    SyncCommitteeContributionElectra,
    SyncCommitteeMessageElectra,
    encode_json_array,
    get_ssz_type,
)
from spy_ssz.ssz import Fork, ObjectKind, SszObject


def verify_public_export_types(data: bytes) -> None:
    assert_type(encode_json_array([]), bytes)
    assert_type(
        get_ssz_type(Fork.ELECTRA, ObjectKind.ATTESTATION),
        type[SszObject],
    )
    assert_type(AttestationElectra.from_json(data), AttestationElectra)
    assert_type(AttestationElectraMainnet.from_ssz(data), AttestationElectraMainnet)
    assert_type(AttestationDataElectra.from_json(data), AttestationDataElectra)
    assert_type(AggregateAndProofElectra.from_json(data), AggregateAndProofElectra)
    assert_type(
        SyncCommitteeContributionElectra.from_json(data),
        SyncCommitteeContributionElectra,
    )
    assert_type(
        ContributionAndProofElectra.from_json(data), ContributionAndProofElectra
    )
    assert_type(SingleAttestationElectra.from_json(data), SingleAttestationElectra)
    assert_type(
        SyncCommitteeMessageElectra.from_json(data), SyncCommitteeMessageElectra
    )
    assert_type(
        SignedAggregateAndProofElectra.from_json(data), SignedAggregateAndProofElectra
    )
    assert_type(
        SignedContributionAndProofElectra.from_json(data),
        SignedContributionAndProofElectra,
    )
    assert_type(IndexedAttestationElectra.from_json(data), IndexedAttestationElectra)
    assert_type(AttesterSlashingElectra.from_json(data), AttesterSlashingElectra)
    assert_type(BeaconBlockHeaderElectra.from_json(data), BeaconBlockHeaderElectra)
    assert_type(
        SignedBeaconBlockHeaderElectra.from_json(data), SignedBeaconBlockHeaderElectra
    )
    assert_type(ProposerSlashingElectra.from_json(data), ProposerSlashingElectra)
    assert_type(
        signing.AttestationElectra.from_json(data),
        AttestationElectra,
    )

    block = BeaconBlockContentsElectraMainnet.from_ssz(data)
    assert_type(block, BeaconBlockContentsElectraMainnet)
    assert_type(
        block.sign(bytes(96)),
        SignedBeaconBlockContentsElectraMainnet,
    )
