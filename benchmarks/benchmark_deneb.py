from __future__ import annotations

import gc
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import msgspec
from eth_consensus_specs.deneb import mainnet as spec

from postpy_ssz.deneb import DenebSignedBeaconBlock, decode_deneb_block
from postpy_ssz.native_deneb import NativeDenebBlock


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "block-sample-3642900.json"
SSZ_SAMPLE = ROOT / "block-sample-3642900.bin"


def measure(function: Callable[[], Any], rounds: int) -> tuple[float, float]:
    samples: list[float] = []
    for _ in range(rounds):
        gc.disable()
        try:
            start = time.perf_counter_ns()
            function()
            samples.append((time.perf_counter_ns() - start) / 1_000_000)
        finally:
            gc.enable()
    return statistics.median(samples), min(samples)


def measure_cold_roots(blocks: list[Any]) -> tuple[float, float]:
    samples: list[float] = []
    for block in blocks:
        gc.disable()
        try:
            start = time.perf_counter_ns()
            block.hash_tree_root()
            samples.append((time.perf_counter_ns() - start) / 1_000_000)
        finally:
            gc.enable()
    return statistics.median(samples), min(samples)


def show(label: str, result: tuple[float, float]) -> None:
    median, best = result
    print(f"{label:<30} {median:8.3f} ms  (best {best:8.3f})")


def main() -> None:
    raw = SAMPLE.read_bytes()
    ssz_raw = SSZ_SAMPLE.read_bytes()
    generic_obj = msgspec.json.decode(raw)["data"]
    reference = spec.SignedBeaconBlock.from_obj(generic_obj)
    fast = decode_deneb_block(raw)
    native = NativeDenebBlock.from_json(raw)
    native_ssz = NativeDenebBlock.from_ssz(ssz_raw)
    assert fast.message_hash_tree_root() == reference.message.hash_tree_root()
    assert fast.hash_tree_root() == reference.hash_tree_root()
    assert native.hash_tree_root() == reference.hash_tree_root()
    assert native_ssz.hash_tree_root() == reference.hash_tree_root()

    def native_decode() -> None:
        block = NativeDenebBlock.from_json(raw)
        block.close()

    def native_full() -> bytes:
        block = NativeDenebBlock.from_json(raw)
        try:
            return block.hash_tree_root()
        finally:
            block.close()

    def native_ssz_decode() -> None:
        block = NativeDenebBlock.from_ssz(ssz_raw)
        block.close()

    def native_ssz_full() -> bytes:
        block = NativeDenebBlock.from_ssz(ssz_raw)
        try:
            return block.hash_tree_root()
        finally:
            block.close()

    native_cold = [NativeDenebBlock.from_json(raw) for _ in range(50)]

    fast_cold = [decode_deneb_block(raw) for _ in range(50)]
    reference_cold = [spec.SignedBeaconBlock.from_obj(generic_obj) for _ in range(20)]

    print(f"sample: {len(raw):,} bytes, Deneb slot {fast.message.slot}")
    print(f"block root:  0x{fast.message_hash_tree_root().hex()}")
    print(f"signed root: 0x{fast.hash_tree_root().hex()}\n")
    show("SPy native decode", measure(native_decode, 300))
    show("SPy native cold root", measure_cold_roots(native_cold))
    show("SPy native cached root", measure(native.hash_tree_root, 10_000))
    native_full_result = measure(native_full, 100)
    show("SPy native decode + root", native_full_result)
    show("SPy native SSZ decode", measure(native_ssz_decode, 300))
    show("SPy SSZ decode + root", measure(native_ssz_full, 100))
    print()
    show("msgspec typed decode", measure(lambda: decode_deneb_block(raw), 300))
    show("specialized cold root", measure_cold_roots(fast_cold))
    show("specialized cached root", measure(fast.hash_tree_root, 10_000))
    fast_full = measure(lambda: decode_deneb_block(raw).hash_tree_root(), 100)
    show("specialized decode + root", fast_full)
    print()
    show("reference object build", measure(lambda: spec.SignedBeaconBlock.from_obj(generic_obj), 30))
    show("reference cold root", measure_cold_roots(reference_cold))
    reference_full = measure(
        lambda: spec.SignedBeaconBlock.from_obj(msgspec.json.decode(raw)["data"]).hash_tree_root(),
        30,
    )
    show("reference decode + root", reference_full)
    print(
        f"\nnative vs reference: {reference_full[0] / native_full_result[0]:.2f}x"
    )
    print(f"specialized Python vs reference: {reference_full[0] / fast_full[0]:.2f}x")

    for block in native_cold:
        block.close()
    native.close()
    native_ssz.close()


if __name__ == "__main__":
    main()
