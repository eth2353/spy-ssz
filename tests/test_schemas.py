import pytest

from spy_ssz.schema import get_schema, schema_definitions, schema_for
from spy_ssz.ssz import Fork, ObjectKind


def test_fork_ids_follow_consensus_chronology() -> None:
    assert list(Fork) == [
        Fork.PHASE0,
        Fork.ALTAIR,
        Fork.BELLATRIX,
        Fork.CAPELLA,
        Fork.DENEB,
        Fork.ELECTRA,
        Fork.FULU,
    ]
    assert [fork.value for fork in Fork] == list(range(7))


def test_single_schema_codec_lookup_rejects_multiplexed_codecs() -> None:
    assert schema_for("electra_block").fork is Fork.ELECTRA
    with pytest.raises(ValueError, match="expected one schema for 'signing'"):
        schema_for("signing")


def test_only_electra_and_fulu_schemas_are_registered() -> None:
    assert {schema.fork for schema in schema_definitions()} == {
        Fork.ELECTRA,
        Fork.FULU,
    }
    with pytest.raises(KeyError):
        get_schema(Fork.DENEB, ObjectKind.SIGNED_BEACON_BLOCK)
