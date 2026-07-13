"""Generate SPy constants from authoritative schema and preset YAML files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "spy_ssz" / "schemas.yaml"
PRESETS = ROOT / "spy_ssz" / "presets"
METADATA = ROOT / "src" / "metadata.spy"
PRESET_CONFIG = ROOT / "src" / "preset_config.spy"


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def render_metadata() -> str:
    source = _load(SCHEMAS)
    lines = [
        '"""Generated from spy_ssz/schemas.yaml; do not edit."""',
        "",
    ]
    for name, value in source["forks"].items():
        lines.append(f"FORK_{name}: i32 = {int(value)}")
    lines.append("")
    for name, value in source["object_kinds"].items():
        lines.append(f"OBJECT_{name}: i32 = {int(value)}")
    lines.append("")
    for schema in source["schemas"]:
        lines.append(f"SCHEMA_{schema['name']}: i32 = {int(schema['id'])}")
    return "\n".join(lines) + "\n"


def render_preset_config() -> str:
    paths = sorted(PRESETS.glob("*.yaml"))
    presets = [(path.stem, _load(path)) for path in paths]
    order = {name: int(values["PRESET_ID"]) for name, values in presets}
    presets.sort(key=lambda item: order[item[0]])
    keys = tuple(key for key in presets[0][1] if key != "PRESET_ID")
    for name, values in presets:
        if tuple(key for key in values if key != "PRESET_ID") != keys:
            raise ValueError(f"{name} preset keys differ from mainnet")

    lines = [
        '"""Generated from spy_ssz/presets/*.yaml; do not edit."""',
        "",
    ]
    for name, index in sorted(order.items(), key=lambda item: item[1]):
        lines.append(f"PRESET_{name.upper()}: i32 = {index}")
    lines.append("")
    for key in keys:
        function = key.lower()
        lines.append(f"def preset_{function}(preset: i32) -> i32:")
        for index, (name, values) in enumerate(presets):
            prefix = "if" if index == 0 else "elif"
            lines.append(f"    {prefix} preset == PRESET_{name.upper()}:")
            lines.append(f"        return {int(values[key])}")
        lines.append("    return 0")
        lines.append("")
    return "\n".join(lines)


def generate(*, check: bool = False) -> None:
    outputs = {
        METADATA: render_metadata(),
        PRESET_CONFIG: render_preset_config(),
    }
    stale = [path for path, value in outputs.items() if not path.exists() or path.read_text() != value]
    if check and stale:
        raise SystemExit("generated SPy metadata is stale: " + ", ".join(map(str, stale)))
    for path, value in outputs.items():
        path.write_text(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=args.check)


if __name__ == "__main__":
    main()
