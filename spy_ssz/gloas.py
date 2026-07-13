"""Gloas SSZ types."""

from . import _spy
from .ssz import SszObject, register_json_decoder, register_ssz_decoder
from .preset import Preset
from .schema import schemas_for


_DEFINITION = schemas_for("gloas_attestation")[0]
GloasAttestation = type(
    _DEFINITION.python_type,
    (SszObject,),
    {"expected_fork": _DEFINITION.fork, "expected_kind": _DEFINITION.kind},
)
for _preset_name in _DEFINITION.presets:
    _preset = Preset[_preset_name.upper()]
    globals()[f"{_DEFINITION.python_type}{_preset.name.title()}"] = GloasAttestation
register_json_decoder(
    _DEFINITION.fork,
    _DEFINITION.kind,
    _spy.lib.spy_schema_gloas_decode_attestation_owned,
)
register_ssz_decoder(
    _DEFINITION.fork,
    _DEFINITION.kind,
    _spy.lib.spy_schema_gloas_decode_attestation_ssz_owned,
)
