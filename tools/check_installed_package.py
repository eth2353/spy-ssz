"""Smoke-test an installed wheel with `python -I tools/check_installed_package.py`.

Isolated mode keeps the source checkout off sys.path so missing wheel modules,
resources, and native symbols cannot be hidden by a local development build.
"""

from importlib.resources import files

import spy_ssz
from spy_ssz import (
    Fork,
    ObjectKind,
    Preset,
    encode_json_array,
    get_ssz_type,
    load_preset,
)
from spy_ssz.schema import schema_definitions


def main() -> None:
    for name in vars(spy_ssz)["__all__"]:
        getattr(spy_ssz, name)
    package = files("spy_ssz")
    for resource in (
        "py.typed",
        "__init__.pyi",
        "schemas.yaml",
        "consensus_types.json",
    ):
        assert package.joinpath(resource).is_file(), resource
    for definition in schema_definitions():
        for preset_name in definition.presets:
            concrete = get_ssz_type(
                definition.fork, definition.kind, Preset[preset_name.upper()]
            )
            assert concrete.expected_fork is definition.fork
            assert concrete.expected_kind is definition.kind
    for preset in Preset:
        assert load_preset(preset).sync_committee_size > 0
        for fork in (Fork.ELECTRA, Fork.FULU, Fork.GLOAS):
            concrete = get_ssz_type(fork, ObjectKind.ATTESTATION_DATA, preset)
            with concrete.from_ssz(bytes(128)) as value:
                encoded = value.to_json()
                assert (
                    encode_json_array([value, value])
                    == b"[" + encoded + b"," + encoded + b"]"
                )
                with concrete.from_json(encoded) as decoded:
                    assert decoded.to_ssz() == bytes(128)
                    assert decoded.hash_tree_root() == value.hash_tree_root()
    print(f"Installed package checks passed: {spy_ssz.__file__}")


if __name__ == "__main__":
    main()
