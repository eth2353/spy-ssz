"""Deneb SSZ types."""

from __future__ import annotations

from . import _spy
from .ssz import SszObject, register_json_decoder, register_ssz_decoder
from .preset import Preset
from .schema import schemas_for


_CODECS = {
    "deneb_block": (
        _spy.lib.spy_schema_deneb_decode_owned,
        _spy.lib.spy_schema_deneb_decode_ssz_owned,
    ),
    "deneb_attestation": (
        _spy.lib.spy_schema_deneb_decode_attestation_owned,
        _spy.lib.spy_schema_deneb_decode_attestation_ssz_owned,
    ),
}
for _definition in (*schemas_for("deneb_block"), *schemas_for("deneb_attestation")):
    _type = type(
        _definition.python_type,
        (SszObject,),
        {"expected_fork": _definition.fork, "expected_kind": _definition.kind},
    )
    globals()[_definition.python_type] = _type
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        globals()[f"{_definition.python_type}{_preset.name.title()}"] = _type
    _json_decoder, _ssz_decoder = _CODECS[_definition.codec]
    register_json_decoder(_definition.fork, _definition.kind, _json_decoder)
    register_ssz_decoder(_definition.fork, _definition.kind, _ssz_decoder)
