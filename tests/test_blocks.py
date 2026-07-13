import msgspec
from eth_consensus_specs.electra import mainnet as electra
from remerkleable.byte_arrays import ByteVector
from remerkleable.complex import Container, List

from spy_ssz.blocks import (
    ElectraBeaconBlockContentsMainnet,
    ElectraBlindedBeaconBlockMainnet,
)


Blob = ByteVector[131072]


class BlockContents(Container):
    block: electra.BeaconBlock
    kzg_proofs: List[electra.KZGProof, 4096]
    blobs: List[Blob, 4096]


class SignedBlockContents(Container):
    signed_block: electra.SignedBeaconBlock
    kzg_proofs: List[electra.KZGProof, 4096]
    blobs: List[Blob, 4096]


_body_fields = {
    ("execution_payload_header" if name == "execution_payload" else name): (
        electra.ExecutionPayloadHeader if name == "execution_payload" else field_type
    )
    for name, field_type in electra.BeaconBlockBody.__annotations__.items()
}
BlindedBody = type(
    "BlindedBody", (Container,), {"__annotations__": _body_fields}
)


class BlindedBlock(Container):
    slot: electra.Slot
    proposer_index: electra.ValidatorIndex
    parent_root: electra.Root
    state_root: electra.Root
    body: BlindedBody


class SignedBlindedBlock(Container):
    message: BlindedBlock
    signature: electra.BLSSignature


def test_block_contents_json_ssz_signing_and_projections() -> None:
    reference = BlockContents(block=electra.BeaconBlock(slot=12, proposer_index=34))
    raw_json = msgspec.json.encode({"version": "electra", "data": reference.to_obj()})

    with ElectraBeaconBlockContentsMainnet.from_json(raw_json) as value:
        assert value.hash_tree_root() == reference.hash_tree_root()
        assert value.to_ssz() == reference.encode_bytes()
        assert value.block_hash_tree_root() == (
            f"0x{reference.block.hash_tree_root().hex()}"
        )
        header = value.header_dict()
        assert header["slot"] == "12"
        assert header["proposer_index"] == "34"
        assert header["body_root"] == f"0x{reference.block.body.hash_tree_root().hex()}"
        signed = value.sign(bytes(96))
        try:
            signed_reference = SignedBlockContents(
                signed_block=electra.SignedBeaconBlock(message=reference.block)
            )
            assert signed.hash_tree_root() == signed_reference.hash_tree_root()
            assert signed.to_ssz() == signed_reference.encode_bytes()
        finally:
            signed.close()

    with ElectraBeaconBlockContentsMainnet.from_ssz(
        reference.encode_bytes()
    ) as value:
        assert value.hash_tree_root() == reference.hash_tree_root()
        assert BlockContents.from_obj(
            msgspec.json.decode(value.to_json())
        ).hash_tree_root() == reference.hash_tree_root()


def test_blinded_block_json_ssz_signing_and_projections() -> None:
    reference = BlindedBlock(slot=56, proposer_index=78)
    raw_json = msgspec.json.encode({"version": "electra", "data": reference.to_obj()})

    with ElectraBlindedBeaconBlockMainnet.from_json(raw_json) as value:
        assert value.hash_tree_root() == reference.hash_tree_root()
        assert value.to_ssz() == reference.encode_bytes()
        assert value.block_hash_tree_root() == f"0x{reference.hash_tree_root().hex()}"
        assert value.header_dict()["body_root"] == (
            f"0x{reference.body.hash_tree_root().hex()}"
        )
        signed = value.sign(bytes(96))
        try:
            signed_reference = SignedBlindedBlock(message=reference)
            assert signed.hash_tree_root() == signed_reference.hash_tree_root()
            assert signed.to_ssz() == signed_reference.encode_bytes()
        finally:
            signed.close()

    with ElectraBlindedBeaconBlockMainnet.from_ssz(
        reference.encode_bytes()
    ) as value:
        assert value.hash_tree_root() == reference.hash_tree_root()
        assert BlindedBlock.from_obj(
            msgspec.json.decode(value.to_json())
        ).hash_tree_root() == reference.hash_tree_root()
