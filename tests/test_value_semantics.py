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
