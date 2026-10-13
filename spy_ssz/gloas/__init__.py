"""First-class Gloas validator-client containers and beacon blocks."""

from .. import _spy
from ..block import BlockProjection, signature_bytes
from ..preset import Preset
from ..schema import Fork, ObjectKind, get_schema, schema_definitions
from .._codecs import register_schema
from .._variants import export_preset_types
from ..ssz import SszObject, _spy_bytes

_DEFINITIONS = {
    definition.kind: definition
    for definition in schema_definitions()
    if definition.fork is Fork.GLOAS
}

for _definition in _DEFINITIONS.values():
    _source_base = (
        BlockProjection if _definition.kind is ObjectKind.BEACON_BLOCK else SszObject
    )
    _attributes = {
        "expected_fork": _definition.fork,
        "expected_kind": _definition.kind,
    }
    if _definition.codec == "gloas_signing":
        _attributes.update(
            json_input_envelope_key=None,
            json_output_envelope_key=None,
        )
        if _definition.kind is ObjectKind.PAYLOAD_ATTESTATION_DATA:
            _attributes.update(
                json_input_envelope_key="data",
                json_output_envelope_key="data",
                json_decoder_handles_envelope=False,
                json_encoder_handles_envelope=False,
                json_output_metadata={"version": "gloas"},
            )
    elif _definition.kind is ObjectKind.BEACON_BLOCK:
        _attributes.update(json_output_envelope_key="data")
    elif _definition.kind is ObjectKind.EXECUTION_PAYLOAD_ENVELOPE:
        _attributes.update(json_output_metadata={"version": "gloas"})
    elif _definition.kind in {
        ObjectKind.SIGNED_BEACON_BLOCK,
        ObjectKind.SIGNED_EXECUTION_PAYLOAD_ENVELOPE,
    }:
        _attributes.update(
            json_input_envelope_key="data",
            json_output_envelope_key=None,
        )
    _base = type(_definition.python_type, (_source_base,), _attributes)
    export_preset_types(globals(), _base, _definition)

_BEACON_BLOCK = globals()["BeaconBlockGloas"]
_BEACON_BLOCK.signed_schema_id = get_schema(
    Fork.GLOAS, ObjectKind.SIGNED_BEACON_BLOCK
).schema_id
_BEACON_BLOCK.signed_types_by_preset = {
    preset: globals()[f"SignedBeaconBlockGloas{preset.name.title()}"]
    for preset in Preset
}


def _sign_execution_payload_envelope(
    self: SszObject, signature: str | bytes
) -> SszObject:
    signed_type = _SIGNED_ENVELOPE_TYPES[self.expected_preset]
    signature_obj, signature_view = _spy_bytes(signature_bytes(signature))
    with self._use_handle() as source_handle:
        handle = _spy.lib.spy_ssz_object_clone_and_sign_block(
            source_handle,
            signature_obj,
            signed_type.expected_kind,
            _SIGNED_ENVELOPE.schema_id,
            False,
        )
    assert signature_view
    if not handle.p or not _spy.lib.spy_ssz_object_is_valid(handle):
        if handle.p:
            _spy.lib.spy_ssz_object_destroy(handle)
        raise ValueError("SPy execution payload envelope signing failed")
    return signed_type(handle)


_ENVELOPE = get_schema(Fork.GLOAS, ObjectKind.EXECUTION_PAYLOAD_ENVELOPE)
_SIGNED_ENVELOPE = get_schema(Fork.GLOAS, ObjectKind.SIGNED_EXECUTION_PAYLOAD_ENVELOPE)
_SIGNED_ENVELOPE_TYPES = {
    preset: globals()[f"SignedExecutionPayloadEnvelopeGloas{preset.name.title()}"]
    for preset in Preset
}
for _preset in Preset:
    globals()[
        f"ExecutionPayloadEnvelopeGloas{_preset.name.title()}"
    ].sign = _sign_execution_payload_envelope


for _definition in _DEFINITIONS.values():
    register_schema(_definition)
