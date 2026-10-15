"""Measure first and repeated immutable field projections in installed wheels.

Use an isolated interpreter (-I). Decoding and close are outside measured
intervals. Each first-read sample starts with a freshly decoded native owner.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import random
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import msgspec

from spy_ssz import Fork, ObjectKind, Preset, SszObject, get_ssz_type, projections


def measure(
    factory: Callable[[], SszObject],
    read: Callable[[SszObject], Any],
    rounds: int,
    warmup: int,
    *,
    cached: bool = False,
) -> float:
    samples = []
    for repeat in range(rounds + warmup):
        with factory() as value:
            if cached:
                read(value)
            enabled = gc.isenabled()
            gc.disable()
            try:
                before = time.perf_counter_ns()
                result = read(value)
                elapsed = time.perf_counter_ns() - before
            finally:
                if enabled:
                    gc.enable()
            assert result is not None
            if repeat >= warmup:
                samples.append(elapsed)
            del result
    return statistics.median(samples)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1040)
    args = parser.parse_args()
    if args.limit < 1 or args.rounds < 1 or args.warmup < 0:
        parser.error("limit/rounds must be positive and warmup nonnegative")
    cases = []
    manifests = {}
    for manifest_path in sorted(args.corpus.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_bytes())
        manifests[manifest["network"]] = hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest()
        fork = Fork[manifest["fork"].upper()]
        codec = get_ssz_type(
            fork, ObjectKind.SIGNED_BEACON_BLOCK, Preset[manifest["preset"]]
        )
        signing = get_ssz_type(
            fork, ObjectKind.ATTESTATION_DATA, Preset[manifest["preset"]]
        )
        for block in manifest["blocks"][: args.limit]:
            cases.append(
                (manifest_path.parent, manifest["network"], codec, signing, block)
            )
    random.Random(args.seed).shuffle(cases)
    rows = []
    for directory, network, codec, signing, block in cases:
        raw = (directory / block["ssz"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == block["ssz_sha256"]
        with codec.from_ssz(raw) as value:
            canonical = json.loads(value.to_json())
            message = value.message
            expected = projections.project_field(
                codec.expected_fork,
                "SignedBeaconBlock",
                "message",
                canonical["message"],
            )
            assert message == expected
            projection_digest = hashlib.sha256(
                msgspec.json.encode(message.to_obj())
            ).hexdigest()
            assert value.message.slot == int(canonical["message"]["slot"])
            assert (
                value.message.body.randao_reveal.hex()
                == canonical["message"]["body"]["randao_reveal"][2:]
            )
            assert value.signature.hex() == canonical["signature"][2:]
        small = signing.from_obj(
            {
                "slot": str(block["slot"]),
                "index": "0",
                "beacon_block_root": "0x" + "00" * 32,
                "source": {"epoch": "0", "root": "0x" + "00" * 32},
                "target": {"epoch": "0", "root": "0x" + "00" * 32},
            }
        )
        small_ssz = small.to_ssz()
        small.close()

        def factory() -> SszObject:
            return codec.from_ssz(raw)

        def small_factory() -> SszObject:
            return signing.from_ssz(small_ssz)

        timings = {}
        for name, make, read in (
            ("signature", factory, lambda value: value.signature),
            ("message", factory, lambda value: value.message),
            ("nested", factory, lambda value: value.message.body.randao_reveal),
            ("scalar", small_factory, lambda value: value.slot),
            ("small_nested", small_factory, lambda value: value.source),
        ):
            for cached in (False, True):
                timings[name + ("_cached" if cached else "_first")] = measure(
                    make, read, args.rounds, args.warmup, cached=cached
                )
        rows.append(
            {
                "network": network,
                "slot": block["slot"],
                "projection_digest": projection_digest,
                "median_ns": timings,
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "manifests": manifests,
                "rounds": args.rounds,
                "warmup": args.warmup,
                "seed": args.seed,
                "blocks": rows,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
