"""Python value conversion for JSON-backed SSZ projections."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from copy import deepcopy
from typing import Any

from ._repr import format_container


class Bitfield:
    """Small immutable SSZ bitvector or bitlist.

    Bitvectors retain their declared length and zero-fill any values omitted by
    the input iterable. Bitlists retain the iterable's length and include their
    SSZ termination bit when serialized.
    """

    __slots__ = ("_bitlist", "_data", "_length")

    def __init__(self, data: bytes, length: int, *, bitlist: bool = False):
        length = self._size(length, "bitfield length")
        if not isinstance(data, bytes):
            raise TypeError("bitfield data must be bytes")
        if len(data) != (length + 7) // 8:
            raise ValueError("bitfield data does not match its declared length")
        if length % 8 and data[-1] >> (length % 8):
            raise ValueError("bitfield padding bits must be zero")
        self._bitlist = bitlist
        self._data = data
        self._length = length

    def __repr__(self) -> str:
        return format_container(
            type(self).__name__,
            (("length", self._length), ("data", self._data)),
        )

    __str__ = __repr__

    @staticmethod
    def _size(value: int, name: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
        return value

    @staticmethod
    def _bit(value: bool | int) -> bool:
        if not isinstance(value, (bool, int)):
            raise TypeError("bitfield values must be bool or int")
        return bool(value)

    @classmethod
    def bitvector(cls, length: int, values: Iterable[bool | int] = ()) -> Bitfield:
        """Construct a zero-filled SSZ bitvector with a declared length."""
        length = cls._size(length, "bitvector length")
        data = bytearray((length + 7) // 8)
        for index, value in enumerate(values):
            if index >= length:
                raise ValueError(
                    f"bitvector has more values than its declared length {length}"
                )
            if cls._bit(value):
                data[index // 8] |= 1 << (index % 8)
        return cls(bytes(data), length)

    @classmethod
    def bitlist(cls, limit: int, values: Iterable[bool | int] = ()) -> Bitfield:
        """Construct an SSZ bitlist and enforce its declared limit."""
        limit = cls._size(limit, "bitlist limit")
        bits: list[bool] = []
        for value in values:
            if len(bits) >= limit:
                raise ValueError(f"bitlist exceeds its declared limit {limit}")
            bits.append(cls._bit(value))

        data = bytearray((len(bits) + 7) // 8)
        for index, value in enumerate(bits):
            if value:
                data[index // 8] |= 1 << (index % 8)
        return cls(bytes(data), len(bits), bitlist=True)

    @classmethod
    def from_hex(cls, value: str, *, bitlist: bool) -> Bitfield:
        data = bytearray.fromhex(value.removeprefix("0x"))
        length = len(data) * 8
        if bitlist:
            if not data or data[-1] == 0:
                raise ValueError("bitlist is missing its termination bit")
            marker = data[-1].bit_length() - 1
            length = (len(data) - 1) * 8 + marker
            data[-1] &= (1 << marker) - 1
            if marker == 0:
                data.pop()
        return cls(bytes(data), length, bitlist=bitlist)

    def to_hex(self) -> str:
        """Serialize the bitfield as Beacon API hexadecimal SSZ data."""
        data = bytearray(self._data)
        if self._bitlist:
            encoded_length = (self._length + 1 + 7) // 8
            if len(data) < encoded_length:
                data.extend(b"\x00" * (encoded_length - len(data)))
            data[self._length // 8] |= 1 << (self._length % 8)
        return f"0x{data.hex()}"

    def to_obj(self) -> str:
        """Return the Beacon API object representation."""
        return self.to_hex()

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> bool:
        if index < 0:
            index += self._length
        if index < 0 or index >= self._length:
            raise IndexError(index)
        return bool(self._data[index // 8] & (1 << (index % 8)))

    def __iter__(self) -> Iterator[bool]:
        for index in range(self._length):
            yield self[index]

    def count(self, value: bool = True) -> int:
        ones = sum(byte.bit_count() for byte in self._data)
        return ones if value else self._length - ones


def _project_value(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("0x"):
            return bytes.fromhex(value[2:])
        if value.isdecimal():
            return int(value)
    if isinstance(value, dict):
        return _FrozenView(value)
    if isinstance(value, list):
        return tuple(_project_value(item) for item in value)
    return value


class _FrozenView:
    __slots__ = ("_value",)

    def __init__(self, value: dict[str, Any]):
        self._value = value

    def __getattr__(self, name: str) -> Any:
        try:
            return _project_value(self._value[name])
        except KeyError:
            raise AttributeError(name) from None

    def to_obj(self) -> dict[str, Any]:
        return deepcopy(self._value)


def _json_compatible(value: Any) -> Any:
    if hasattr(value, "to_obj"):
        return _json_compatible(value.to_obj())
    if isinstance(value, bytes):
        return f"0x{value.hex()}"
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


# Preserve the established public location for repr, pickle, and introspection.
Bitfield.__module__ = "spy_ssz.ssz"
