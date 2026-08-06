"""Reference SSZ containers for the EIP-8359 block-body extension."""

from eth_consensus_specs.electra import mainnet as electra
from remerkleable.byte_arrays import ByteVector
from remerkleable.complex import Container

ClientData = ByteVector[32]

_body_fields = {
    **electra.BeaconBlockBody.__annotations__,
    "client_data": ClientData,
}
BeaconBlockBody = type(
    "BeaconBlockBody",
    (Container,),
    {"__annotations__": _body_fields},
)


class BeaconBlock(Container):
    slot: electra.Slot
    proposer_index: electra.ValidatorIndex
    parent_root: electra.Root
    state_root: electra.Root
    body: BeaconBlockBody


class SignedBeaconBlock(Container):
    message: BeaconBlock
    signature: electra.BLSSignature


_blinded_body_fields = {
    ("execution_payload_header" if name == "execution_payload" else name): (
        electra.ExecutionPayloadHeader if name == "execution_payload" else field_type
    )
    for name, field_type in _body_fields.items()
}
BlindedBeaconBlockBody = type(
    "BlindedBeaconBlockBody",
    (Container,),
    {"__annotations__": _blinded_body_fields},
)


class BlindedBeaconBlock(Container):
    slot: electra.Slot
    proposer_index: electra.ValidatorIndex
    parent_root: electra.Root
    state_root: electra.Root
    body: BlindedBeaconBlockBody


class SignedBlindedBeaconBlock(Container):
    message: BlindedBeaconBlock
    signature: electra.BLSSignature
