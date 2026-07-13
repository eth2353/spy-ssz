"""Fulu SSZ block types, reusing the Electra block schema."""

from . import _spy
from .ssz import (
    SszObject,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)
from .preset import Preset
from .schema import schema_for


_DEFINITION = schema_for("fulu_block")
FuluSignedBeaconBlock = type(
    _DEFINITION.python_type,
    (SszObject,),
    {"expected_fork": _DEFINITION.fork, "expected_kind": _DEFINITION.kind},
)
for _preset_name in _DEFINITION.presets:
    _preset = Preset[_preset_name.upper()]
    _name = f"{_DEFINITION.python_type}{_preset.name.title()}"
    globals()[_name] = (
        FuluSignedBeaconBlock
        if _preset is Preset.MAINNET
        else type(_name, (FuluSignedBeaconBlock,), {"expected_preset": _preset})
    )

for _preset_name in _DEFINITION.presets:
    _preset = Preset[_preset_name.upper()]
    register_json_decoder(
        _DEFINITION.fork,
        _DEFINITION.kind,
        lambda source, preset=_preset: _spy.lib.spy_schema_fulu_decode_preset_owned(
            source, preset
        ),
        _preset,
    )
    register_ssz_decoder(
        _DEFINITION.fork,
        _DEFINITION.kind,
        lambda source, preset=_preset: _spy.lib.spy_schema_fulu_decode_ssz_preset_owned(
            source, preset
        ),
        _preset,
    )
    register_ssz_encoder(
        _DEFINITION.fork,
        _DEFINITION.kind,
        _spy.lib.spy_schema_electra_ssz_size,
        _spy.lib.spy_schema_electra_encode_ssz,
        _preset,
    )
    register_json_encoder(
        _DEFINITION.fork,
        _DEFINITION.kind,
        _spy.lib.spy_schema_electra_json_size,
        _spy.lib.spy_schema_electra_encode_json,
        _preset,
    )
