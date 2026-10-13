"""First-class Fulu types backed by unchanged Electra wire codecs."""

from ..block import BlockProjection
from ..preset import Preset
from ..schema import Fork, ObjectKind, get_schema, schema_definitions
from .._codecs import register_schema
from .._variants import export_preset_types
from ..ssz import SszObject


_PROJECTION_KINDS = {
    ObjectKind.BEACON_BLOCK_CONTENTS,
    ObjectKind.BLINDED_BEACON_BLOCK,
}
_BARE_BLOCK_KINDS = {
    *_PROJECTION_KINDS,
    ObjectKind.SIGNED_BEACON_BLOCK,
    ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS,
    ObjectKind.SIGNED_BLINDED_BEACON_BLOCK,
}
_DEFINITIONS = {
    definition.kind: definition
    for definition in schema_definitions()
    if definition.fork is Fork.FULU
}

for _definition in _DEFINITIONS.values():
    _source_base = (
        BlockProjection if _definition.kind in _PROJECTION_KINDS else SszObject
    )
    _attributes = {
        "expected_fork": _definition.fork,
        "expected_kind": _definition.kind,
    }
    if _definition.codec == "fulu_signing":
        _attributes.update(
            json_input_envelope_key=None,
            json_output_envelope_key=None,
        )
    elif _definition.kind in _BARE_BLOCK_KINDS:
        _attributes.update(
            json_input_envelope_key="data",
            json_output_envelope_key=None,
        )
    _base = type(
        _definition.python_type,
        (_source_base,),
        _attributes,
    )
    export_preset_types(
        globals(),
        _base,
        _definition,
        alias_mainnet=_definition.codec != "fulu_block_containers",
    )

_FULU_CONTENTS = globals()["BeaconBlockContentsFulu"]
_FULU_CONTENTS.signed_schema_id = get_schema(
    Fork.FULU, ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS
).schema_id
_FULU_CONTENTS.signed_types_by_preset = {
    preset: globals()[f"SignedBeaconBlockContentsFulu{preset.name.title()}"]
    for preset in Preset
}
_FULU_BLINDED = globals()["BlindedBeaconBlockFulu"]
_FULU_BLINDED.signed_schema_id = get_schema(
    Fork.FULU, ObjectKind.SIGNED_BLINDED_BEACON_BLOCK
).schema_id
_FULU_BLINDED.signed_types_by_preset = {
    preset: globals()[f"SignedBlindedBeaconBlockFulu{preset.name.title()}"]
    for preset in Preset
}


for _definition in _DEFINITIONS.values():
    register_schema(_definition)
