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
PYTHON_ENUMS = ROOT / "spy_ssz" / "_schema_enums.py"
PRESET_CONFIG = ROOT / "src" / "preset_config.spy"
PACKAGE_STUB = ROOT / "spy_ssz" / "__init__.pyi"
TYPE_STUBS = {
    module: ROOT / "spy_ssz" / f"{module}.pyi"
    for module in ("blocks", "deneb", "electra", "fulu", "gloas", "signing")
}


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
    return "\n".join(lines).rstrip() + "\n"


def render_python_enums() -> str:
    source = _load(SCHEMAS)
    lines = [
        '"""Generated from spy_ssz/schemas.yaml; do not edit."""',
        "",
        "from enum import IntEnum",
        "",
        "",
    ]
    for class_name, key in (("Fork", "forks"), ("ObjectKind", "object_kinds")):
        lines.append(f"class {class_name}(IntEnum):")
        for name, value in source[key].items():
            lines.append(f"    {name} = {int(value)}")
        lines.extend(["", ""])
    return "\n".join(lines).rstrip() + "\n"


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


def _type_exports(schema: dict[str, Any]) -> list[str]:
    return [
        schema["python_type"],
        *[f"{schema['python_type']}{preset.title()}" for preset in schema["presets"]],
    ]


def _render_dynamic_stub(
    schemas: list[dict[str, Any]], *, alias_all: bool = False
) -> str:
    lines = [
        '"""Generated from spy_ssz/schemas.yaml; do not edit."""',
        "",
        "from .ssz import SszObject",
        "",
    ]
    for schema_index, schema in enumerate(schemas):
        base = schema["python_type"]
        lines.extend([f"class {base}(SszObject): ...", ""])
        for index, preset in enumerate(schema["presets"]):
            variant = f"{base}{preset.title()}"
            if alias_all or preset == "mainnet":
                lines.append(f"{variant} = {base}")
                if index + 1 < len(schema["presets"]):
                    lines.append("")
            else:
                lines.append(f"class {variant}({base}): ...")
        last_preset_is_alias = alias_all or schema["presets"][-1] == "mainnet"
        if schema_index + 1 < len(schemas) and last_preset_is_alias:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _stub_method(name: str, return_type: str) -> list[str]:
    signature = f"    def {name}(self, signature: str | bytes) -> {return_type}: ..."
    if len(signature) <= 88:
        return [signature]
    return [
        f"    def {name}(",
        "        self, signature: str | bytes",
        f"    ) -> {return_type}: ...",
    ]


def _render_blocks_stub(schemas: list[dict[str, Any]]) -> str:
    by_kind = {schema["kind"]: schema for schema in schemas}
    contents = by_kind["BEACON_BLOCK_CONTENTS"]["python_type"]
    signed_contents = by_kind["SIGNED_BEACON_BLOCK_CONTENTS"]["python_type"]
    blinded = by_kind["BLINDED_BEACON_BLOCK"]["python_type"]
    signed_blinded = by_kind["SIGNED_BLINDED_BEACON_BLOCK"]["python_type"]
    presets = by_kind["BEACON_BLOCK_CONTENTS"]["presets"]
    lines = [
        '"""Generated from spy_ssz/schemas.yaml; do not edit."""',
        "",
        "from .ssz import SszObject",
        "",
        f"class {contents}(SszObject):",
        "    def header_dict(self) -> dict[str, str]: ...",
        "    def block_hash_tree_root(self) -> str: ...",
        *_stub_method("sign", signed_contents),
        f"    @classmethod\n    def signed_type(cls) -> type[{signed_contents}]: ...",
        "",
        f"class {signed_contents}(SszObject): ...",
        "",
        f"class {blinded}(SszObject):",
        "    def header_dict(self) -> dict[str, str]: ...",
        "    def block_hash_tree_root(self) -> str: ...",
        *_stub_method("sign", signed_blinded),
        f"    @classmethod\n    def signed_type(cls) -> type[{signed_blinded}]: ...",
        "",
        f"class {signed_blinded}(SszObject): ...",
    ]
    for preset in presets:
        suffix = preset.title()
        lines.extend(
            [
                f"class {signed_contents}{suffix}({signed_contents}): ...",
                "",
                f"class {contents}{suffix}({contents}):",
                *_stub_method("sign", f"{signed_contents}{suffix}"),
                f"    @classmethod\n    def signed_type(cls) -> type[{signed_contents}{suffix}]: ...",
                "",
                f"class {signed_blinded}{suffix}({signed_blinded}): ...",
                "",
                f"class {blinded}{suffix}({blinded}):",
                *_stub_method("sign", f"{signed_blinded}{suffix}"),
                f"    @classmethod\n    def signed_type(cls) -> type[{signed_blinded}{suffix}]: ...",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_type_stubs() -> dict[Path, str]:
    source = _load(SCHEMAS)
    schemas = source["schemas"]
    by_module: dict[str, list[dict[str, Any]]] = {}
    for schema in schemas:
        module = source["codecs"][schema["codec"]]
        by_module.setdefault(module, []).append(schema)

    stubs = {
        TYPE_STUBS["blocks"]: _render_blocks_stub(by_module["blocks"]),
        TYPE_STUBS["deneb"]: _render_dynamic_stub(by_module["deneb"], alias_all=True),
        TYPE_STUBS["electra"]: _render_dynamic_stub(by_module["electra"]),
        TYPE_STUBS["fulu"]: _render_dynamic_stub(by_module["fulu"]),
        TYPE_STUBS["gloas"]: _render_dynamic_stub(by_module["gloas"], alias_all=True),
        TYPE_STUBS["signing"]: _render_dynamic_stub(by_module["signing"]),
    }

    lines = [
        '"""Generated from spy_ssz/schemas.yaml; do not edit."""',
        "",
        "from ._schema_enums import (",
        "    Fork as Fork,",
        "    ObjectKind as ObjectKind,",
        ")",
        "from .consensus_types import (",
        "    TypeDefinition as TypeDefinition,",
        "    get_type_definition as get_type_definition,",
        "    get_type_shape as get_type_shape,",
        "    iter_type_definitions as iter_type_definitions,",
        ")",
        "from .preset import (",
        "    Preset as Preset,",
        "    PresetConfig as PresetConfig,",
        "    load_preset as load_preset,",
        ")",
        "from .ssz import (",
        "    SszObject as SszObject,",
        "    decode_json as decode_json,",
        "    decode_ssz as decode_ssz,",
        ")",
    ]
    for module in sorted(by_module):
        exports = [
            export for schema in by_module[module] for export in _type_exports(schema)
        ]
        lines.extend(["", f"from .{module} import ("])
        lines.extend(f"    {name} as {name}," for name in exports)
        lines.append(")")
    stubs[PACKAGE_STUB] = "\n".join(lines).rstrip() + "\n"
    return stubs


def generate(*, check: bool = False) -> None:
    outputs = {
        METADATA: render_metadata(),
        METADATA_HEADER: render_metadata_header(),
        PYTHON_ENUMS: render_python_enums(),
        PRESET_CONFIG: render_preset_config(),
        **render_type_stubs(),
    }
    stale = [
        path
        for path, value in outputs.items()
        if not path.exists() or path.read_text() != value
    ]
    if check and stale:
        raise SystemExit(
            "generated SPy metadata is stale: " + ", ".join(map(str, stale))
        )
    for path, value in outputs.items():
        path.write_text(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=args.check)


if __name__ == "__main__":
    main()
