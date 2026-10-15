"""Time an installed native build against paired Beacon API block manifests.

Run with the target environment's Python and -I so the checkout cannot shadow
its installed wheel. Disk reads, input verification, and cold-hash object
construction are outside the measured intervals. Decode timings include close.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import random
import statistics
import time
from pathlib import Path

import spy_ssz
from spy_ssz import Fork, ObjectKind, Preset, get_ssz_type


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int, help="maximum blocks per network")
    args = parser.parse_args()
    if (
        args.rounds < 1
        or args.warmup < 0
        or (args.limit is not None and args.limit < 1)
    ):
        parser.error("rounds and limit must be positive; warmup must be nonnegative")
    cases = []
    manifests = {}
    for path in sorted(args.corpus.glob("*/manifest.json")):
        manifest = json.loads(path.read_bytes())
        manifests[manifest["network"]] = hashlib.sha256(path.read_bytes()).hexdigest()
        codec = get_ssz_type(
            Fork[manifest["fork"].upper()],
            ObjectKind.SIGNED_BEACON_BLOCK,
            Preset[manifest["preset"]],
        )
        for block in manifest["blocks"][: args.limit]:
            cases.append((path.parent, manifest["network"], codec, block))
    if not cases:
        parser.error("no block manifests found")
    random.Random(args.seed).shuffle(cases)
    rows = []
    started = time.time()
    for index, (directory, network, codec, block) in enumerate(cases, 1):
        raw_json = (directory / block["json"]).read_bytes()
        raw_ssz = (directory / block["ssz"]).read_bytes()
        assert hashlib.sha256(raw_json).hexdigest() == block["json_sha256"]
        assert hashlib.sha256(raw_ssz).hexdigest() == block["ssz_sha256"]
        with codec.from_ssz(raw_ssz) as value:
            root = value.hash_tree_root()
            assert value.to_ssz() == raw_ssz
            with codec.from_json(raw_json) as decoded:
                assert decoded.hash_tree_root() == root
                assert decoded.to_ssz() == raw_ssz
            with codec.from_json(b'{"data":' + value.to_json() + b"}") as decoded:
                assert decoded.hash_tree_root() == root

            def json_decode():
                codec.from_json(raw_json).close()

            def ssz_decode():
                codec.from_ssz(raw_ssz).close()

            operations = {
                "json_decode": json_decode,
                "ssz_decode": ssz_decode,
                "json_encode": value.to_json,
                "ssz_encode": value.to_ssz,
                "hash_cold": None,
                "hash_cached": value.hash_tree_root,
            }
            timings = {}
            for name, operation in operations.items():
                samples = []
                enabled = gc.isenabled()
                gc.disable()
                try:
                    for repeat in range(args.warmup + args.rounds):
                        fresh = codec.from_ssz(raw_ssz) if operation is None else None
                        call = fresh.hash_tree_root if fresh is not None else operation
                        try:
                            before = time.perf_counter_ns()
                            call()
                            elapsed = time.perf_counter_ns() - before
                        finally:
                            if fresh is not None:
                                fresh.close()
                        if repeat >= args.warmup:
                            samples.append(elapsed)
                finally:
                    if enabled:
                        gc.enable()
                timings[name] = statistics.median(samples)
            rows.append(
                {
                    "network": network,
                    "slot": block["slot"],
                    "root": root.hex(),
                    "json_bytes": len(raw_json),
                    "ssz_bytes": len(raw_ssz),
                    "ns": timings,
                }
            )
        if index % 100 == 0:
            print(f"{index}/{len(cases)} blocks", flush=True)
    args.output.write_text(
        json.dumps(
            {
                "package": spy_ssz.__file__,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "started": started,
                "finished": time.time(),
                "rounds": args.rounds,
                "warmup": args.warmup,
                "seed": args.seed,
                "manifests": manifests,
                "blocks": rows,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Wrote {len(rows)} complete measurements to {args.output}")


if __name__ == "__main__":
    main()
