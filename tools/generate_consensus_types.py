"""Generate the normalized Electra+ SSZ type catalog from consensus-specs."""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

from remerkleable.basic import boolean, uint
from remerkleable.bitfields import Bitlist, Bitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container, List, Vector
from remerkleable.core import View
from remerkleable.progressive import (
    CompatibleUnion,
    ProgressiveBitlist,
    ProgressiveByteList,
    ProgressiveContainer,
    ProgressiveList,
)
from remerkleable.union import Union


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "spy_ssz" / "consensus_types.json"
FORK_MODULES = {
    "electra": "eth_consensus_specs.electra.mainnet",
    "fulu": "eth_consensus_specs.fulu.mainnet",
}
GENERIC_EXPORTS = {
    "View",
    "boolean",
    "Container",
    "List",
    "Vector",
    "uint8",
    "uint32",
    "uint64",
    "uint256",
    "Bytes1",
    "Bytes4",
    "Bytes8",
    "Bytes20",
    "Bytes32",
    "Bytes48",
    "Bytes96",
    "Bitlist",
    "Bitvector",
    "ByteList",
    "ByteVector",
    "ProgressiveBitlist",
    "ProgressiveByteList",
    "ProgressiveContainer",
    "ProgressiveList",
}


class CatalogBuilder:
    def __init__(self) -> None:
        self.indices: dict[type[View], int] = {}
        self.types: list[dict[str, Any] | None] = []

    def reference(self, typ: type[View] | None) -> int:
        if typ is None:
            return -1
        existing = self.indices.get(typ)
        if existing is not None:
            return existing
        index = len(self.types)
        self.indices[typ] = index
        self.types.append(None)
        self.types[index] = self.describe(typ)
        return index

    def describe(self, typ: type[View]) -> dict[str, Any]:
        base: dict[str, Any] = {"repr": typ.type_repr()}
        if issubclass(typ, boolean):
            return base | {"kind": "boolean", "byte_length": 1}
        if issubclass(typ, uint):
            return base | {"kind": "uint", "byte_length": typ.type_byte_length()}
        if issubclass(typ, ProgressiveByteList):
            return base | {"kind": "progressive_byte_list"}
        if issubclass(typ, ProgressiveBitlist):
            return base | {"kind": "progressive_bitlist"}
        if issubclass(typ, ByteList):
            return base | {"kind": "byte_list", "limit": typ.limit()}
        if issubclass(typ, ByteVector):
            return base | {"kind": "byte_vector", "length": typ.vector_length()}
        if issubclass(typ, Bitlist):
            return base | {"kind": "bitlist", "limit": typ.limit()}
        if issubclass(typ, Bitvector):
            return base | {"kind": "bitvector", "length": typ.vector_length()}
        if issubclass(typ, CompatibleUnion):
            return base | {
                "kind": "compatible_union",
                "options": [self.reference(option) for option in typ.options()],
            }
        if issubclass(typ, Union):
            return base | {
                "kind": "union",
                "options": [self.reference(option) for option in typ.options()],
            }
        if issubclass(typ, ProgressiveContainer):
            return base | {
                "kind": "progressive_container",
                "fields": [
                    [name, self.reference(field_type)]
                    for name, field_type in typ.fields().items()
                ],
                "active_fields": list(typ._active_fields),
            }
        if issubclass(typ, Container):
            return base | {
                "kind": "container",
                "fields": [
                    [name, self.reference(field_type)]
                    for name, field_type in typ.fields().items()
                ],
            }
        if issubclass(typ, ProgressiveList):
            return base | {
                "kind": "progressive_list",
                "element": self.reference(typ.element_cls()),
            }
        if issubclass(typ, List):
            return base | {
                "kind": "list",
                "element": self.reference(typ.element_cls()),
                "limit": typ.limit(),
            }
        if issubclass(typ, Vector):
            return base | {
                "kind": "vector",
                "element": self.reference(typ.element_cls()),
                "length": typ.vector_length(),
            }
        raise TypeError(f"unsupported SSZ type: {typ!r}")


def main() -> None:
    forks: dict[str, Any] = {}
    for fork, module_name in FORK_MODULES.items():
        module = __import__(module_name, fromlist=["mainnet"])
        builder = CatalogBuilder()
        names: dict[str, int] = {}
        for name, value in vars(module).items():
            if (
                name.startswith("_")
                or name in GENERIC_EXPORTS
                or not isinstance(value, type)
            ):
                continue
            try:
                if issubclass(value, View):
                    names[name] = builder.reference(value)
            except TypeError:
                continue
        forks[fork] = {"names": names, "types": builder.types}
    catalog = {
        "format": 1,
        "source": {
            "package": "eth-consensus-specs",
            "version": version("eth-consensus-specs"),
            "preset": "mainnet",
        },
        "forks": forks,
    }
    OUTPUT.write_text(json.dumps(catalog, separators=(",", ":")) + "\n")
    print(
        ", ".join(
            f"{fork}: {len(data['names'])} names/{len(data['types'])} shapes"
            for fork, data in forks.items()
        )
    )


if __name__ == "__main__":
    main()
