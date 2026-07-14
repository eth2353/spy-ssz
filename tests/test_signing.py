from unittest import mock

import msgspec
import pytest
from eth_consensus_specs.electra import mainnet as electra
from eth_consensus_specs.electra import minimal as electra_minimal

from spy_ssz.signing import (
    AggregateAndProofElectra,
    AttestationDataElectra,
    AttestationElectra,
    AttestationElectraMinimal,
    AttesterSlashingElectra,
    BeaconBlockHeaderElectra,
    ContributionAndProofElectra,
    IndexedAttestationElectra,
    ProposerSlashingElectra,
    SignedAggregateAndProofElectra,
    SignedBeaconBlockHeaderElectra,
    SignedContributionAndProofElectra,
    SingleAttestationElectra,
    SyncCommitteeContributionElectra,
    SyncCommitteeMessageElectra,
)
from spy_ssz import encode_json_array
from spy_ssz import Preset, get_ssz_type
from spy_ssz.ssz import Fork, ObjectKind, _JSON_ENCODERS, decode_json


@pytest.mark.parametrize(
    ("reference_type", "spy_type"),
    [
        (electra.AttestationData, AttestationDataElectra),
        (electra.Attestation, AttestationElectra),
        (electra.AggregateAndProof, AggregateAndProofElectra),
        (electra.SyncCommitteeContribution, SyncCommitteeContributionElectra),
        (electra.ContributionAndProof, ContributionAndProofElectra),
        (electra.SingleAttestation, SingleAttestationElectra),
        (electra.SyncCommitteeMessage, SyncCommitteeMessageElectra),
        (electra.SignedAggregateAndProof, SignedAggregateAndProofElectra),
        (electra.SignedContributionAndProof, SignedContributionAndProofElectra),
        (electra.IndexedAttestation, IndexedAttestationElectra),
        (electra.AttesterSlashing, AttesterSlashingElectra),
        (electra.BeaconBlockHeader, BeaconBlockHeaderElectra),
        (electra.SignedBeaconBlockHeader, SignedBeaconBlockHeaderElectra),
        (electra.ProposerSlashing, ProposerSlashingElectra),
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


@pytest.mark.parametrize(
    ("reference_type", "kind"),
    [
        (electra.AttestationData, ObjectKind.ATTESTATION_DATA),
        (electra.Attestation, ObjectKind.ATTESTATION),
        (electra.AggregateAndProof, ObjectKind.AGGREGATE_AND_PROOF),
        (
            electra.SyncCommitteeContribution,
            ObjectKind.SYNC_COMMITTEE_CONTRIBUTION,
        ),
        (electra.ContributionAndProof, ObjectKind.CONTRIBUTION_AND_PROOF),
        (electra.SingleAttestation, ObjectKind.SINGLE_ATTESTATION),
        (electra.SyncCommitteeMessage, ObjectKind.SYNC_COMMITTEE_MESSAGE),
        (
            electra.SignedAggregateAndProof,
            ObjectKind.SIGNED_AGGREGATE_AND_PROOF,
        ),
        (
            electra.SignedContributionAndProof,
            ObjectKind.SIGNED_CONTRIBUTION_AND_PROOF,
        ),
        (electra.IndexedAttestation, ObjectKind.INDEXED_ATTESTATION),
        (electra.AttesterSlashing, ObjectKind.ATTESTER_SLASHING),
        (electra.BeaconBlockHeader, ObjectKind.BEACON_BLOCK_HEADER),
        (electra.SignedBeaconBlockHeader, ObjectKind.SIGNED_BEACON_BLOCK_HEADER),
        (electra.ProposerSlashing, ObjectKind.PROPOSER_SLASHING),
    ],
)
def test_fulu_signing_types_reuse_electra_wire_schema(reference_type, kind) -> None:
    reference = reference_type()
    fulu_type = get_ssz_type(Fork.FULU, kind, Preset.MAINNET)

    with fulu_type.from_obj(reference.to_obj()) as from_json:
        assert type(from_json) is fulu_type
        assert from_json.fork is Fork.FULU
        assert from_json.object_kind is kind
        assert from_json.schema_id == 600 + kind.value
        assert from_json.hash_tree_root() == reference.hash_tree_root()
        assert from_json.to_ssz() == reference.encode_bytes()

    with fulu_type.from_ssz(reference.encode_bytes()) as from_ssz:
        assert type(from_ssz) is fulu_type
        assert from_ssz.fork is Fork.FULU
        assert from_ssz.schema_id == 600 + kind.value
        assert from_ssz.hash_tree_root() == reference.hash_tree_root()


def test_fulu_typed_composition_preserves_fulu_identity() -> None:
    attestation_type = get_ssz_type(Fork.FULU, ObjectKind.ATTESTATION, Preset.MAINNET)
    aggregate_type = get_ssz_type(
        Fork.FULU, ObjectKind.AGGREGATE_AND_PROOF, Preset.MAINNET
    )
    with attestation_type.from_obj(electra.Attestation().to_obj()) as attestation:
        with aggregate_type(
            aggregator_index=1,
            aggregate=attestation,
            selection_proof=bytes(96),
        ) as aggregate:
            assert aggregate.fork is Fork.FULU
            assert aggregate.schema_id == 605

    with AttestationElectra.from_obj(
        electra.Attestation().to_obj()
    ) as electra_attestation:
        with pytest.raises(TypeError, match="nested SSZ object fork"):
            aggregate_type(
                aggregator_index=1,
                aggregate=electra_attestation,
                selection_proof=bytes(96),
            )


def test_constructor_and_bitfield_projection() -> None:
    reference = electra.Attestation()
    with AttestationElectra(**reference.to_obj()) as value:
        assert len(value.aggregation_bits) == 0
        assert sum(value.aggregation_bits) == 0
        assert len(value.committee_bits) == 64
        assert value.committee_bits.count() == 0
        assert value.data.slot == 0


def test_typed_children_are_composed_without_json_roundtrip() -> None:
    signature = bytes(range(96))
    attestation_reference = electra.Attestation()
    attestation = AttestationElectra.from_obj(attestation_reference.to_obj())
    with (
        mock.patch.object(
            AttestationElectra,
            "to_obj",
            side_effect=AssertionError("typed composition must stay native"),
        ),
        mock.patch.object(
            AttestationElectra,
            "to_json",
            side_effect=AssertionError("typed composition must stay native"),
        ),
    ):
        aggregate = AggregateAndProofElectra(
            aggregator_index=12,
            aggregate=attestation,
            selection_proof=signature,
        )
    attestation.close()
    aggregate_reference = electra.AggregateAndProof(
        aggregator_index=12,
        aggregate=attestation_reference,
        selection_proof=signature,
    )
    assert aggregate.to_ssz() == aggregate_reference.encode_bytes()

    with mock.patch.object(
        AggregateAndProofElectra,
        "to_json",
        side_effect=AssertionError("typed composition must stay native"),
    ):
        signed_aggregate = SignedAggregateAndProofElectra.from_obj(
            {"message": aggregate, "signature": signature}
        )
    aggregate.close()
    assert (
        signed_aggregate.to_ssz()
        == electra.SignedAggregateAndProof(
            message=aggregate_reference,
            signature=signature,
        ).encode_bytes()
    )
    signed_aggregate.close()

    contribution_reference = electra.SyncCommitteeContribution()
    contribution = SyncCommitteeContributionElectra.from_obj(
        contribution_reference.to_obj()
    )
    with mock.patch.object(
        SyncCommitteeContributionElectra,
        "to_json",
        side_effect=AssertionError("typed composition must stay native"),
    ):
        proof = ContributionAndProofElectra(
            aggregator_index="34",
            contribution=contribution,
            selection_proof=signature,
        )
    contribution.close()
    proof_reference = electra.ContributionAndProof(
        aggregator_index=34,
        contribution=contribution_reference,
        selection_proof=signature,
    )
    assert proof.to_ssz() == proof_reference.encode_bytes()
    with mock.patch.object(
        ContributionAndProofElectra,
        "to_json",
        side_effect=AssertionError("typed composition must stay native"),
    ):
        signed_proof = SignedContributionAndProofElectra(
            message=proof,
            signature=signature,
        )
    proof.close()
    assert (
        signed_proof.to_ssz()
        == electra.SignedContributionAndProof(
            message=proof_reference,
            signature=signature,
        ).encode_bytes()
    )
    signed_proof.close()

    data_reference = electra.AttestationData(slot=56)
    data = AttestationDataElectra.from_obj(data_reference.to_obj())
    with mock.patch.object(
        AttestationDataElectra,
        "to_json",
        side_effect=AssertionError("typed composition must stay native"),
    ):
        single = SingleAttestationElectra(
            committee_index=78,
            attester_index=90,
            data=data,
            signature=signature,
        )
    data.close()
    assert (
        single.to_ssz()
        == electra.SingleAttestation(
            committee_index=78,
            attester_index=90,
            data=data_reference,
            signature=signature,
        ).encode_bytes()
    )
    single.close()


def test_populated_variable_slashing_types_match_consensus_ssz() -> None:
    first = electra.IndexedAttestation(attesting_indices=[1, 2, 3])
    second = electra.IndexedAttestation(attesting_indices=[4, 5])
    reference = electra.AttesterSlashing(
        attestation_1=first,
        attestation_2=second,
    )

    with AttesterSlashingElectra.from_obj(reference.to_obj()) as from_json:
        assert from_json.hash_tree_root() == reference.hash_tree_root()
        assert from_json.to_ssz() == reference.encode_bytes()
        assert from_json.attestation_1.attesting_indices == (1, 2, 3)
    with AttesterSlashingElectra.from_ssz(reference.encode_bytes()) as from_ssz:
        assert from_ssz.hash_tree_root() == reference.hash_tree_root()
        assert from_ssz.attestation_2.attesting_indices == (4, 5)


def test_json_decoder_rejects_missing_fields_without_unsafe_token_access() -> None:
    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationDataElectra.from_json(b"{}")


def test_json_decoder_reports_status_for_wrong_fixed_byte_length() -> None:
    value = electra.AttestationData().to_obj()
    value["beacon_block_root"] = "0x00"

    with pytest.raises(
        ValueError, match=r"invalid JSON object \(status=MALFORMED_INPUT"
    ):
        AttestationDataElectra.from_obj(value)


@pytest.mark.parametrize(
    ("reference_type", "spy_type"),
    [
        (electra.AttestationData, AttestationDataElectra),
        (electra.SyncCommitteeContribution, SyncCommitteeContributionElectra),
        (electra.ContributionAndProof, ContributionAndProofElectra),
        (electra.SingleAttestation, SingleAttestationElectra),
        (electra.SyncCommitteeMessage, SyncCommitteeMessageElectra),
        (electra.SignedContributionAndProof, SignedContributionAndProofElectra),
        (electra.BeaconBlockHeader, BeaconBlockHeaderElectra),
        (electra.SignedBeaconBlockHeader, SignedBeaconBlockHeaderElectra),
        (electra.ProposerSlashing, ProposerSlashingElectra),
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
        AggregateAndProofElectra.from_ssz(raw)


def test_ssz_decoder_rejects_bitlist_over_encoded_length_limit() -> None:
    raw = bytearray(electra.Attestation().encode_bytes())
    bitlist_start = int.from_bytes(raw[:4], "little")
    bit_limit = int(
        electra.MAX_VALIDATORS_PER_COMMITTEE * electra.MAX_COMMITTEES_PER_SLOT
    )
    max_encoded_length = (bit_limit + 8) // 8
    raw[bitlist_start:] = bytes(max_encoded_length) + b"\x01"

    with pytest.raises(ValueError, match="invalid SSZ object"):
        AttestationElectra.from_ssz(raw)


@pytest.mark.parametrize("invalid", ["0x10", "0x80", "0xff"])
def test_minimal_attestation_json_rejects_bitvector_padding(invalid: str) -> None:
    value = electra_minimal.Attestation().to_obj()
    value["committee_bits"] = invalid

    with pytest.raises(
        ValueError, match=r"invalid JSON object \(status=MALFORMED_INPUT"
    ):
        AttestationElectraMinimal.from_obj(value)


@pytest.mark.parametrize("invalid", [0x10, 0x80, 0xFF])
def test_minimal_attestation_ssz_rejects_bitvector_padding(invalid: int) -> None:
    raw = bytearray(electra_minimal.Attestation().encode_bytes())
    raw[228] = invalid

    with pytest.raises(ValueError, match="invalid SSZ object"):
        AttestationElectraMinimal.from_ssz(raw)


def test_minimal_attestation_accepts_full_bitvector_value() -> None:
    reference = electra_minimal.Attestation(committee_bits=[True] * 4)

    with (
        AttestationElectraMinimal.from_obj(reference.to_obj()) as from_json,
        AttestationElectraMinimal.from_ssz(reference.encode_bytes()) as from_ssz,
    ):
        assert from_json.to_ssz() == reference.encode_bytes()
        assert from_ssz.hash_tree_root() == reference.hash_tree_root()


def test_generic_signing_decode_preserves_bare_json_shape() -> None:
    expected = electra.AttestationData().to_obj()
    with decode_json(
        msgspec.json.encode(expected), Fork.ELECTRA, ObjectKind.ATTESTATION_DATA
    ) as value:
        assert value.to_obj()["slot"] == "0"
        assert value.slot == 0


@pytest.mark.parametrize(
    ("spy_type", "reference_factory"),
    [
        (AttestationElectra, electra.Attestation),
        (AggregateAndProofElectra, electra.AggregateAndProof),
        (SyncCommitteeMessageElectra, electra.SyncCommitteeMessage),
        (SyncCommitteeContributionElectra, electra.SyncCommitteeContribution),
        (SignedAggregateAndProofElectra, electra.SignedAggregateAndProof),
    ],
)
def test_native_json_array_encoding_uses_one_output_buffer(
    spy_type, reference_factory
) -> None:
    values = [spy_type.from_obj(reference_factory().to_obj()) for _ in range(3)]
    try:
        key = (
            spy_type.expected_fork,
            spy_type.expected_kind,
            spy_type.expected_preset,
        )
        individual_codec = _JSON_ENCODERS[key]
        with (
            mock.patch.object(
                spy_type,
                "to_json",
                side_effect=AssertionError("batch encoding must stay native"),
            ),
            mock.patch.dict(
                _JSON_ENCODERS,
                {
                    key: (
                        mock.Mock(
                            side_effect=AssertionError("batch sizing must be fused")
                        ),
                        mock.Mock(
                            side_effect=AssertionError("batch encoding must be fused")
                        ),
                    )
                },
            ),
        ):
            encoded = encode_json_array(values)
        assert _JSON_ENCODERS[key] == individual_codec
        assert msgspec.json.decode(encoded) == [value.to_obj() for value in values]
    finally:
        for value in values:
            value.close()


def test_native_json_array_encoding_validates_inputs() -> None:
    assert encode_json_array([]) == b"[]"
    with (
        AttestationDataElectra.from_obj(electra.AttestationData().to_obj()) as data,
        SyncCommitteeMessageElectra.from_obj(
            electra.SyncCommitteeMessage().to_obj()
        ) as message,
    ):
        with pytest.raises(TypeError, match="same concrete SSZ type"):
            encode_json_array([data, message])
    with pytest.raises(TypeError, match="concrete SPy SSZ objects"):
        encode_json_array([object()])  # type: ignore[list-item]
