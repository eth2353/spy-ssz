from dataclasses import FrozenInstanceError
from copy import copy
from importlib import import_module
from threading import Event, Thread
from pathlib import Path

import pytest
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz import Checkpoint, projections
from spy_ssz.signing import (
    AggregateAndProofElectra,
    AttestationDataElectra,
)
from spy_ssz.ssz import SszObject
from spy_ssz import Fork, ObjectKind, Preset, get_ssz_type


ROOT = Path(__file__).parents[1]


def test_public_project_field_supports_catalog_types_without_codecs() -> None:
    from spy_ssz import Fork

    assert projections.project_field(Fork.ELECTRA, "Checkpoint", "epoch", "123") == 123
    assert projections.project_field(
        Fork.GLOAS, "Checkpoint", "root", "0x" + "ab" * 32
    ) == bytes.fromhex("ab" * 32)


@pytest.mark.parametrize("fork", [Fork.ELECTRA, Fork.FULU, Fork.GLOAS])
@pytest.mark.parametrize("preset", list(Preset))
@pytest.mark.parametrize("length", [0, 8, 9])
def test_native_bitlist_termination_and_packed_uint_widths(
    fork, preset, length
) -> None:
    reference_preset = "minimal" if preset is Preset.MINIMAL else "mainnet"
    spec = import_module(f"eth_consensus_specs.{fork.name.lower()}.{reference_preset}")
    bits = [index % 2 == 0 for index in range(length)]
    reference = spec.Attestation(aggregation_bits=bits)
    codec = get_ssz_type(fork, ObjectKind.ATTESTATION, preset)
    with codec.from_ssz(reference.encode_bytes()) as value:
        assert list(value.aggregation_bits) == bits
        assert value.aggregation_bits.to_hex() == reference.aggregation_bits.to_obj()
        assert value.committee_bits.to_hex() == reference.committee_bits.to_obj()
    indices = [0, 2**32 + 1, 2**64 - 1]
    reference = spec.IndexedAttestation(attesting_indices=indices)
    codec = get_ssz_type(fork, ObjectKind.INDEXED_ATTESTATION, preset)
    with codec.from_ssz(reference.encode_bytes()) as value:
        assert value.attesting_indices == tuple(indices)


@pytest.mark.parametrize("fork", [Fork.ELECTRA, Fork.FULU, Fork.GLOAS])
def test_native_nested_uint256_uses_full_storage_width(fork) -> None:
    spec = import_module(f"eth_consensus_specs.{fork.name.lower()}.mainnet")
    payload = spec.ExecutionPayload(base_fee_per_gas=2**256 - 1)
    if fork is Fork.GLOAS:
        reference = spec.ExecutionPayloadEnvelope(payload=payload)
        codec = get_ssz_type(fork, ObjectKind.EXECUTION_PAYLOAD_ENVELOPE)
        with codec.from_ssz(reference.encode_bytes()) as value:
            assert value.payload.base_fee_per_gas == 2**256 - 1
    else:
        reference = spec.SignedBeaconBlock(
            message=spec.BeaconBlock(
                body=spec.BeaconBlockBody(execution_payload=payload)
            )
        )
        codec = get_ssz_type(fork, ObjectKind.SIGNED_BEACON_BLOCK)
        with codec.from_ssz(reference.encode_bytes()) as value:
            assert value.message.body.execution_payload.base_fee_per_gas == 2**256 - 1


def test_attestation_data_has_typed_immutable_projections() -> None:
    reference = electra.AttestationData()
    with AttestationDataElectra.from_obj(reference.to_obj()) as value:
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
    with AggregateAndProofElectra.from_obj(reference.to_obj()) as value:
        assert isinstance(value.aggregate.data, projections.AttestationData)
        assert isinstance(value.aggregate.data.source, Checkpoint)
        assert value.aggregate.data.slot == 0


def test_native_field_reads_bypass_json_and_survive_close(monkeypatch) -> None:
    reference = electra.AggregateAndProof()
    value = AggregateAndProofElectra.from_ssz(reference.encode_bytes())
    independent = copy(value)

    def unexpected_json(self):
        raise AssertionError("attribute reads must not decode the full JSON graph")

    monkeypatch.setattr(SszObject, "_decoded_obj", unexpected_json)
    snapshot = value.aggregate
    assert snapshot is value.aggregate
    assert snapshot.data is value.aggregate.data
    assert snapshot == independent.aggregate
    assert snapshot is not independent.aggregate
    with pytest.raises(AttributeError):
        value.missing_field
    assert value._obj_cache is None
    value.close()
    assert not value._projection_cache
    assert snapshot.data.source == Checkpoint(epoch=0, root=bytes(32))
    with pytest.raises(RuntimeError, match="closed"):
        value.aggregate
    assert independent.aggregate.data.slot == 0
    independent.close()


def test_native_snapshot_rejects_invalid_fields_and_short_buffers() -> None:
    from spy_ssz import _spy
    from spy_ssz._native import _spy_bytes

    with AttestationDataElectra.from_ssz(
        electra.AttestationData().encode_bytes()
    ) as value:
        with value._use_handle() as handle:
            sizes = _spy.ffi.new("int32_t[2]")
            for index in (-1, 5):
                assert not _spy.lib.spy_ssz_object_projection_size(handle, index, sizes)
            assert _spy.lib.spy_ssz_object_projection_size(handle, 0, sizes)
            count, length = sizes
            assert count == 1 and length == 32
            records = _spy.ffi.new("spy_projection_node[]", count)
            data, view = _spy_bytes(bytearray(length - 1))
            assert not _spy.lib.spy_ssz_object_projection_copy(
                handle, 0, records, count, data
            )
            assert view
            data, view = _spy_bytes(bytearray(length))
            assert not _spy.lib.spy_ssz_object_projection_copy(
                handle, 0, records, 0, data
            )
            assert not _spy.lib.spy_ssz_object_projection_copy(
                handle, -1, records, count, data
            )
            assert view
            oversized = _spy.ffi.new("spy_BytesObject *")
            oversized.length = 2**31
            assert not _spy.lib.spy_ssz_object_projection_copy(
                handle, 0, records, count, oversized
            )


def test_close_waits_for_complete_native_projection(monkeypatch) -> None:
    from spy_ssz._projection import _NativeProjection

    value = AggregateAndProofElectra.from_ssz(
        electra.AggregateAndProof().encode_bytes()
    )
    started = Event()
    release = Event()
    close_started = Event()
    closed = Event()
    snapshots = []
    errors = []
    original = _NativeProjection.data

    def blocking_data(self, length):
        started.set()
        if not release.wait(timeout=5):
            raise TimeoutError("test did not release projection")
        return original(self, length)

    def read():
        try:
            snapshots.append(value.aggregate)
        except BaseException as error:
            errors.append(error)

    def close():
        close_started.set()
        value.close()
        closed.set()

    monkeypatch.setattr(_NativeProjection, "data", blocking_data)
    reader = Thread(target=read)
    closer = Thread(target=close)
    reader.start()
    assert started.wait(timeout=5)
    closer.start()
    assert close_started.wait(timeout=5)
    assert not closed.wait(timeout=0.05)
    release.set()
    reader.join(timeout=5)
    closer.join(timeout=5)
    assert not reader.is_alive() and not closer.is_alive()
    assert not errors
    assert snapshots[0].data.slot == 0


def test_generated_stubs_expose_concrete_projection_types() -> None:
    signing_stub = (ROOT / "spy_ssz" / "signing.pyi").read_text()
    projections_stub = (ROOT / "spy_ssz" / "projections.pyi").read_text()
    assert "def slot(self) -> int" in signing_stub
    assert "def beacon_block_root(self) -> bytes" in signing_stub
    assert "def source(self) -> projections.Checkpoint" in signing_stub
    assert "def target(self) -> projections.Checkpoint" in signing_stub
    assert (
        """class Checkpoint(Projection):
    def __init__(
        self,
        epoch: int,
        root: bytes,
    ) -> None: ..."""
        in projections_stub
    )
