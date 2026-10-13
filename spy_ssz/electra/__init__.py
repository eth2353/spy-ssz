"""Electra SSZ block, block-contents, and blinded-block types."""

from ..block import BlockProjection
from ..preset import Preset
from ..schema import get_schema, schema_for, schemas_for
from .._codecs import register_schema
from .._variants import export_preset_types
from ..ssz import SszObject
from ..schema import Fork, ObjectKind


_SIGNED_BLOCK = schema_for("electra_block")
SignedBeaconBlockElectra = type(
    _SIGNED_BLOCK.python_type,
    (SszObject,),
    {
        "expected_fork": _SIGNED_BLOCK.fork,
        "expected_kind": _SIGNED_BLOCK.kind,
        "json_input_envelope_key": "data",
        "json_output_envelope_key": None,
    },
)
export_preset_types(globals(), SignedBeaconBlockElectra, _SIGNED_BLOCK)
register_schema(_SIGNED_BLOCK)


_CONTENTS = get_schema(Fork.ELECTRA, ObjectKind.BEACON_BLOCK_CONTENTS)
_SIGNED_CONTENTS = get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS)
_BLINDED = get_schema(Fork.ELECTRA, ObjectKind.BLINDED_BEACON_BLOCK)
_SIGNED_BLINDED = get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BLINDED_BEACON_BLOCK)


class BeaconBlockContentsElectra(BlockProjection):
    expected_fork = _CONTENTS.fork
    expected_kind = _CONTENTS.kind
    signed_schema_id = _SIGNED_CONTENTS.schema_id


class SignedBeaconBlockContentsElectra(SszObject):
    expected_fork = _SIGNED_CONTENTS.fork
    expected_kind = _SIGNED_CONTENTS.kind
    json_input_envelope_key = "data"
    json_output_envelope_key = None


class BlindedBeaconBlockElectra(BlockProjection):
    expected_fork = _BLINDED.fork
    expected_kind = _BLINDED.kind
    signed_schema_id = _SIGNED_BLINDED.schema_id


class SignedBlindedBeaconBlockElectra(SszObject):
    expected_fork = _SIGNED_BLINDED.fork
    expected_kind = _SIGNED_BLINDED.kind
    json_input_envelope_key = "data"
    json_output_envelope_key = None


_BASES = (
    (BeaconBlockContentsElectra, _CONTENTS),
    (SignedBeaconBlockContentsElectra, _SIGNED_CONTENTS),
    (BlindedBeaconBlockElectra, _BLINDED),
    (SignedBlindedBeaconBlockElectra, _SIGNED_BLINDED),
)
for _base, _definition in _BASES:
    export_preset_types(globals(), _base, _definition, alias_mainnet=False)


_SIGNED_CONTENTS_BY_PRESET = {
    preset: globals()[f"SignedBeaconBlockContentsElectra{preset.name.title()}"]
    for preset in Preset
}
_SIGNED_BLINDED_BY_PRESET = {
    preset: globals()[f"SignedBlindedBeaconBlockElectra{preset.name.title()}"]
    for preset in Preset
}
BeaconBlockContentsElectra.signed_types_by_preset = _SIGNED_CONTENTS_BY_PRESET
BlindedBeaconBlockElectra.signed_types_by_preset = _SIGNED_BLINDED_BY_PRESET


for _definition in schemas_for("block_containers"):
    register_schema(_definition)
