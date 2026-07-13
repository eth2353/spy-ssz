"""Benchmark JSON and SSZ codecs over a directory of signed beacon blocks."""

from __future__ import annotations

import argparse
import csv
import gc
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import msgspec
from eth_consensus_specs.altair import mainnet as altair
from eth_consensus_specs.bellatrix import mainnet as bellatrix
from eth_consensus_specs.capella import mainnet as capella
from eth_consensus_specs.deneb import mainnet as deneb
from eth_consensus_specs.electra import mainnet as electra
from eth_consensus_specs.fulu import mainnet as fulu
from eth_consensus_specs.gloas import mainnet as gloas
from eth_consensus_specs.heze import mainnet as heze
from eth_consensus_specs.phase0 import mainnet as phase0


DEFAULT_CORPUS = Path("/Users/luca/Downloads/eth-blocks/beacon_blocks")
SPECS = {
    "phase0": phase0,
    "altair": altair,
    "bellatrix": bellatrix,
    "capella": capella,
    "deneb": deneb,
    "electra": electra,
    "fulu": fulu,
    "gloas": gloas,
    "heze": heze,
}
FORK_SLOT_STARTS = (
    (411_392 * 32, "fulu"),
    (364_032 * 32, "electra"),
    (269_568 * 32, "deneb"),
    (194_048 * 32, "capella"),
    (144_896 * 32, "bellatrix"),
    (74_240 * 32, "altair"),
    (0, "phase0"),
)
KNOWN_SUFFIXES = (".ssz_snappy", ".json", ".ssz", ".bin")


@dataclass(slots=True)
class Sources:
    key: str
    json: Path | None = None
    ssz: Path | None = None


@dataclass(slots=True)
class BlockCase:
    key: str
    fork: str
    spec: Any
    value: Any
    json_bytes: bytes
    ssz_bytes: bytes
    encoded_json_length: int


@dataclass(slots=True)
class Measurement:
    block: str
    fork: str
    metric: str
    byte_length: int
    nanoseconds: int


@dataclass(slots=True)
class Results:
    values: list[Measurement] = field(default_factory=list)

    def add(
        self,
        case: BlockCase,
        metric: str,
        byte_length: int,
        nanoseconds: int,
    ) -> None:
        self.values.append(
            Measurement(case.key, case.fork, metric, byte_length, nanoseconds)
        )


def source_key(root: Path, path: Path) -> str:
    relative = path.relative_to(root).as_posix()
    lowered = relative.lower()
    for suffix in KNOWN_SUFFIXES:
        if lowered.endswith(suffix):
            return relative[: -len(suffix)]
    return relative


def discover(root: Path, limit: int | None) -> list[Sources]:
    grouped: dict[str, Sources] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        lower = path.name.lower()
        if not lower.endswith(KNOWN_SUFFIXES):
            continue
        key = source_key(root, path)
        sources = grouped.setdefault(key, Sources(key))
        if lower.endswith(".json"):
            sources.json = path
        else:
            sources.ssz = path
    result = list(grouped.values())
    if limit is not None:
        result = result[:limit]
    return result


def unwrap_json(raw: bytes) -> tuple[dict[str, Any], str | None]:
    decoded = msgspec.json.decode(raw)
    if not isinstance(decoded, dict):
        raise ValueError("top-level JSON value is not an object")
    version = decoded.get("version")
    value = decoded.get("data", decoded)
    if isinstance(value, dict) and "signed_block" in value:
        value = value["signed_block"]
    if not isinstance(value, dict) or "message" not in value:
        raise ValueError("JSON does not contain a signed beacon block")
    return value, version.lower() if isinstance(version, str) else None


def fork_from_path(path: str) -> str | None:
    lowered = path.lower()
    for fork in reversed(tuple(SPECS)):
        if fork in lowered:
            return fork
    return None


def fork_from_slot(value: dict[str, Any]) -> str | None:
    try:
        slot = int(value["message"]["slot"])
    except (KeyError, TypeError, ValueError):
        return None
    for start, fork in FORK_SLOT_STARTS:
        if slot >= start:
            return fork
    return None


def fork_from_ssz(raw: bytes) -> str | None:
    if len(raw) < 12:
        return None
    message_offset = int.from_bytes(raw[:4], "little")
    if message_offset < 4 or message_offset + 8 > len(raw):
        return None
    slot = int.from_bytes(raw[message_offset : message_offset + 8], "little")
    for start, fork in FORK_SLOT_STARTS:
        if slot >= start:
            return fork
    return None


def decompress_ssz(path: Path, raw: bytes) -> bytes:
    if not path.name.lower().endswith(".ssz_snappy"):
        return raw
    try:
        import snappy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            f"{path}: python-snappy is required for .ssz_snappy files"
        ) from exc
    return snappy.decompress(raw)


def decode_ssz_with_fork(raw: bytes, fork: str) -> Any:
    return SPECS[fork].SignedBeaconBlock.decode_bytes(raw)


def prepare_case(sources: Sources, forced_fork: str) -> BlockCase:
    json_value: dict[str, Any] | None = None
    supplied_json: bytes | None = None
    supplied_ssz: bytes | None = None
    metadata_fork: str | None = None
    if sources.json is not None:
        supplied_json = sources.json.read_bytes()
        json_value, metadata_fork = unwrap_json(supplied_json)
    if sources.ssz is not None:
        supplied_ssz = decompress_ssz(sources.ssz, sources.ssz.read_bytes())

    fork = None if forced_fork == "auto" else forced_fork
    fork = fork or metadata_fork or fork_from_path(sources.key)
    fork = fork or (fork_from_slot(json_value) if json_value is not None else None)
    fork = fork or (fork_from_ssz(supplied_ssz) if supplied_ssz is not None else None)

    value: Any
    if json_value is not None:
        fork = fork or "phase0"
        spec = SPECS[fork]
        value = spec.SignedBeaconBlock.from_obj(json_value)
    elif sources.ssz is not None:
        if fork is None:
            raise ValueError(
                "cannot infer fork for standalone SSZ; use --fork or put the "
                "fork name in its path"
            )
        spec = SPECS[fork]
        assert supplied_ssz is not None
        value = decode_ssz_with_fork(supplied_ssz, fork)
    else:
        raise AssertionError("source group has no input")

    encoded_json = msgspec.json.encode({"data": value.to_obj()})
    encoded_ssz = value.encode_bytes()
    json_bytes = supplied_json or encoded_json
    ssz_bytes = supplied_ssz or encoded_ssz

    # Validate any paired canonical input before timing it.
    if sources.ssz is not None:
        assert supplied_ssz is not None
        supplied_value = decode_ssz_with_fork(supplied_ssz, fork)
        if supplied_value.hash_tree_root() != value.hash_tree_root():
            raise ValueError("paired JSON and SSZ roots differ")

    return BlockCase(
        sources.key,
        fork,
        spec,
        value,
        json_bytes,
        ssz_bytes,
        len(encoded_json),
    )


def elapsed_ns(function: Callable[[], Any], warmup: int, rounds: int) -> int:
    for _ in range(warmup):
        function()
    samples: list[int] = []
    for _ in range(rounds):
        gc.disable()
        try:
            start = time.perf_counter_ns()
            function()
            samples.append(time.perf_counter_ns() - start)
        finally:
            gc.enable()
    return int(statistics.median(samples))


def benchmark_case(
    case: BlockCase,
    results: Results,
    warmup: int,
    rounds: int,
    spy: bool,
) -> None:
    spec = case.spec

    def json_decode() -> Any:
        value, _ = unwrap_json(case.json_bytes)
        return spec.SignedBeaconBlock.from_obj(value)

    results.add(
        case,
        "json_decode",
        len(case.json_bytes),
        elapsed_ns(
            json_decode,
            warmup,
            rounds,
        ),
    )
    results.add(
        case,
        "json_encode",
        case.encoded_json_length,
        elapsed_ns(
            lambda: msgspec.json.encode({"data": case.value.to_obj()}),
            warmup,
            rounds,
        ),
    )
    results.add(
        case,
        "ssz_decode",
        len(case.ssz_bytes),
        elapsed_ns(
            lambda: spec.SignedBeaconBlock.decode_bytes(case.ssz_bytes),
            warmup,
            rounds,
        ),
    )
    results.add(
        case,
        "ssz_encode",
        len(case.ssz_bytes),
        elapsed_ns(case.value.encode_bytes, warmup, rounds),
    )

    if spy and case.fork in {"deneb", "electra", "fulu"}:
        try:
            if case.fork == "deneb":
                from spy_ssz.deneb import DenebSignedBeaconBlock as SpyBlock
            elif case.fork == "electra":
                from spy_ssz.electra import ElectraSignedBeaconBlock as SpyBlock
            else:
                from spy_ssz.fulu import FuluSignedBeaconBlock as SpyBlock
        except (ImportError, AttributeError):
            return

        def spy_json_decode() -> None:
            block = SpyBlock.from_json(case.json_bytes)
            block.close()

        def spy_ssz_decode() -> None:
            block = SpyBlock.from_ssz(case.ssz_bytes)
            block.close()

        try:
            results.add(
                case,
                "spy_json_decode",
                len(case.json_bytes),
                elapsed_ns(spy_json_decode, warmup, rounds),
            )
            results.add(
                case,
                "spy_ssz_decode",
                len(case.ssz_bytes),
                elapsed_ns(spy_ssz_decode, warmup, rounds),
            )
            if case.fork in {"electra", "fulu"}:
                spy_block = SpyBlock.from_ssz(case.ssz_bytes)
                try:
                    spy_json_length = len(spy_block.to_json())
                    spy_ssz_length = len(spy_block.to_ssz())
                    results.add(
                        case,
                        "spy_json_encode",
                        spy_json_length,
                        elapsed_ns(spy_block.to_json, warmup, rounds),
                    )
                    results.add(
                        case,
                        "spy_ssz_encode",
                        spy_ssz_length,
                        elapsed_ns(spy_block.to_ssz, warmup, rounds),
                    )
                finally:
                    spy_block.close()
        except (ValueError, NotImplementedError) as exc:
            print(f"SPy metrics unavailable for {case.key}: {exc}", file=sys.stderr)


def percentile(values: list[float], fraction: float) -> float:
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def print_summary(results: Results) -> None:
    forks = sorted({value.fork for value in results.values})
    for fork_filter in [None, *forks]:
        selected = [
            value
            for value in results.values
            if fork_filter is None or value.fork == fork_filter
        ]
        label = "all forks" if fork_filter is None else fork_filter
        blocks = len({value.block for value in selected})
        print(f"\n{label}: {blocks} blocks")
        print(
            f"{'operation':<22} {'p50 ms':>10} {'p95 ms':>10} "
            f"{'total ms':>11} {'MiB/s':>10}"
        )
        for metric in sorted({value.metric for value in selected}):
            rows = [value for value in selected if value.metric == metric]
            milliseconds = [value.nanoseconds / 1_000_000 for value in rows]
            total_ns = sum(value.nanoseconds for value in rows)
            total_bytes = sum(value.byte_length for value in rows)
            throughput = total_bytes / (1024 * 1024) / (total_ns / 1e9)
            print(
                f"{metric:<22} {statistics.median(milliseconds):10.3f} "
                f"{percentile(milliseconds, 0.95):10.3f} "
                f"{total_ns / 1_000_000:11.3f} {throughput:10.1f}"
            )


def write_csv(path: Path, results: Results) -> None:
    with path.open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(
            ["block", "fork", "operation", "bytes", "nanoseconds", "milliseconds"]
        )
        for value in results.values:
            writer.writerow(
                [
                    value.block,
                    value.fork,
                    value.metric,
                    value.byte_length,
                    value.nanoseconds,
                    value.nanoseconds / 1_000_000,
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=DEFAULT_CORPUS)
    parser.add_argument("--fork", choices=["auto", *SPECS], default="auto")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--csv", type=Path, help="write per-block timings")
    parser.add_argument(
        "--no-spy",
        action="store_true",
        help="skip available spy-ssz SPy codec measurements",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.rounds < 1 or args.warmup < 0:
        raise SystemExit("--rounds must be positive and --warmup non-negative")
    try:
        sources = discover(args.directory, args.limit)
    except PermissionError as exc:
        raise SystemExit(
            f"cannot read {args.directory}: {exc}\n"
            "Grant the terminal/Codex process access to Downloads or copy the corpus "
            "under the workspace."
        ) from exc
    if not sources:
        raise SystemExit(f"no JSON/SSZ block files found under {args.directory}")

    results = Results()
    skipped: list[tuple[str, str]] = []
    print(
        f"discovered {len(sources)} block groups; "
        f"warmup={args.warmup}, rounds={args.rounds}"
    )
    for index, source in enumerate(sources, 1):
        try:
            case = prepare_case(source, args.fork)
            benchmark_case(case, results, args.warmup, args.rounds, not args.no_spy)
            print(
                f"[{index:>5}/{len(sources)}] {case.fork:<7} {case.key}",
                file=sys.stderr,
            )
        except Exception as exc:  # Keep a large corpus benchmark progressing.
            skipped.append((source.key, str(exc)))
            print(f"skip {source.key}: {exc}", file=sys.stderr)

    if not results.values:
        raise SystemExit("no blocks could be decoded")
    print_summary(results)
    if args.csv is not None:
        write_csv(args.csv, results)
        print(f"\nwrote {args.csv}")
    if skipped:
        print(f"\nskipped {len(skipped)} block groups", file=sys.stderr)
        for key, reason in skipped[:20]:
            print(f"  {key}: {reason}", file=sys.stderr)
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more", file=sys.stderr)


if __name__ == "__main__":
    main()
