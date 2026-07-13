"""Normalized definitions for all named Electra, Fulu, and Gloas SSZ types."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Iterator

from .native_object import Fork


@dataclass(frozen=True, slots=True)
class TypeDefinition:
    fork: Fork
    name: str
    type_id: int
    descriptor: dict[str, object]


@lru_cache(maxsize=1)
def _catalog() -> dict[str, object]:
    resource = files(__package__).joinpath("consensus_types.json")
    return json.loads(resource.read_text())


def get_type_definition(fork: Fork, name: str) -> TypeDefinition:
    fork_data = _catalog()["forks"][fork.name.lower()]
    type_id = fork_data["names"][name]
    return TypeDefinition(fork, name, type_id, fork_data["types"][type_id])


def get_type_shape(fork: Fork, type_id: int) -> dict[str, object]:
    return _catalog()["forks"][fork.name.lower()]["types"][type_id]


def iter_type_definitions(fork: Fork) -> Iterator[TypeDefinition]:
    fork_data = _catalog()["forks"][fork.name.lower()]
    for name, type_id in fork_data["names"].items():
        yield TypeDefinition(fork, name, type_id, fork_data["types"][type_id])
