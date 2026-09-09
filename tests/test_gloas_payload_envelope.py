import msgspec
from eth_consensus_specs.gloas import mainnet as gloas

from spy_ssz import ObjectKind
from spy_ssz.gloas import (
    ExecutionPayloadEnvelopeGloasMainnet,
    PayloadAttestationDataGloasMainnet,
    SignedExecutionPayloadEnvelopeGloasMainnet,
)


def _reference_envelope() -> gloas.ExecutionPayloadEnvelope:
    return gloas.ExecutionPayloadEnvelope(
        payload=gloas.ExecutionPayload(
            block_number=12,
            gas_limit=30_000_000,
            gas_used=21_000,
            timestamp=34,
            extra_data=b"gloas",
            base_fee_per_gas=56,
            transactions=[b"\x01\x02", b"\x03"],
            withdrawals=[
                gloas.Withdrawal(
                    index=1,
                    validator_index=2,
                    address=bytes.fromhex("11" * 20),
                    amount=3,
                )
            ],
            blob_gas_used=4,
            excess_blob_gas=5,
            block_access_list=b"\xaa\xbb\xcc",
            slot_number=78,
        ),
        execution_requests=gloas.ExecutionRequests(),
        builder_index=9,
        beacon_block_root=bytes.fromhex("22" * 32),
        parent_beacon_block_root=bytes.fromhex("33" * 32),
    )


def test_execution_payload_envelope_json_ssz_and_projections() -> None:
    reference = _reference_envelope()
    response = msgspec.json.encode(
        {
            "data": reference.to_obj(),
            "version": "gloas",
            "execution_optimistic": False,
            "future_metadata": {"ignored": True},
        }
    )

    with ExecutionPayloadEnvelopeGloasMainnet.from_json(response) as envelope:
        assert envelope.object_kind is ObjectKind.EXECUTION_PAYLOAD_ENVELOPE
        assert (
            gloas.ExecutionPayloadEnvelope.from_obj(envelope.to_obj()).hash_tree_root()
            == reference.hash_tree_root()
        )
        assert envelope.to_ssz() == reference.encode_bytes()
        assert envelope.hash_tree_root() == reference.hash_tree_root()
        assert envelope.builder_index == 9
        assert envelope.payload.block_number == 12
        assert envelope.payload.transactions == (b"\x01\x02", b"\x03")
        assert envelope.payload.block_access_list == b"\xaa\xbb\xcc"

    with ExecutionPayloadEnvelopeGloasMainnet.from_ssz(
        reference.encode_bytes()
    ) as envelope:
        assert envelope.hash_tree_root() == reference.hash_tree_root()
        encoded = msgspec.json.decode(envelope.to_json())
        assert encoded["version"] == "gloas"
        assert set(encoded) == {"version", "data"}
        assert (
            gloas.ExecutionPayloadEnvelope.from_obj(encoded["data"]).hash_tree_root()
            == reference.hash_tree_root()
        )


def test_execution_payload_envelope_signs_to_direct_publish_body() -> None:
    reference = _reference_envelope()
    signature = bytes(range(96))
    expected = gloas.SignedExecutionPayloadEnvelope(
        message=reference,
        signature=signature,
    )

    with (
        ExecutionPayloadEnvelopeGloasMainnet.from_obj(reference.to_obj()) as envelope,
        envelope.sign(signature) as signed,
    ):
        assert isinstance(signed, SignedExecutionPayloadEnvelopeGloasMainnet)
        assert signed.object_kind is ObjectKind.SIGNED_EXECUTION_PAYLOAD_ENVELOPE
        assert signed.to_ssz() == expected.encode_bytes()
        assert signed.hash_tree_root() == expected.hash_tree_root()
        publish_body = msgspec.json.decode(signed.to_json())
        assert set(publish_body) == {"message", "signature"}
        assert (
            gloas.SignedExecutionPayloadEnvelope.from_obj(publish_body).hash_tree_root()
            == expected.hash_tree_root()
        )


def test_signed_execution_payload_envelope_accepts_response_metadata() -> None:
    expected = gloas.SignedExecutionPayloadEnvelope(
        message=_reference_envelope(),
        signature=bytes(range(96)),
    )
    response = msgspec.json.encode(
        {
            "data": expected.to_obj(),
            "version": "gloas",
            "future_metadata": [1, 2, 3],
        }
    )

    with SignedExecutionPayloadEnvelopeGloasMainnet.from_json(response) as signed:
        assert signed.to_ssz() == expected.encode_bytes()
        assert signed.hash_tree_root() == expected.hash_tree_root()


def test_payload_attestation_data_uses_versioned_response_envelope() -> None:
    expected = gloas.PayloadAttestationData(slot=12, payload_present=True)
    response = msgspec.json.encode(
        {
            "version": "gloas",
            "data": expected.to_obj(),
            "future_metadata": {"ignored": True},
        }
    )

    with PayloadAttestationDataGloasMainnet.from_json(response) as data:
        assert data.to_ssz() == expected.encode_bytes()
        assert data.hash_tree_root() == expected.hash_tree_root()
        encoded = msgspec.json.decode(data.to_json())
        assert set(encoded) == {
            "beacon_block_root",
            "slot",
            "payload_present",
            "blob_data_available",
        }
        assert (
            gloas.PayloadAttestationData.from_obj(encoded).hash_tree_root()
            == expected.hash_tree_root()
        )

    with PayloadAttestationDataGloasMainnet.from_obj(expected.to_obj()) as data:
        assert data.hash_tree_root() == expected.hash_tree_root()
