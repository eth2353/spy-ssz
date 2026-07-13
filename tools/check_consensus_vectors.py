"""Check Electra and Fulu codecs against consensus-specs SSZ static vectors."""

from __future__ import annotations

import argparse
from collections import Counter
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml

from spy_ssz.schema import Fork, module_for_codec, schema_definitions


SUPPORTED_FORKS = (Fork.ELECTRA, Fork.FULU)
SUPPORTED_PRESETS = ("minimal", "mainnet")


def _snappy_module() -> Any:
    try:
        return import_module("snappy")
    except ModuleNotFoundError:
        raise SystemExit(
            "python-snappy is required; run with "
            "`uv run --with python-snappy python tools/check_consensus_vectors.py ...`"
        ) from None


def _vector_root(root: Path, preset: str) -> Path:
    candidate = root / preset
    if candidate.is_dir():
        return candidate
    nested = root / "tests" / preset
    if nested.is_dir():
        return nested
    raise SystemExit(
        f"could not find {preset!r} vectors under {root}; expected "
        f"{candidate} or {nested}"
    )


def _codec_class(definition: Any, preset: str) -> type[Any]:
    module_name = module_for_codec(definition.codec)
    module = import_module(f"spy_ssz.{module_name}")
    suffix = "" if preset == "mainnet" else preset.title()
    return getattr(module, f"{definition.python_type}{suffix}")


def check_vectors(root: Path, presets: tuple[str, ...]) -> bool:
    snappy = _snappy_module()
    counts: Counter[tuple[str, str, str]] = Counter()
    failures: list[str] = []
    supported_types: set[tuple[str, str]] = set()
    codec_targets = 0
    total = 0
    passed = 0

    for preset in presets:
        preset_root = _vector_root(root, preset)
        for definition in schema_definitions():
            if definition.fork not in SUPPORTED_FORKS:
                continue
            if definition.consensus_type is None or preset not in definition.presets:
                continue

            fork = definition.fork.name.lower()
            type_name = definition.consensus_type
            cases_root = preset_root / fork / "ssz_static" / type_name
            if not cases_root.is_dir():
                failures.append(f"missing vectors: {preset}/{fork}/{type_name}")
                continue

            codec_class = _codec_class(definition, preset)
            serialized_paths = sorted(cases_root.glob("*/*/serialized.ssz_snappy"))
            if not serialized_paths:
                failures.append(f"no vectors: {preset}/{fork}/{type_name}")
                continue
            supported_types.add((fork, type_name))
            codec_targets += 1

            for serialized_path in serialized_paths:
                total += 1
                counts[(preset, fork, type_name)] += 1
                case = serialized_path.parent
                try:
                    serialized = snappy.decompress(serialized_path.read_bytes())
                    roots = yaml.safe_load((case / "roots.yaml").read_text())
                    expected_root = bytes.fromhex(roots["root"].removeprefix("0x"))
                    with codec_class.from_ssz(serialized) as value:
                        actual_root = value.hash_tree_root()
                        encoded = value.to_ssz()
                    if actual_root != expected_root:
                        raise AssertionError(
                            f"root 0x{actual_root.hex()} != 0x{expected_root.hex()}"
                        )
                    if encoded != serialized:
                        raise AssertionError(
                            "canonical roundtrip differs "
                            f"({len(encoded)} != {len(serialized)} bytes)"
                        )
                    passed += 1
                except Exception as exc:
                    failures.append(f"{case}: {type(exc).__name__}: {exc}")

    print(
        f"supported_types={len(supported_types)} codec_targets={codec_targets} "
        f"vectors={total} "
        f"passed={passed} failed={len(failures)}"
    )
    for (preset, fork, type_name), count in sorted(counts.items()):
        print(f"coverage {preset}/{fork}/{type_name}={count}")
    for failure in failures[:100]:
        print(f"FAIL {failure}")
    if len(failures) > 100:
        print(f"... {len(failures) - 100} more failures")
    return not failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        type=Path,
        help="extracted archive root containing tests/<preset> or <preset>",
    )
    parser.add_argument(
        "--preset",
        action="append",
        choices=SUPPORTED_PRESETS,
        dest="presets",
        help="preset to check; repeat for both (default: minimal and mainnet)",
    )
    args = parser.parse_args()
    presets = tuple(args.presets or SUPPORTED_PRESETS)
    if not check_vectors(args.root, presets):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
