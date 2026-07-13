"""Immutable Electra signing types used by validator clients."""

from . import _spy
from .ssz import (
    SszObject,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)
from .preset import Preset
from .schema import schemas_for


_SCHEMAS = {value.kind: value for value in schemas_for("signing")}
for _definition in _SCHEMAS.values():
    _base = type(
        _definition.python_type,
        (SszObject,),
        {
            "expected_fork": _definition.fork,
            "expected_kind": _definition.kind,
            "json_input_envelope_key": None,
            "json_output_envelope_key": None,
        },
    )
    globals()[_definition.python_type] = _base
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        _name = f"{_definition.python_type}{_preset.name.title()}"
        globals()[_name] = (
            _base
            if _preset is Preset.MAINNET
            else type(_name, (_base,), {"expected_preset": _preset})
        )


for _kind, _definition in _SCHEMAS.items():
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        register_json_decoder(
            _definition.fork,
            _kind,
            lambda source, kind=_kind, schema=_definition.schema_id, preset=_preset: (
                _spy.lib.spy_schema_signing_decode_json_owned(
                    source, kind, schema, preset
                )
            ),
            _preset,
        )
        register_ssz_decoder(
            _definition.fork,
            _kind,
            lambda source, kind=_kind, schema=_definition.schema_id, preset=_preset: (
                _spy.lib.spy_schema_signing_decode_ssz_owned(
                    source, kind, schema, preset
                )
            ),
            _preset,
        )
        register_json_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_signing_json_size,
            _spy.lib.spy_schema_signing_encode_json,
            _preset,
        )
        register_ssz_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_signing_ssz_size,
            _spy.lib.spy_schema_signing_encode_ssz,
            _preset,
        )
