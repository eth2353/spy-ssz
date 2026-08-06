"""Normalized definitions for all named Electra and Fulu SSZ types."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any, Iterator, TypedDict, cast

from .schema import Fork


@dataclass(frozen=True, slots=True)
class TypeDefinition:
    fork: Fork
    name: str
    type_id: int
    descriptor: dict[str, Any]


class _ForkCatalog(TypedDict):
    names: dict[str, int]
    types: list[dict[str, Any]]


class _Catalog(TypedDict):
    forks: dict[str, _ForkCatalog]


@lru_cache(maxsize=1)
def _catalog() -> _Catalog:
    resource = files(__package__).joinpath("consensus_types.json")
    catalog = cast(_Catalog, json.loads(resource.read_text()))
    # EIP-8359 is implemented locally ahead of its inclusion in the upstream
    # consensus-specs package used to generate consensus_types.json.
    for fork_name in ("electra", "fulu"):
        fork_data = catalog["forks"][fork_name]
        body = fork_data["types"][fork_data["names"]["BeaconBlockBody"]]
        if not any(name == "client_data" for name, _ in body["fields"]):
            graffiti_type = dict(body["fields"])["graffiti"]
            body["fields"].append(["client_data", graffiti_type])
            body["repr"] += "\n    client_data: Bytes32"
    return catalog


def get_type_definition(fork: Fork, name: str) -> TypeDefinition:
    fork_data = _catalog()["forks"][fork.name.lower()]
    type_id = fork_data["names"][name]
    return TypeDefinition(fork, name, type_id, fork_data["types"][type_id])


def get_type_shape(fork: Fork, type_id: int) -> dict[str, Any]:
    return _catalog()["forks"][fork.name.lower()]["types"][type_id]


def iter_type_definitions(fork: Fork) -> Iterator[TypeDefinition]:
    fork_data = _catalog()["forks"][fork.name.lower()]
    for name, type_id in fork_data["names"].items():
        yield TypeDefinition(fork, name, type_id, fork_data["types"][type_id])
