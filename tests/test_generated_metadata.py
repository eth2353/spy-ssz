import subprocess
import sys
from pathlib import Path

from spy_ssz.consensus_types import get_type_definition
from spy_ssz.schema import Fork, schema_definitions
from tools.build_extension import generate_metadata


ROOT = Path(__file__).parents[1]


def test_build_metadata_generation_does_not_spawn_python(monkeypatch) -> None:
    def fail(*args, **kwargs) -> None:
        raise AssertionError("metadata generation must run in-process")

    monkeypatch.setattr(subprocess, "run", fail)
    generate_metadata()


def test_spy_metadata_matches_authoritative_yaml() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_spy_metadata.py"), "--check"],
        cwd=ROOT,
        check=True,
    )


def test_runtime_consensus_types_exist_in_generated_catalog() -> None:
    for schema in schema_definitions():
        if schema.consensus_type is None or schema.fork is Fork.DENEB:
            continue
        assert (
            get_type_definition(schema.fork, schema.consensus_type).name
            == schema.consensus_type
        )


def test_schema_ids_are_unique() -> None:
    definitions = schema_definitions()
    assert len({value.schema_id for value in definitions}) == len(definitions)
    assert len({(value.fork, value.kind) for value in definitions}) == len(definitions)
