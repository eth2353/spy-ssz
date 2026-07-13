"""Generate SPy constants from authoritative schema and preset YAML files."""

from __future__ import annotations

import argparse
import json
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
CONSENSUS_TYPES = ROOT / "spy_ssz" / "consensus_types.json"
PROJECTIONS = ROOT / "spy_ssz" / "projections.py"
PROJECTIONS_STUB = ROOT / "spy_ssz" / "projections.pyi"


_CONTAINER_KINDS = {"container", "progressive_container"}
_SEQUENCE_KINDS = {"list", "vector", "progressive_list"}
_BYTE_KINDS = {
    "byte_list",
    "byte_vector",
    "bitlist",
    "bitvector",
    "progressive_byte_list",
    "progressive_bitlist",
}


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def _consensus_catalog() -> dict[str, Any]:
    value = json.loads(CONSENSUS_TYPES.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{CONSENSUS_TYPES} must contain a mapping")
    return value


def _type_references(shape: dict[str, Any]) -> list[int]:
    kind = shape["kind"]
    if kind in _CONTAINER_KINDS:
        return [type_id for _, type_id in shape["fields"]]
    if kind in _SEQUENCE_KINDS:
        return [shape["element"]]
    if kind in {"union", "compatible_union"}:
        return [type_id for type_id in shape["options"] if type_id >= 0]
    return []


def _type_fingerprint(
    fork_data: dict[str, Any], type_id: int, cache: dict[int, Any]
) -> Any:
    cached = cache.get(type_id)
    if cached is not None:
        return cached
    shape = fork_data["types"][type_id]
    kind = shape["kind"]
    value: Any
    if kind in _CONTAINER_KINDS:
        value = (
            kind,
            tuple(
                (name, _type_fingerprint(fork_data, child, cache))
                for name, child in shape["fields"]
            ),
        )
    elif kind in _SEQUENCE_KINDS:
        value = (
            kind,
            shape.get("length"),
            shape.get("limit"),
            _type_fingerprint(fork_data, shape["element"], cache),
        )
    elif kind in {"union", "compatible_union"}:
        value = (
            kind,
            tuple(
                None if child < 0 else _type_fingerprint(fork_data, child, cache)
                for child in shape["options"]
            ),
        )
    else:
        value = (
            kind,
            shape.get("byte_length"),
            shape.get("length"),
            shape.get("limit"),
        )
    cache[type_id] = value
    return value


def _projection_model(
    schemas: list[dict[str, Any]], catalog: dict[str, Any]
) -> tuple[
    dict[tuple[str, int], str],
    dict[tuple[str, int], dict[str, Any]],
]:
    reachable: dict[tuple[str, int], dict[str, Any]] = {}
    names: dict[tuple[str, int], str] = {}
    for schema in schemas:
        consensus_type = schema.get("consensus_type")
        fork = schema["fork"].lower()
        fork_data = catalog["forks"].get(fork)
        if consensus_type is None or fork_data is None:
            continue
        reverse_names = {type_id: name for name, type_id in fork_data["names"].items()}
        pending = [fork_data["names"][consensus_type]]
        visited: set[int] = set()
        while pending:
            type_id = pending.pop()
            if type_id in visited:
                continue
            visited.add(type_id)
            shape = fork_data["types"][type_id]
            pending.extend(_type_references(shape))
            if shape["kind"] in _CONTAINER_KINDS:
                key = (fork, type_id)
                reachable[key] = shape
                names[key] = reverse_names.get(
                    type_id, f"{fork.title()}Type{type_id}Projection"
                )

    grouped: dict[str, list[tuple[str, int]]] = {}
    for key, name in names.items():
        grouped.setdefault(name, []).append(key)
    class_names: dict[tuple[str, int], str] = {}
    for name, keys in grouped.items():
        fingerprints = {
            _type_fingerprint(catalog["forks"][fork], type_id, {})
            for fork, type_id in keys
        }
        if len(fingerprints) == 1:
            class_names.update((key, name) for key in keys)
        else:
            class_names.update((key, f"{key[0].title()}{name}") for key in keys)
    return class_names, reachable


def _python_annotation(
    catalog: dict[str, Any],
    class_names: dict[tuple[str, int], str],
    fork: str,
    type_id: int,
    *,
    qualified: bool,
) -> str:
    shape = catalog["forks"][fork]["types"][type_id]
    kind = shape["kind"]
    if kind == "boolean":
        return "bool"
    if kind == "uint":
        return "int"
    if kind in _BYTE_KINDS:
        return "bytes"
    if kind in _CONTAINER_KINDS:
        name = class_names[(fork, type_id)]
        return f"projections.{name}" if qualified else name
    if kind in _SEQUENCE_KINDS:
        element = _python_annotation(
            catalog,
            class_names,
            fork,
            shape["element"],
            qualified=qualified,
        )
        return f"tuple[{element}, ...]"
    return "Any"


def _render_projection_base() -> list[str]:
    return [
        "class Projection:",
        "    def to_obj(self) -> dict[str, Any]:",
        "        return {",
        "            field.name: _json_value(getattr(self, field.name)) for field in fields(self)",
        "        }",
        "",
        "",
        "def _json_value(value: Any) -> Any:",
        "    if isinstance(value, Projection):",
        "        return value.to_obj()",
        "    if isinstance(value, bool):",
        "        return value",
        "    if isinstance(value, int):",
        "        return value",
        "    if isinstance(value, bytes):",
        '        return f"0x{value.hex()}"',
        "    if isinstance(value, tuple):",
        "        return [_json_value(item) for item in value]",
        "    return value",
        "",
        "",
        "def _hex_bytes(value: Any) -> bytes:",
        '    if not isinstance(value, str) or not value.startswith("0x"):',
        '        raise TypeError("expected 0x-prefixed hex string")',
        "    return bytes.fromhex(value[2:])",
    ]


def render_projections(
    schemas: list[dict[str, Any]], catalog: dict[str, Any]
) -> tuple[str, str]:
    class_names, reachable = _projection_model(schemas, catalog)
    definitions: dict[str, tuple[str, int, dict[str, Any]]] = {}
    for key, shape in reachable.items():
        definitions.setdefault(class_names[key], (*key, shape))

    runtime = [
        '"""Generated immutable projections from consensus_types.json; do not edit."""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass, fields",
        "from typing import Any",
        "",
        "from .consensus_types import get_type_definition, get_type_shape",
        "from ._schema_enums import Fork",
        "",
        "",
        "_BYTE_KINDS = {",
        '    "bitlist",',
        '    "bitvector",',
        '    "byte_list",',
        '    "byte_vector",',
        '    "progressive_bitlist",',
        '    "progressive_byte_list",',
        "}",
        '_CONTAINER_KINDS = {"container", "progressive_container"}',
        '_SEQUENCE_KINDS = {"list", "progressive_list", "vector"}',
        "",
        "",
        *_render_projection_base(),
    ]
    stub = [
        '"""Generated immutable projections from consensus_types.json; do not edit."""',
        "",
        "from typing import Any",
        "",
        "from ._schema_enums import Fork",
        "",
        "class Projection:",
        "    def to_obj(self) -> dict[str, Any]: ...",
        "",
        "def project_value(fork: Fork, type_id: int, value: Any) -> Any: ...",
        "def project_field(fork: Fork, consensus_type: str, name: str, value: Any) -> Any: ...",
    ]
    for name in sorted(definitions):
        fork, _, shape = definitions[name]
        projection_fields = [
            (
                field_name,
                _python_annotation(
                    catalog,
                    class_names,
                    fork,
                    field_type,
                    qualified=False,
                ),
            )
            for field_name, field_type in shape["fields"]
        ]
        runtime.extend(
            [
                "",
                "",
                "@dataclass(frozen=True, slots=True)",
                f"class {name}(Projection):",
            ]
        )
        stub.extend(["", f"class {name}(Projection):"])
        if projection_fields:
            stub.extend(["    def __init__(", "        self,"])
            stub.extend(
                f"        {field_name}: {annotation},"
                for field_name, annotation in projection_fields
            )
            stub.append("    ) -> None: ...")
        else:
            stub.append("    def __init__(self) -> None: ...")
        for field_name, annotation in projection_fields:
            runtime.append(f"    {field_name}: {annotation}")
            stub.extend(
                [
                    "    @property",
                    f"    def {field_name}(self) -> {annotation}: ...",
                ]
            )
        if not projection_fields:
            runtime.append("    pass")

    runtime.extend(["", "", "_PROJECTION_TYPES = {"])
    for (fork, type_id), name in sorted(class_names.items()):
        runtime.append(f"    (Fork.{fork.upper()}, {type_id}): {name},")
    runtime.extend(
        [
            "}",
            "",
            "",
            "def project_value(fork: Fork, type_id: int, value: Any) -> Any:",
            "    shape = get_type_shape(fork, type_id)",
            '    kind = shape["kind"]',
            '    if kind == "boolean":',
            "        return bool(value)",
            '    if kind == "uint":',
            "        return int(value)",
            "    if kind in _BYTE_KINDS:",
            "        return _hex_bytes(value)",
            "    if kind in _CONTAINER_KINDS:",
            "        projection = _PROJECTION_TYPES[(fork, type_id)]",
            "        return projection(",
            "            **{",
            "                name: project_value(fork, child, value[name])",
            '                for name, child in shape["fields"]',
            "            }",
            "        )",
            "    if kind in _SEQUENCE_KINDS:",
            '        return tuple(project_value(fork, shape["element"], item) for item in value)',
            "    return value",
            "",
            "",
            "def project_field(fork: Fork, consensus_type: str, name: str, value: Any) -> Any:",
            "    definition = get_type_definition(fork, consensus_type)",
            '    fields_by_name = dict(definition.descriptor["fields"])',
            "    return project_value(fork, fields_by_name[name], value)",
        ]
    )
    return "\n".join(runtime).rstrip() + "\n", "\n".join(stub).rstrip() + "\n"


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


def _schema_properties(
    schema: dict[str, Any],
    catalog: dict[str, Any],
    class_names: dict[tuple[str, int], str],
) -> list[tuple[str, str]]:
    consensus_type = schema.get("consensus_type")
    fork = schema["fork"].lower()
    fork_data = catalog["forks"].get(fork)
    if consensus_type is None or fork_data is None:
        return []
    root = fork_data["names"][consensus_type]
    shape = fork_data["types"][root]
    return [
        (
            name,
            "Bitfield"
            if name in {"aggregation_bits", "committee_bits"}
            else _python_annotation(
                catalog,
                class_names,
                fork,
                type_id,
                qualified=True,
            ),
        )
        for name, type_id in shape["fields"]
    ]


def _stub_class(name: str, base: str, properties: list[tuple[str, str]]) -> list[str]:
    if not properties:
        return [f"class {name}({base}): ..."]
    lines = [f"class {name}({base}):"]
    for property_name, annotation in properties:
        lines.extend(
            [
                "    @property",
                f"    def {property_name}(self) -> {annotation}: ...",
            ]
        )
    return lines


def _render_dynamic_stub(
    schemas: list[dict[str, Any]],
    catalog: dict[str, Any],
    class_names: dict[tuple[str, int], str],
    *,
    alias_all: bool = False,
) -> str:
    properties_by_type = {
        schema["python_type"]: _schema_properties(schema, catalog, class_names)
        for schema in schemas
    }
    annotations = {
        annotation
        for properties in properties_by_type.values()
        for _, annotation in properties
    }
    lines = [
        '"""Generated from spy_ssz/schemas.yaml; do not edit."""',
        "",
    ]
    if any(annotation.startswith("projections.") for annotation in annotations):
        lines.extend(["from . import projections"])
    if "Bitfield" in annotations:
        lines.extend(["from .ssz import Bitfield, SszObject"])
    else:
        lines.extend(["from .ssz import SszObject"])
    lines.append("")
    for schema_index, schema in enumerate(schemas):
        base = schema["python_type"]
        properties = properties_by_type[base]
        lines.extend([*_stub_class(base, "SszObject", properties), ""])
        for index, preset in enumerate(schema["presets"]):
            variant = f"{base}{preset.title()}"
            if alias_all or preset == "mainnet":
                lines.append(f"{variant} = {base}")
                if index + 1 < len(schema["presets"]):
                    lines.append("")
            else:
                lines.append(f"class {variant}({base}): ...")
        if schema_index + 1 < len(schemas):
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
    catalog = _consensus_catalog()
    class_names, _ = _projection_model(schemas, catalog)
    projections, projections_stub = render_projections(schemas, catalog)
    by_module: dict[str, list[dict[str, Any]]] = {}
    for schema in schemas:
        module = source["codecs"][schema["codec"]]
        by_module.setdefault(module, []).append(schema)

    stubs = {
        TYPE_STUBS["blocks"]: _render_blocks_stub(by_module["blocks"]),
        TYPE_STUBS["deneb"]: _render_dynamic_stub(
            by_module["deneb"], catalog, class_names, alias_all=True
        ),
        TYPE_STUBS["electra"]: _render_dynamic_stub(
            by_module["electra"], catalog, class_names
        ),
        TYPE_STUBS["fulu"]: _render_dynamic_stub(
            by_module["fulu"], catalog, class_names
        ),
        TYPE_STUBS["gloas"]: _render_dynamic_stub(
            by_module["gloas"], catalog, class_names, alias_all=True
        ),
        TYPE_STUBS["signing"]: _render_dynamic_stub(
            by_module["signing"], catalog, class_names
        ),
        PROJECTIONS: projections,
        PROJECTIONS_STUB: projections_stub,
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
        "from .projections import Checkpoint as Checkpoint",
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
