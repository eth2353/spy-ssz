"""Deterministic human-readable formatting for SSZ values."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def format_value(value: Any) -> str:
    if isinstance(value, bytes):
        return f"0x{value.hex()}"
    if isinstance(value, str):
        if value.startswith("0x"):
            try:
                return f"0x{bytes.fromhex(value[2:]).hex()}"
            except ValueError:
                pass
        if value.isdecimal():
            return str(int(value))
        return repr(value)
    if isinstance(value, tuple):
        items = ", ".join(format_value(item) for item in value)
        if len(value) == 1:
            items += ","
        return f"({items})"
    if isinstance(value, list):
        return f"[{', '.join(format_value(item) for item in value)}]"
    if isinstance(value, dict):
        items = ", ".join(
            f"{key!r}: {format_value(item)}" for key, item in value.items()
        )
        return f"{{{items}}}"
    return repr(value)


def format_container(type_name: str, values: Iterable[tuple[str, Any]]) -> str:
    fields = ", ".join(f"{name}={format_value(value)}" for name, value in values)
    return f"{type_name}({fields})"
