"""Electra SSZ block, block-contents, and blinded-block types."""

from .. import _spy
from ..block import BlockProjection
from ..preset import Preset
from ..schema import get_schema, schema_for, schemas_for
from ..ssz import (
    Fork,
    ObjectKind,
    SszObject,
    bind_decoder,
    register_json_decoder,
    register_json_array_encoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)


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
for _preset_name in _SIGNED_BLOCK.presets:
    _preset = Preset[_preset_name.upper()]
    _name = f"{_SIGNED_BLOCK.python_type}{_preset.name.title()}"
    globals()[_name] = (
        SignedBeaconBlockElectra
        if _preset is Preset.MAINNET
        else type(_name, (SignedBeaconBlockElectra,), {"expected_preset": _preset})
    )

for _preset_name in _SIGNED_BLOCK.presets:
    _preset = Preset[_preset_name.upper()]
    register_json_decoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        bind_decoder(
            _spy.lib.spy_schema_block_decode_json_owned,
            _SIGNED_BLOCK.fork,
            _SIGNED_BLOCK.schema_id,
            _preset,
        ),
        _preset,
    )
    register_ssz_decoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        bind_decoder(
            _spy.lib.spy_schema_block_decode_ssz_owned,
            _SIGNED_BLOCK.fork,
            _SIGNED_BLOCK.schema_id,
            _preset,
        ),
        _preset,
    )
    register_ssz_encoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        _spy.lib.spy_schema_electra_ssz_size,
        _spy.lib.spy_schema_electra_encode_ssz,
        _preset,
    )
    register_json_encoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        _spy.lib.spy_schema_electra_json_size,
        _spy.lib.spy_schema_electra_encode_json,
        _preset,
    )


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


def _variant(name: str, base: type[SszObject], preset: Preset):
    return type(name, (base,), {"expected_preset": preset})


_BASES = (
    (BeaconBlockContentsElectra, _CONTENTS),
    (SignedBeaconBlockContentsElectra, _SIGNED_CONTENTS),
    (BlindedBeaconBlockElectra, _BLINDED),
    (SignedBlindedBeaconBlockElectra, _SIGNED_BLINDED),
)
for _base, _definition in _BASES:
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        _name = f"{_base.__name__}{_preset.name.title()}"
        globals()[_name] = _variant(_name, _base, _preset)


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
    _kind = _definition.kind
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        register_json_decoder(
            _definition.fork,
            _kind,
            bind_decoder(
                _spy.lib.spy_schema_block_containers_decode_json_owned,
                _definition.fork,
                _kind,
                _definition.schema_id,
                _preset,
            ),
            _preset,
        )
        register_ssz_decoder(
            _definition.fork,
            _kind,
            bind_decoder(
                _spy.lib.spy_schema_block_containers_decode_ssz_owned,
                _definition.fork,
                _kind,
                _definition.schema_id,
                _preset,
            ),
            _preset,
        )
        register_json_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_block_containers_json_size,
            _spy.lib.spy_schema_block_containers_encode_json,
            _preset,
        )
        register_json_array_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_block_containers_json_array_size,
            _spy.lib.spy_schema_block_containers_encode_json_array,
            _preset,
        )
        register_ssz_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_block_containers_ssz_size,
            _spy.lib.spy_schema_block_containers_encode_ssz,
            _preset,
        )
