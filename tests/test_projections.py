from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz import Checkpoint
from spy_ssz.projections import AttestationData as AttestationDataProjection
from spy_ssz.signing import AggregateAndProof, AttestationData


ROOT = Path(__file__).parents[1]


def test_attestation_data_has_typed_immutable_projections() -> None:
    reference = electra.AttestationData()
    with AttestationData.from_obj(reference.to_obj()) as value:
        assert value.slot == 0
        assert value.beacon_block_root == bytes(32)
        assert value.source == Checkpoint(epoch=0, root=bytes(32))
        assert value.target == value.source
        assert hash(value.target) == hash(value.source)
        assert value.source.to_obj() == reference.source.to_obj()
        with pytest.raises(FrozenInstanceError):
            value.source.epoch = 1


def test_nested_containers_use_named_projection_types() -> None:
    reference = electra.AggregateAndProof()
    with AggregateAndProof.from_obj(reference.to_obj()) as value:
        assert isinstance(value.aggregate.data, AttestationDataProjection)
        assert isinstance(value.aggregate.data.source, Checkpoint)
        assert value.aggregate.data.slot == 0


def test_generated_stubs_expose_concrete_projection_types() -> None:
    signing_stub = (ROOT / "spy_ssz" / "signing.pyi").read_text()
    assert "def slot(self) -> int" in signing_stub
    assert "def beacon_block_root(self) -> bytes" in signing_stub
    assert "def source(self) -> projections.Checkpoint" in signing_stub
    assert "def target(self) -> projections.Checkpoint" in signing_stub
