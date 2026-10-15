"""Immutable Electra signing types used by validator clients."""

from ._variants import export_preset_types
from .schema import schemas_for
from .ssz import SszObject

_SCHEMAS = {value.kind: value for value in schemas_for("signing")}
for _definition in _SCHEMAS.values():
    _base = type(
        _definition.python_type,
        (SszObject,),
        {
            "__slots__": (),
            "expected_fork": _definition.fork,
            "expected_kind": _definition.kind,
            "json_input_envelope_key": None,
            "json_output_envelope_key": None,
        },
    )
    export_preset_types(globals(), _base, _definition)
