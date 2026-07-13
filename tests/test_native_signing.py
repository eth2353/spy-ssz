import msgspec
import pytest
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz.native_signing import (
    AggregateAndProof,
    Attestation,
    AttestationData,
    ContributionAndProof,
    SyncCommitteeContribution,
)


@pytest.mark.parametrize(
    ("reference_type", "native_type"),
    [
        (electra.AttestationData, AttestationData),
        (electra.Attestation, Attestation),
        (electra.AggregateAndProof, AggregateAndProof),
        (electra.SyncCommitteeContribution, SyncCommitteeContribution),
        (electra.ContributionAndProof, ContributionAndProof),
    ],
)
def test_signing_types_match_consensus_ssz(reference_type, native_type) -> None:
    reference = reference_type()
    value = reference.to_obj()

    with native_type.from_obj(value) as from_json:
        assert from_json.hash_tree_root() == reference.hash_tree_root()
        assert from_json.to_ssz() == reference.encode_bytes()
        assert reference_type.from_obj(
            msgspec.json.decode(from_json.to_json())
        ).hash_tree_root() == reference.hash_tree_root()
    with native_type.from_ssz(reference.encode_bytes()) as from_ssz:
        assert from_ssz.hash_tree_root() == reference.hash_tree_root()
        assert from_ssz.to_ssz() == reference.encode_bytes()


def test_native_constructor_and_bitfield_projection() -> None:
    reference = electra.Attestation()
    with Attestation(**reference.to_obj()) as value:
        assert len(value.aggregation_bits) == 0
        assert sum(value.aggregation_bits) == 0
        assert len(value.committee_bits) == 64
        assert value.committee_bits.count() == 0
        assert value.data.slot == 0
