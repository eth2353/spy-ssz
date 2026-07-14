from importlib import import_module

import pytest

import spy_ssz
from spy_ssz import Preset, SszObject, get_ssz_type
from spy_ssz.schema import (
    get_schema,
    module_for_codec,
    schema_definitions,
    schema_for,
)
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


def test_public_type_resolver_is_complete_and_coherent() -> None:
    for definition in schema_definitions():
        module = import_module(f"spy_ssz.{module_for_codec(definition.codec)}")
        for preset_name in definition.presets:
            preset = Preset[preset_name.upper()]
            expected = getattr(module, f"{definition.python_type}{preset.name.title()}")
            resolved = get_ssz_type(definition.fork, definition.kind, preset)
            assert resolved is expected
            assert resolved is getattr(spy_ssz, expected.__name__)
            assert issubclass(resolved, SszObject)


def test_public_type_resolver_rejects_unsupported_combination() -> None:
    with pytest.raises(
        NotImplementedError,
        match="^no SPy schema for DENEB/ATTESTATION/GNOSIS$",
    ):
        get_ssz_type(Fork.DENEB, ObjectKind.ATTESTATION, Preset.GNOSIS)


def test_fulu_resolver_aliases_unchanged_electra_schemas() -> None:
    electra_kinds = {
        definition.kind
        for definition in schema_definitions()
        if definition.fork is Fork.ELECTRA
    }
    for kind in electra_kinds:
        for preset in Preset:
            fulu_type = get_ssz_type(Fork.FULU, kind, preset)
            if kind is ObjectKind.SIGNED_BEACON_BLOCK:
                assert fulu_type is not get_ssz_type(Fork.ELECTRA, kind, preset)
                assert fulu_type.expected_fork is Fork.FULU
            else:
                assert fulu_type is get_ssz_type(Fork.ELECTRA, kind, preset)
