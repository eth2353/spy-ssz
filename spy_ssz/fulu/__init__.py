"""First-class Fulu types backed by unchanged Electra wire codecs."""

from .. import _spy
from ..electra import _BlockProjection
from ..preset import Preset
from ..schema import Fork, ObjectKind, get_schema, schema_definitions
from ..ssz import (
    SszObject,
    bind_decoder,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)


_PROJECTION_KINDS = {
    ObjectKind.BEACON_BLOCK_CONTENTS,
    ObjectKind.BLINDED_BEACON_BLOCK,
}
_BARE_BLOCK_KINDS = {
    *_PROJECTION_KINDS,
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
        _BlockProjection if _definition.kind in _PROJECTION_KINDS else SszObject
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
    globals()[_definition.python_type] = _base
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        _name = f"{_definition.python_type}{_preset.name.title()}"
        globals()[_name] = (
            type(_name, (_base,), {"expected_preset": _preset})
            if _definition.codec == "fulu_block_containers"
            else _base
            if _preset is Preset.MAINNET
            else type(_name, (_base,), {"expected_preset": _preset})
        )


_FULU_CONTENTS = globals()["FuluBeaconBlockContents"]
_FULU_CONTENTS.signed_schema_id = get_schema(
    Fork.FULU, ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS
).schema_id
_FULU_CONTENTS.signed_types_by_preset = {
    preset: globals()[f"FuluSignedBeaconBlockContents{preset.name.title()}"]
    for preset in Preset
}
_FULU_BLINDED = globals()["FuluBlindedBeaconBlock"]
_FULU_BLINDED.signed_schema_id = get_schema(
    Fork.FULU, ObjectKind.SIGNED_BLINDED_BEACON_BLOCK
).schema_id
_FULU_BLINDED.signed_types_by_preset = {
    preset: globals()[f"FuluSignedBlindedBeaconBlock{preset.name.title()}"]
    for preset in Preset
}


for _definition in _DEFINITIONS.values():
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        if _definition.codec == "fulu_block":
            _json_decoder = bind_decoder(
                _spy.lib.spy_schema_block_decode_json_owned,
                _definition.fork,
                _definition.schema_id,
                _preset,
            )
            _ssz_decoder = bind_decoder(
                _spy.lib.spy_schema_block_decode_ssz_owned,
                _definition.fork,
                _definition.schema_id,
                _preset,
            )
            _json_sizer = _spy.lib.spy_schema_electra_json_size
            _json_encoder = _spy.lib.spy_schema_electra_encode_json
            _ssz_sizer = _spy.lib.spy_schema_electra_ssz_size
            _ssz_encoder = _spy.lib.spy_schema_electra_encode_ssz
        elif _definition.codec == "fulu_signing":
            _json_decoder = bind_decoder(
                _spy.lib.spy_schema_signing_decode_json_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _ssz_decoder = bind_decoder(
                _spy.lib.spy_schema_signing_decode_ssz_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _json_sizer = _spy.lib.spy_schema_signing_json_size
            _json_encoder = _spy.lib.spy_schema_signing_encode_json
            _ssz_sizer = _spy.lib.spy_schema_signing_ssz_size
            _ssz_encoder = _spy.lib.spy_schema_signing_encode_ssz
        else:
            _json_decoder = bind_decoder(
                _spy.lib.spy_schema_block_containers_decode_json_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _ssz_decoder = bind_decoder(
                _spy.lib.spy_schema_block_containers_decode_ssz_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _json_sizer = _spy.lib.spy_schema_block_containers_json_size
            _json_encoder = _spy.lib.spy_schema_block_containers_encode_json
            _ssz_sizer = _spy.lib.spy_schema_block_containers_ssz_size
            _ssz_encoder = _spy.lib.spy_schema_block_containers_encode_ssz

        register_json_decoder(
            _definition.fork, _definition.kind, _json_decoder, _preset
        )
        register_ssz_decoder(_definition.fork, _definition.kind, _ssz_decoder, _preset)
        register_json_encoder(
            _definition.fork,
            _definition.kind,
            _json_sizer,
            _json_encoder,
            _preset,
        )
        register_ssz_encoder(
            _definition.fork,
            _definition.kind,
            _ssz_sizer,
            _ssz_encoder,
            _preset,
        )
