"""Benchmark native JSON array encoding for small immutable SSZ objects."""

from __future__ import annotations

import argparse
import gc
import statistics
import time
from contextlib import nullcontext

import msgspec
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz import encode_json_array
from spy_ssz.signing import AttestationData
from spy_ssz.ssz import _JSON_ARRAY_ENCODERS


def percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


class _WithoutNativeBatch:
    def __enter__(self) -> None:
        self.key = (
            AttestationData.expected_fork,
            AttestationData.expected_kind,
            AttestationData.expected_preset,
        )
        self.codec = _JSON_ARRAY_ENCODERS.pop(self.key)

    def __exit__(self, *exc_info: object) -> None:
        _JSON_ARRAY_ENCODERS[self.key] = self.codec


def benchmark(
    size: int, warmup: int, rounds: int, *, native_batch: bool
) -> tuple[int, int, float]:
    values = [
        AttestationData.from_obj(electra.AttestationData(slot=index).to_obj())
        for index in range(size)
    ]
    try:
        context = nullcontext() if native_batch else _WithoutNativeBatch()
        with context:
            encoded = encode_json_array(values)
            assert len(msgspec.json.decode(encoded)) == size
            for _ in range(warmup):
                encode_json_array(values)

            samples: list[int] = []
            for _ in range(rounds):
                gc.disable()
                try:
                    start = time.perf_counter_ns()
                    encode_json_array(values)
                    samples.append(time.perf_counter_ns() - start)
                finally:
                    gc.enable()
        return (
            len(encoded),
            int(statistics.median(samples)),
            percentile(samples, 0.95),
        )
    finally:
        for value in values:
            value.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[10, 100, 1_000])
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if any(size < 1 for size in args.sizes):
        raise SystemExit("--sizes must contain positive integers")
    if args.warmup < 0 or args.rounds < 1:
        raise SystemExit("--warmup must be non-negative and --rounds positive")

    print(
        f"warmup={args.warmup}, rounds={args.rounds}\n\n"
        f"{'objects':>8} {'bytes':>10} {'fallback ms':>12} {'native ms':>10} "
        f"{'speedup':>9} {'native p95':>11} {'MiB/s':>10}"
    )
    for size in args.sizes:
        byte_length, fallback_ns, _ = benchmark(
            size, args.warmup, args.rounds, native_batch=False
        )
        native_length, native_ns, native_p95_ns = benchmark(
            size, args.warmup, args.rounds, native_batch=True
        )
        assert native_length == byte_length
        print(
            f"{size:8d} {byte_length:10d} {fallback_ns / 1e6:12.3f} "
            f"{native_ns / 1e6:10.3f} {fallback_ns / native_ns:8.2f}x "
            f"{native_p95_ns / 1e6:11.3f} "
            f"{byte_length / (1024 * 1024) / (native_ns / 1e9):10.1f}"
        )


if __name__ == "__main__":
    main()
