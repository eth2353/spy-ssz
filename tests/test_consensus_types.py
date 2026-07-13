from spy_ssz.consensus_types import (
    get_type_definition,
    get_type_shape,
    iter_type_definitions,
)
from spy_ssz.schema import Fork


def test_all_electra_plus_named_ssz_types_are_cataloged() -> None:
    assert len(list(iter_type_definitions(Fork.ELECTRA))) == 92
    assert len(list(iter_type_definitions(Fork.FULU))) == 103
    assert len(list(iter_type_definitions(Fork.GLOAS))) == 121
    assert len(list(iter_type_definitions(Fork.HEZE))) == 123


def test_gloas_progressive_definitions_preserve_fields_and_element_types() -> None:
    attestation = get_type_definition(Fork.GLOAS, "Attestation")
    assert attestation.descriptor["kind"] == "progressive_container"
    assert attestation.descriptor["active_fields"] == [1, 1, 1, 1]

    aggregation_id = dict(attestation.descriptor["fields"])["aggregation_bits"]
    aggregation = get_type_shape(Fork.GLOAS, aggregation_id)
    assert aggregation["kind"] == "progressive_bitlist"


def test_fork_specific_state_definitions_are_distinct() -> None:
    electra = get_type_definition(Fork.ELECTRA, "BeaconState")
    fulu = get_type_definition(Fork.FULU, "BeaconState")
    assert len(electra.descriptor["fields"]) == 37
    assert len(fulu.descriptor["fields"]) == 38
