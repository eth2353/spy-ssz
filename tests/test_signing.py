import msgspec
import pytest
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz.signing import (
    AggregateAndProof,
    Attestation,
    AttestationData,
    AttesterSlashing,
    BeaconBlockHeader,
    ContributionAndProof,
    IndexedAttestation,
    ProposerSlashing,
    SignedAggregateAndProof,
    SignedBeaconBlockHeader,
    SignedContributionAndProof,
    SingleAttestation,
    SyncCommitteeContribution,
    SyncCommitteeMessage,
)
from spy_ssz.ssz import Fork, ObjectKind, decode_json


@pytest.mark.parametrize(
    ("reference_type", "spy_type"),
    [
        (electra.AttestationData, AttestationData),
        (electra.Attestation, Attestation),
        (electra.AggregateAndProof, AggregateAndProof),
        (electra.SyncCommitteeContribution, SyncCommitteeContribution),
        (electra.ContributionAndProof, ContributionAndProof),
        (electra.SingleAttestation, SingleAttestation),
        (electra.SyncCommitteeMessage, SyncCommitteeMessage),
        (electra.SignedAggregateAndProof, SignedAggregateAndProof),
        (electra.SignedContributionAndProof, SignedContributionAndProof),
        (electra.IndexedAttestation, IndexedAttestation),
        (electra.AttesterSlashing, AttesterSlashing),
        (electra.BeaconBlockHeader, BeaconBlockHeader),
        (electra.SignedBeaconBlockHeader, SignedBeaconBlockHeader),
        (electra.ProposerSlashing, ProposerSlashing),
    ],
)
def test_signing_types_match_consensus_ssz(reference_type, spy_type) -> None:
    reference = reference_type()
    value = reference.to_obj()

    with spy_type.from_obj(value) as from_json:
        assert from_json.hash_tree_root() == reference.hash_tree_root()
        assert from_json.to_ssz() == reference.encode_bytes()
        assert (
            reference_type.from_obj(
                msgspec.json.decode(from_json.to_json())
            ).hash_tree_root()
            == reference.hash_tree_root()
        )
    with spy_type.from_ssz(reference.encode_bytes()) as from_ssz:
        assert from_ssz.hash_tree_root() == reference.hash_tree_root()
        assert from_ssz.to_ssz() == reference.encode_bytes()


def test_constructor_and_bitfield_projection() -> None:
    reference = electra.Attestation()
    with Attestation(**reference.to_obj()) as value:
        assert len(value.aggregation_bits) == 0
        assert sum(value.aggregation_bits) == 0
        assert len(value.committee_bits) == 64
        assert value.committee_bits.count() == 0
        assert value.data.slot == 0


def test_populated_variable_slashing_types_match_consensus_ssz() -> None:
    first = electra.IndexedAttestation(attesting_indices=[1, 2, 3])
    second = electra.IndexedAttestation(attesting_indices=[4, 5])
    reference = electra.AttesterSlashing(
        attestation_1=first,
        attestation_2=second,
    )

    with AttesterSlashing.from_obj(reference.to_obj()) as from_json:
        assert from_json.hash_tree_root() == reference.hash_tree_root()
        assert from_json.to_ssz() == reference.encode_bytes()
        assert from_json.attestation_1.attesting_indices == (1, 2, 3)
    with AttesterSlashing.from_ssz(reference.encode_bytes()) as from_ssz:
        assert from_ssz.hash_tree_root() == reference.hash_tree_root()
        assert from_ssz.attestation_2.attesting_indices == (4, 5)


def test_json_decoder_rejects_missing_fields_without_unsafe_token_access() -> None:
    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(b"{}")


@pytest.mark.parametrize(
    ("reference_type", "spy_type"),
    [
        (electra.AttestationData, AttestationData),
        (electra.SyncCommitteeContribution, SyncCommitteeContribution),
        (electra.ContributionAndProof, ContributionAndProof),
        (electra.SingleAttestation, SingleAttestation),
        (electra.SyncCommitteeMessage, SyncCommitteeMessage),
        (electra.SignedContributionAndProof, SignedContributionAndProof),
        (electra.BeaconBlockHeader, BeaconBlockHeader),
        (electra.SignedBeaconBlockHeader, SignedBeaconBlockHeader),
        (electra.ProposerSlashing, ProposerSlashing),
    ],
)
def test_fixed_size_ssz_decoder_rejects_trailing_data(reference_type, spy_type) -> None:
    with pytest.raises(ValueError, match="invalid SSZ object"):
        spy_type.from_ssz(reference_type().encode_bytes() + b"garbage")


def test_ssz_decoder_rejects_noncanonical_first_variable_offset() -> None:
    raw = bytearray(electra.AggregateAndProof().encode_bytes())
    raw[8:12] = (109).to_bytes(4, "little")
    raw[108:108] = b"x"
    with pytest.raises(ValueError, match="invalid SSZ object"):
        AggregateAndProof.from_ssz(raw)


def test_generic_signing_decode_preserves_bare_json_shape() -> None:
    expected = electra.AttestationData().to_obj()
    with decode_json(
        msgspec.json.encode(expected), Fork.ELECTRA, ObjectKind.ATTESTATION_DATA
    ) as value:
        assert value.to_obj()["slot"] == "0"
        assert value.slot == 0
