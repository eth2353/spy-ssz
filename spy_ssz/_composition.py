"""Native graph composition for signing containers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import _spy
from ._native import _spy_bytes
from .schema import ObjectKind, get_schema

if TYPE_CHECKING:
    from .ssz import SszObject


_COMPOSITION_FIELDS = {
    ObjectKind.AGGREGATE_AND_PROOF: (
        "aggregate",
        "aggregator_index",
        None,
        "selection_proof",
    ),
    ObjectKind.CONTRIBUTION_AND_PROOF: (
        "contribution",
        "aggregator_index",
        None,
        "selection_proof",
    ),
    ObjectKind.SINGLE_ATTESTATION: (
        "data",
        "committee_index",
        "attester_index",
        "signature",
    ),
    ObjectKind.SIGNED_AGGREGATE_AND_PROOF: (
        "message",
        None,
        None,
        "signature",
    ),
    ObjectKind.SIGNED_CONTRIBUTION_AND_PROOF: (
        "message",
        None,
        None,
        "signature",
    ),
}


def _uint64_bytes(value: Any) -> bytes:
    if isinstance(value, str):
        if value.startswith("0x"):
            encoded = value[2:]
            if len(encoded) % 2 != 0 or len(encoded) > 16:
                raise ValueError("SSZ uint64 hexadecimal value is out of range")
            try:
                return bytes.fromhex(encoded).ljust(8, b"\x00")
            except ValueError:
                raise ValueError("SSZ uint64 field must be hexadecimal") from None
        if (
            not value
            or not value.isdecimal()
            or (len(value) > 1 and value.startswith("0"))
        ):
            raise ValueError("SSZ uint64 field must be a canonical decimal string")
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("SSZ uint64 field must be an integer or numeric string")
    try:
        return value.to_bytes(8, "little", signed=False)
    except OverflowError:
        raise ValueError("SSZ uint64 field is out of range") from None


def _fixed_bytes96(value: Any) -> bytes:
    if isinstance(value, str):
        value = value.removeprefix("0x")
        try:
            value = bytes.fromhex(value)
        except ValueError:
            raise ValueError("96-byte SSZ field must be hexadecimal") from None
    elif isinstance(value, (bytearray, memoryview)):
        value = bytes(value)
    if not isinstance(value, bytes):
        raise TypeError("native SSZ composition requires bytes or hexadecimal strings")
    if len(value) != 96:
        raise ValueError("SSZ field must contain 96 bytes")
    return value


def _compose_fields(cls: type[SszObject], fields: dict[str, Any]) -> Any | None:
    """Compose supported signing containers by cloning a typed child graph."""
    from .ssz import SszObject

    kind = cls.expected_kind
    if kind is None:
        return None
    layout = _COMPOSITION_FIELDS.get(kind)
    if layout is None:
        return None
    child_name, first_name, second_name, fixed_name = layout
    expected_names = {
        name
        for name in (child_name, first_name, second_name, fixed_name)
        if name is not None
    }
    if set(fields) != expected_names:
        return None
    child = fields[child_name]
    if not isinstance(child, SszObject):
        return None
    if child.fork is not cls.expected_fork:
        raise TypeError("nested SSZ object fork does not match its parent")
    if child.preset is not cls.expected_preset:
        raise TypeError("nested SSZ object preset does not match its parent")
    first = _uint64_bytes(fields[first_name]) if first_name is not None else bytes(8)
    second = _uint64_bytes(fields[second_name]) if second_name is not None else bytes(8)
    fixed = _fixed_bytes96(fields[fixed_name])
    first_obj, first_view = _spy_bytes(first)
    second_obj, second_view = _spy_bytes(second)
    fixed_obj, fixed_view = _spy_bytes(fixed)
    definition = get_schema(cls.expected_fork, kind)
    with child._use_handle() as child_handle:
        handle = _spy.lib.spy_ssz_object_compose_signing(
            child_handle,
            kind,
            definition.schema_id,
            first_obj,
            second_obj,
            fixed_obj,
        )
    assert first_view and second_view and fixed_view
    if not handle.p or not _spy.lib.spy_ssz_object_is_valid(handle):
        if handle.p:
            _spy.lib.spy_ssz_object_destroy(handle)
        raise TypeError("nested SSZ object type is incompatible with its parent")
    return handle
