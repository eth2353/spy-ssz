import msgspec
from eth_consensus_specs.electra import mainnet as electra
from eth_consensus_specs.fulu import mainnet as fulu

from spy_ssz.native_electra import NativeElectraBlock
from spy_ssz.native_fulu import NativeFuluBlock
from spy_ssz.native_object import Fork


def populated_electra_block() -> electra.SignedBeaconBlock:
    body = electra.BeaconBlockBody(
        proposer_slashings=[electra.ProposerSlashing()],
        attester_slashings=[
            electra.AttesterSlashing(
                attestation_1=electra.IndexedAttestation(
                    attesting_indices=[1, 2, 3]
                ),
                attestation_2=electra.IndexedAttestation(
                    attesting_indices=[4, 5]
                ),
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

    with NativeElectraBlock.from_json(raw_json) as decoded:
        assert decoded.fork is Fork.ELECTRA
        assert decoded.schema_id == 501
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        assert decoded.encode_bytes() == raw_ssz
        encoded_json = decoded.to_json()
        assert decoded.encode_json() == encoded_json
        roundtrip = electra.SignedBeaconBlock.from_obj(
            msgspec.json.decode(encoded_json)["data"]
        )
        assert roundtrip.hash_tree_root() == expected
    with NativeElectraBlock.from_ssz(raw_ssz) as decoded:
        assert decoded.fork is Fork.ELECTRA
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        encoded_json = decoded.to_json()
        roundtrip = electra.SignedBeaconBlock.from_obj(
            msgspec.json.decode(encoded_json)["data"]
        )
        assert roundtrip.hash_tree_root() == expected


def test_fulu_reuses_the_electra_block_codec_with_fulu_metadata() -> None:
    electra_bytes = populated_electra_block().encode_bytes()
    reference = fulu.SignedBeaconBlock.decode_bytes(electra_bytes)
    expected = reference.hash_tree_root()
    raw_json = msgspec.json.encode({"data": reference.to_obj()})
    raw_ssz = reference.encode_bytes()

    with NativeFuluBlock.from_json(raw_json) as decoded:
        assert decoded.fork is Fork.FULU
        assert decoded.schema_id == 601
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        roundtrip = fulu.SignedBeaconBlock.from_obj(
            msgspec.json.decode(decoded.to_json())["data"]
        )
        assert roundtrip.hash_tree_root() == expected
    with NativeFuluBlock.from_ssz(raw_ssz) as decoded:
        assert decoded.fork is Fork.FULU
        assert decoded.hash_tree_root() == expected
        assert decoded.to_ssz() == raw_ssz
        roundtrip = fulu.SignedBeaconBlock.from_obj(
            msgspec.json.decode(decoded.to_json())["data"]
        )
        assert roundtrip.hash_tree_root() == expected
