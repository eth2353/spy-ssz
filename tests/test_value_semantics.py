from eth_consensus_specs.electra import mainnet as electra

from spy_ssz.signing import (
    AttestationData,
    AttestationDataMinimal,
    SyncCommitteeContribution,
)


def test_ssz_objects_have_schema_and_preset_scoped_value_semantics() -> None:
    reference = electra.AttestationData()
    with (
        AttestationData.from_ssz(reference.encode_bytes()) as first,
        AttestationData.from_obj(reference.to_obj()) as second,
        AttestationDataMinimal.from_ssz(reference.encode_bytes()) as minimal,
        SyncCommitteeContribution.from_obj(
            electra.SyncCommitteeContribution().to_obj()
        ) as different_schema,
    ):
        assert first == second
        assert hash(first) == hash(second)
        assert len({first, second}) == 1
        assert first != minimal
        assert first != different_schema
        assert first != object()


def test_to_obj_returns_a_detached_value() -> None:
    reference = electra.AttestationData(slot=123)
    with AttestationData.from_obj(reference.to_obj()) as value:
        expected = value.to_obj()
        detached = value.to_obj()
        detached["slot"] = "999"
        detached["source"]["epoch"] = "999"

        assert value.slot == 123
        assert value.source.epoch == 0
        assert value.to_obj() == expected
