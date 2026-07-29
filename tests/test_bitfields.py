from collections.abc import Iterable
from typing import Any

import pytest

from spy_ssz import Bitfield


@pytest.mark.parametrize(
    ("length", "values", "expected"),
    [
        (1, (), "0x00"),
        (8, (), "0x00"),
        (9, (), "0x0000"),
        (10, [True, False, 2], "0x0500"),
        (8, (index % 2 for index in range(8)), "0xaa"),
    ],
)
def test_bitvector_construction_and_serialization(
    length: int, values: Iterable[bool | int], expected: str
) -> None:
    value = Bitfield.bitvector(length, values)

    assert len(value) == length
    assert value.to_hex() == expected
    assert value.to_obj() == expected
    assert Bitfield.from_hex(expected, bitlist=False).to_hex() == expected


@pytest.mark.parametrize(
    ("limit", "values", "expected"),
    [
        (0, (), "0x01"),
        (8, (), "0x01"),
        (8, [True, False, 2], "0x0d"),
        (8, [False] * 7, "0x80"),
        (8, [True] * 8, "0xff01"),
        (10, (index % 2 for index in range(10)), "0xaa06"),
    ],
)
def test_bitlist_construction_and_serialization(
    limit: int, values: Iterable[bool | int], expected: str
) -> None:
    expected_values = [bool(value) for value in values]
    value = Bitfield.bitlist(limit, expected_values)

    assert len(value) == len(expected_values)
    assert list(value) == expected_values
    assert value.to_hex() == expected
    assert value.to_obj() == expected
    assert Bitfield.from_hex(expected, bitlist=True).to_hex() == expected


def test_bitvector_rejects_values_beyond_declared_length() -> None:
    with pytest.raises(ValueError, match="more values"):
        Bitfield.bitvector(2, [False, False, False])


def test_bitlist_enforces_declared_limit() -> None:
    with pytest.raises(ValueError, match="exceeds"):
        Bitfield.bitlist(2, [False, False, False])


@pytest.mark.parametrize("factory", [Bitfield.bitvector, Bitfield.bitlist])
def test_bitfield_rejects_invalid_sizes(factory: Any) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        factory(-1)
    with pytest.raises(TypeError, match="integer"):
        factory(True)


@pytest.mark.parametrize("factory", [Bitfield.bitvector, Bitfield.bitlist])
def test_bitfield_rejects_non_integer_values(factory: Any) -> None:
    with pytest.raises(TypeError, match="bool or int"):
        factory(1, ["true"])
