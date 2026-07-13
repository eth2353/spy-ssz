import msgspec
import pytest
from eth_consensus_specs.electra import mainnet as electra
from eth_consensus_specs.fulu import mainnet as fulu

from spy_ssz.electra import ElectraSignedBeaconBlock, ElectraSignedBeaconBlockMinimal
from spy_ssz.fulu import FuluSignedBeaconBlock
from spy_ssz.schema import get_schema
from spy_ssz.ssz import Fork
from spy_ssz.ssz import ObjectKind
from spy_ssz.preset import Preset


def populated_electra_block() -> electra.SignedBeaconBlock:
    body = electra.BeaconBlockBody(
        proposer_slashings=[electra.ProposerSlashing()],
        attester_slashings=[
            electra.AttesterSlashing(
                attestation_1=electra.IndexedAttestation(attesting_indices=[1, 2, 3]),
                attestation_2=electra.IndexedAttestation(attesting_indices=[4, 5]),
            )
        ],
        attestations=[
            electra.Attestation(
                aggregation_bits=[True, False, True],
                committee_bits=[True] + [False] * 63,
            )
        ],
        deposits=[electra.Deposit()],
        voluntary_exits=[electra.SignedVoluntaryExit()],
        execution_payload=electra.ExecutionPayload(
            extra_data=b"abc",
            transactions=[b"\x01\x02"],
            withdrawals=[electra.Withdrawal()],
        ),
        bls_to_execution_changes=[electra.SignedBLSToExecutionChange()],
        blob_kzg_commitments=[electra.KZGCommitment()],
        execution_requests=electra.ExecutionRequests(
            deposits=[electra.DepositRequest(index=1)],
            withdrawals=[electra.WithdrawalRequest(amount=2)],
            consolidations=[electra.ConsolidationRequest()],
        ),
    )
    return electra.SignedBeaconBlock(message=electra.BeaconBlock(body=body))


def test_electra_json_and_ssz_cover_every_block_operation_family() -> None:
    reference = populated_electra_block()
    expected = reference.hash_tree_root()
    raw_json = msgspec.json.encode({"data": reference.to_obj()})
    raw_ssz = reference.encode_bytes()

    with ElectraSignedBeaconBlock.from_json(raw_json) as decoded:
        assert decoded.fork is Fork.ELECTRA
        assert (
            decoded.schema_id
            == get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BEACON_BLOCK).schema_id
        )
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        encoded_json = decoded.to_json()
        roundtrip = electra.SignedBeaconBlock.from_obj(
            msgspec.json.decode(encoded_json)["data"]
        )
        assert roundtrip.hash_tree_root() == expected
    with ElectraSignedBeaconBlock.from_ssz(raw_ssz) as decoded:
        assert decoded.fork is Fork.ELECTRA
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        encoded_json = decoded.to_json()
        roundtrip = electra.SignedBeaconBlock.from_obj(
            msgspec.json.decode(encoded_json)["data"]
        )
        assert roundtrip.hash_tree_root() == expected


def test_json_composite_list_decodes_more_than_nine_items() -> None:
    reference = populated_electra_block()
    reference.message.body.execution_payload.withdrawals = [
        electra.Withdrawal(index=index, validator_index=index + 100)
        for index in range(16)
    ]

    with ElectraSignedBeaconBlock.from_obj(reference) as decoded:
        assert decoded.hash_tree_root() == reference.hash_tree_root()
        assert decoded.to_ssz() == reference.encode_bytes()


def test_fulu_reuses_the_electra_block_codec_with_fulu_metadata() -> None:
    electra_bytes = populated_electra_block().encode_bytes()
    reference = fulu.SignedBeaconBlock.decode_bytes(electra_bytes)
    expected = reference.hash_tree_root()
    raw_json = msgspec.json.encode({"data": reference.to_obj()})
    raw_ssz = reference.encode_bytes()

    with FuluSignedBeaconBlock.from_json(raw_json) as decoded:
        assert decoded.fork is Fork.FULU
        assert (
            decoded.schema_id
            == get_schema(Fork.FULU, ObjectKind.SIGNED_BEACON_BLOCK).schema_id
        )
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        roundtrip = fulu.SignedBeaconBlock.from_obj(
            msgspec.json.decode(decoded.to_json())["data"]
        )
        assert roundtrip.hash_tree_root() == expected
    with FuluSignedBeaconBlock.from_ssz(raw_ssz) as decoded:
        assert decoded.fork is Fork.FULU
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        roundtrip = fulu.SignedBeaconBlock.from_obj(
            msgspec.json.decode(decoded.to_json())["data"]
        )
        assert roundtrip.hash_tree_root() == expected


def test_minimal_preset_changes_fixed_vector_sizes_and_roundtrips() -> None:
    value = populated_electra_block().to_obj()
    value["message"]["body"]["sync_aggregate"]["sync_committee_bits"] = "0x00000000"
    for attestation in value["message"]["body"]["attestations"]:
        attestation["committee_bits"] = "0x01"
    raw_json = msgspec.json.encode({"data": value})

    with ElectraSignedBeaconBlockMinimal.from_json(raw_json) as from_json:
        assert from_json.preset is Preset.MINIMAL
        raw_ssz = from_json.to_ssz()
        expected_root = from_json.hash_tree_root()
    with ElectraSignedBeaconBlockMinimal.from_ssz(raw_ssz) as from_ssz:
        assert from_ssz.preset is Preset.MINIMAL
        assert from_ssz.hash_tree_root() == expected_root
        assert from_ssz.to_ssz() == raw_ssz
        encoded = msgspec.json.decode(from_ssz.to_json())["data"]
        body = encoded["message"]["body"]
        assert body["sync_aggregate"]["sync_committee_bits"] == "0x00000000"
        assert body["attestations"][0]["committee_bits"] == "0x01"


def test_block_json_rejects_uint64_overflow() -> None:
    value = populated_electra_block().to_obj()
    value["message"]["slot"] = str(2**64)

    with pytest.raises(ValueError, match="invalid JSON object"):
        ElectraSignedBeaconBlock.from_obj(value)


def test_block_json_rejects_duplicate_keys() -> None:
    raw_json = msgspec.json.encode({"data": populated_electra_block().to_obj()})
    field = b'"slot":0'
    assert field in raw_json
    raw_json = raw_json.replace(field, field + b',"slot":0', 1)

    with pytest.raises(ValueError, match="invalid JSON object"):
        ElectraSignedBeaconBlock.from_json(raw_json)


def test_block_json_rejects_unrecognized_nested_field() -> None:
    value = populated_electra_block().to_obj()
    value["message"]["unknown"] = True

    with pytest.raises(ValueError, match="^unrecognized JSON object field 'unknown'$"):
        ElectraSignedBeaconBlock.from_obj(value)


def test_block_json_accepts_standard_response_metadata() -> None:
    raw_json = msgspec.json.encode(
        {
            "version": "electra",
            "execution_optimistic": False,
            "finalized": True,
            "data": populated_electra_block().to_obj(),
        }
    )

    with ElectraSignedBeaconBlock.from_json(raw_json) as decoded:
        assert decoded.message.slot == 0


def test_block_json_rejects_unrecognized_response_metadata() -> None:
    raw_json = msgspec.json.encode(
        {"unknown": True, "data": populated_electra_block().to_obj()}
    )

    with pytest.raises(ValueError, match="^unrecognized JSON object field 'unknown'$"):
        ElectraSignedBeaconBlock.from_json(raw_json)


def test_block_json_rejects_block_production_metadata() -> None:
    raw_json = msgspec.json.encode(
        {
            "execution_payload_value": "0",
            "data": populated_electra_block().to_obj(),
        }
    )

    with pytest.raises(
        ValueError,
        match="^unrecognized JSON object field 'execution_payload_value'$",
    ):
        ElectraSignedBeaconBlock.from_json(raw_json)


def test_block_json_accepts_remerkleable_little_endian_uint256_hex() -> None:
    reference = populated_electra_block()
    reference.message.body.execution_payload.base_fee_per_gas = 0x010203

    with ElectraSignedBeaconBlock.from_obj(reference) as decoded:
        assert (
            decoded.to_obj()["message"]["body"]["execution_payload"]["base_fee_per_gas"]
            == "66051"
        )
        assert decoded.to_ssz() == reference.encode_bytes()
        assert decoded.hash_tree_root() == reference.hash_tree_root()


@pytest.mark.parametrize("invalid", ["", str(2**256), "0x" + "ff" * 33])
def test_block_json_rejects_invalid_uint256(invalid: str) -> None:
    value = populated_electra_block().to_obj()
    value["message"]["body"]["execution_payload"]["base_fee_per_gas"] = invalid

    with pytest.raises(ValueError, match="invalid JSON object"):
        ElectraSignedBeaconBlock.from_obj(value)


def test_block_json_rejects_list_longer_than_its_ssz_limit() -> None:
    value = populated_electra_block().to_obj()
    value["message"]["body"]["blob_kzg_commitments"] = ["0x" + "00" * 48] * 4097

    with pytest.raises(ValueError, match="invalid JSON object"):
        ElectraSignedBeaconBlock.from_obj(value)
