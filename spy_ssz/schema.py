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
    return tuple(
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


def schemas_for(codec: str) -> tuple[SchemaDefinition, ...]:
    return tuple(value for value in schema_definitions() if value.codec == codec)


def module_for_codec(codec: str) -> str:
    return _source()["codecs"][codec]


def get_schema(fork: Fork, kind: ObjectKind) -> SchemaDefinition:
    for value in schema_definitions():
        if value.fork is fork and value.kind is kind:
            return value
    raise KeyError((fork, kind))
