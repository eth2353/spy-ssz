"""Generate SPy constants from authoritative schema and preset YAML files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMAS = ROOT / "spy_ssz" / "schemas.yaml"
METADATA = ROOT / "src" / "metadata.spy"
METADATA_HEADER = ROOT / "src" / "metadata_constants.h"
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


def render_metadata_header() -> str:
    source = _load(SCHEMAS)
    lines = [
        "/* Generated from spy_ssz/schemas.yaml; do not edit. */",
        "#ifndef SPY_SSZ_METADATA_CONSTANTS_H",
        "#define SPY_SSZ_METADATA_CONSTANTS_H",
        "",
    ]
    for name, value in source["object_kinds"].items():
        lines.append(f"#define SPY_SSZ_OBJECT_{name} {int(value)}")
    lines.extend(["", "#endif", ""])
    return "\n".join(lines)


def render_preset_config() -> str:
    from spy_ssz.preset import Preset
    from spy_ssz.presets import SSZ_LIMIT_KEYS, preset_sources

    sources = preset_sources()
    presets = [(preset.name.lower(), sources[preset.name]) for preset in Preset]

    lines = [
        '"""Generated from canonical spy_ssz/presets/<preset>/*.yaml; do not edit."""',
        "",
    ]
    for preset in Preset:
        lines.append(f"PRESET_{preset.name}: i32 = {preset.value}")
    lines.append("")
    for key in SSZ_LIMIT_KEYS:
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
        METADATA_HEADER: render_metadata_header(),
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
