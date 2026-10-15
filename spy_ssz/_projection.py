"""Copy selected native graph subtrees into independent immutable values.

Only copied snapshot records cross the bridge, never native graph pointers.
The caller holds its owner's lock for the entire traversal, including all CFFI
calls and copies. Returned projections contain only detached Python values.
"""

from __future__ import annotations

from typing import Any
from functools import lru_cache

from . import _spy
from ._native import _spy_bytes
from .consensus_types import get_type_definition, get_type_shape
from .schema import Fork


@lru_cache(maxsize=None)
def field_types(fork: Fork, consensus_type: str) -> dict[str, tuple[int, int]]:
    from .projections import _FIELD_TYPES

    known = _FIELD_TYPES.get((fork, consensus_type))
    if known is not None:
        return known
    # Public project_field also supports named catalog types without native codecs.
    definition = get_type_definition(fork, consensus_type)
    return {
        name: (index, type_id)
        for index, (name, type_id) in enumerate(definition.descriptor["fields"])
    }


class _NativeProjection:
    def __init__(self, nodes: Any, snapshot: bytearray, fork: Fork):
        from .projections import _PROJECTION_TYPES

        self.projection_types = _PROJECTION_TYPES
        self.nodes = nodes
        self.node_index = 0
        self.snapshot = snapshot
        self.position = 0
        self.fork = fork

    def data(self, length: int) -> bytes:
        start = self.position
        self.position += length
        return bytes(self.snapshot[start : self.position])

    def value(self, type_id: int) -> Any:
        shape = get_type_shape(self.fork, type_id)
        kind = shape["kind"]
        record = self.nodes[self.node_index]
        self.node_index += 1
        if kind in {"uint", "boolean"}:
            value = int.from_bytes(self.data(record.data_length), "little")
            return bool(value) if kind == "boolean" else value
        if kind in {"container", "progressive_container"}:
            return self.projection_types[(self.fork, type_id)](
                **{name: self.value(child_type) for name, child_type in shape["fields"]}
            )
        if kind in {"list", "progressive_list", "vector"}:
            if record.kind in {10, 11}:  # Packed basic lists retain element width.
                length, width = record.data_length, record.element_width
                data = self.data(length)
                element = get_type_shape(self.fork, shape["element"])
                if width <= 0 or length % width:
                    raise ValueError("SPy native projection basic-list width failed")
                values = (
                    int.from_bytes(data[offset : offset + width], "little")
                    for offset in range(0, length, width)
                )
                return (
                    tuple(map(bool, values))
                    if element["kind"] == "boolean"
                    else tuple(values)
                )
            return tuple(
                self.value(shape["element"]) for _ in range(record.child_count)
            )
        return self.data(record.data_length)


def project_native_field(
    handle: Any, fork: Fork, consensus_type: str, name: str
) -> Any:
    index, type_id = field_types(fork, consensus_type)[name]
    sizes = _spy.ffi.new("int32_t[2]")
    if not _spy.lib.spy_ssz_object_projection_size(handle, index, sizes):
        raise ValueError("SPy native projection sizing failed")
    node_count, size = sizes
    nodes = _spy.ffi.new("spy_projection_node[]", node_count)
    snapshot = bytearray(size)
    output, view = _spy_bytes(snapshot)
    valid = _spy.lib.spy_ssz_object_projection_copy(
        handle, index, nodes, node_count, output
    )
    assert view
    if not valid:
        raise ValueError("SPy native projection copying failed")
    reader = _NativeProjection(nodes, snapshot, fork)
    result = reader.value(type_id)
    if reader.position != size or reader.node_index != node_count:
        raise ValueError("SPy native projection layout failed")
    return result
