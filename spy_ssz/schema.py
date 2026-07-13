"""Runtime schema metadata loaded from the authoritative YAML definition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from importlib.resources import files
from typing import Any

import yaml


@lru_cache(maxsize=1)
def _source() -> dict[str, Any]:
    resource = files(__package__).joinpath("schemas.yaml")
    value = yaml.safe_load(resource.read_text())
    if value.get("format") != 1:
        raise ValueError("unsupported schema metadata format")
    return value


Fork = IntEnum("Fork", _source()["forks"], module=__name__)
ObjectKind = IntEnum("ObjectKind", _source()["object_kinds"], module=__name__)


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    schema_id: int
    fork: Fork
    kind: ObjectKind
    codec: str
    python_type: str
    presets: tuple[str, ...]
    consensus_type: str | None = None


@lru_cache(maxsize=1)
def schema_definitions() -> tuple[SchemaDefinition, ...]:
    definitions = tuple(
        SchemaDefinition(
            name=value["name"],
            schema_id=int(value["id"]),
            fork=Fork[value["fork"]],
            kind=ObjectKind[value["kind"]],
            codec=value["codec"],
            python_type=value["python_type"],
            presets=tuple(value["presets"]),
            consensus_type=value.get("consensus_type"),
        )
        for value in _source()["schemas"]
    )
    schema_ids = [value.schema_id for value in definitions]
    schema_keys = [(value.fork, value.kind) for value in definitions]
    if len(set(schema_ids)) != len(schema_ids):
        raise ValueError("schema IDs must be unique")
    if len(set(schema_keys)) != len(schema_keys):
        raise ValueError("fork/object-kind schema pairs must be unique")
    return definitions


@lru_cache(maxsize=1)
def _schemas_by_codec() -> dict[str, tuple[SchemaDefinition, ...]]:
    result: dict[str, list[SchemaDefinition]] = {}
    for definition in schema_definitions():
        result.setdefault(definition.codec, []).append(definition)
    return {codec: tuple(definitions) for codec, definitions in result.items()}


@lru_cache(maxsize=1)
def _schemas_by_key() -> dict[tuple[Fork, ObjectKind], SchemaDefinition]:
    return {
        (definition.fork, definition.kind): definition
        for definition in schema_definitions()
    }


def schemas_for(codec: str) -> tuple[SchemaDefinition, ...]:
    return _schemas_by_codec().get(codec, ())


def schema_for(codec: str) -> SchemaDefinition:
    """Return the sole schema for a codec that does not multiplex object kinds."""
    definitions = schemas_for(codec)
    if len(definitions) != 1:
        raise ValueError(f"expected one schema for {codec!r}, found {len(definitions)}")
    return definitions[0]


def module_for_codec(codec: str) -> str:
    return _source()["codecs"][codec]


def get_schema(fork: Fork, kind: ObjectKind) -> SchemaDefinition:
    return _schemas_by_key()[fork, kind]
