from spy_ssz.consensus_types import get_type_definition, iter_type_definitions
from spy_ssz.schema import Fork


def test_all_supported_fork_named_ssz_types_are_cataloged() -> None:
    assert len(list(iter_type_definitions(Fork.ELECTRA))) == 92
    assert len(list(iter_type_definitions(Fork.FULU))) == 103
    assert len(list(iter_type_definitions(Fork.GLOAS))) == 121


def test_fork_specific_state_definitions_are_distinct() -> None:
    electra = get_type_definition(Fork.ELECTRA, "BeaconState")
    fulu = get_type_definition(Fork.FULU, "BeaconState")
    assert len(electra.descriptor["fields"]) == 37
    assert len(fulu.descriptor["fields"]) == 38
