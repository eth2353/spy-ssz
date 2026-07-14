from types import SimpleNamespace

from spy_ssz.schema import Fork
from tools import check_consensus_vectors


def test_vector_definitions_cover_all_implemented_forks() -> None:
    definitions = check_consensus_vectors._vector_definitions()

    assert {definition.fork for definition in definitions} == {
        Fork.ELECTRA,
        Fork.FULU,
        Fork.GLOAS,
    }
    assert len(definitions) == 51


def test_required_gloas_validator_types_include_beacon_blocks() -> None:
    assert {"BeaconBlock", "SignedBeaconBlock"}.issubset(
        check_consensus_vectors.REQUIRED_VALIDATOR_TYPES[Fork.GLOAS]
    )


def test_codec_class_uses_explicit_preset_variant(monkeypatch) -> None:
    mainnet = type("Mainnet", (), {})
    minimal = type("Minimal", (), {})
    module = SimpleNamespace(ExampleMainnet=mainnet, ExampleMinimal=minimal)
    definition = SimpleNamespace(codec="example", python_type="Example")

    monkeypatch.setattr(
        check_consensus_vectors, "module_for_codec", lambda _: "example"
    )
    monkeypatch.setattr(check_consensus_vectors, "import_module", lambda _: module)

    assert check_consensus_vectors._codec_class(definition, "mainnet") is mainnet
    assert check_consensus_vectors._codec_class(definition, "minimal") is minimal
