from __future__ import annotations

import hashlib
import os

import pytest

from postpy_ssz import hash_pair, merkleize, merkleize_python


@pytest.mark.parametrize(
    "pair",
    [
        bytes(64),
        bytes(range(64)),
        bytes.fromhex("ff" * 64),
        os.urandom(64),
    ],
)
def test_hash_pair(pair: bytes) -> None:
    assert hash_pair(pair) == hashlib.sha256(pair).digest()


@pytest.mark.parametrize("leaf_count", [1, 2, 3, 4, 7, 16, 65])
def test_merkleize(leaf_count: int) -> None:
    chunks = os.urandom(leaf_count * 32)
    assert merkleize(chunks) == merkleize_python(chunks)


def test_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        hash_pair(b"too short")
    with pytest.raises(ValueError):
        merkleize(b"")
    with pytest.raises(ValueError):
        merkleize(b"not a chunk")
