from __future__ import annotations

import hashlib
import statistics
import time
from pathlib import Path

from postpy_ssz import hash_pair, merkleize, merkleize_python
from remerkleable.tree import RootNode, subtree_fill_to_contents


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "block-sample-3642900.json"


def packed_sample() -> bytes:
    raw = SAMPLE.read_bytes()
    padding = (-len(raw)) % 32
    return raw + bytes(padding)


def measure(function, argument: bytes, rounds: int) -> tuple[float, bytes]:
    samples: list[float] = []
    result = b""
    for _ in range(rounds):
        start = time.perf_counter_ns()
        result = function(argument)
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    return statistics.median(samples), result


def merkleize_remerkleable(chunks: bytes) -> bytes:
    leaves = [RootNode(chunks[i : i + 32]) for i in range(0, len(chunks), 32)]
    depth = (len(leaves) - 1).bit_length()
    return bytes(subtree_fill_to_contents(leaves, depth).merkle_root())


def main() -> None:
    chunks = packed_sample()
    pair = chunks[:64]
    pair_native_ms, pair_native = measure(hash_pair, pair, 2_000)
    pair_hashlib_ms, pair_hashlib = measure(
        lambda value: hashlib.sha256(value).digest(), pair, 2_000
    )
    assert pair_native == pair_hashlib

    native_ms, native_root = measure(merkleize, chunks, 15)
    python_ms, python_root = measure(merkleize_python, chunks, 15)
    remerkleable_ms, remerkleable_root = measure(
        merkleize_remerkleable, chunks, 15
    )
    assert native_root == python_root == remerkleable_root

    leaf_count = len(chunks) // 32
    padded_count = 1 << (leaf_count - 1).bit_length()
    print(f"sample bytes:         {SAMPLE.stat().st_size:,}")
    print(f"chunks:               {leaf_count:,} ({padded_count:,} padded)")
    print(f"root:                 {native_root.hex()}")
    print(f"pair SPy/CFFI:        {pair_native_ms * 1_000:.2f} us")
    print(f"pair hashlib:         {pair_hashlib_ms * 1_000:.2f} us")
    print(f"bulk SPy/CFFI:        {native_ms:.3f} ms")
    print(f"Python + hashlib:     {python_ms:.3f} ms")
    print(f"eth-remerkleable:     {remerkleable_ms:.3f} ms")
    print(f"vs hashlib loop:      {python_ms / native_ms:.2f}x")
    print(f"vs eth-remerkleable:  {remerkleable_ms / native_ms:.2f}x")


if __name__ == "__main__":
    main()
