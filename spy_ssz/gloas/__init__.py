"""First-class Gloas validator-client containers and beacon blocks."""

from .. import _spy
from ..block import BlockProjection, signature_bytes
from ..preset import Preset
from ..schema import Fork, ObjectKind, get_schema, schema_definitions
from ..ssz import (
    SszObject,
    _spy_bytes,
    bind_decoder,
    register_json_array_encoder,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)

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
    globals()[_definition.python_type] = _base
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        _name = f"{_definition.python_type}{_preset.name.title()}"
        globals()[_name] = (
            _base
            if _preset is Preset.MAINNET
            else type(_name, (_base,), {"expected_preset": _preset})
        )


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
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        if _definition.codec == "gloas_block":
            _json_decoder = bind_decoder(
                _spy.lib.spy_schema_gloas_block_decode_json_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _ssz_decoder = bind_decoder(
                _spy.lib.spy_schema_gloas_block_decode_ssz_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _json_sizer = _spy.lib.spy_schema_gloas_json_size
            _json_encoder = _spy.lib.spy_schema_gloas_encode_json
            _ssz_sizer = _spy.lib.spy_schema_gloas_ssz_size
            _ssz_encoder = _spy.lib.spy_schema_gloas_encode_ssz
        elif _definition.codec == "gloas_payload_envelope":
            _json_decoder = bind_decoder(
                _spy.lib.spy_schema_gloas_payload_envelope_decode_json_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _ssz_decoder = bind_decoder(
                _spy.lib.spy_schema_gloas_payload_envelope_decode_ssz_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _json_sizer = _spy.lib.spy_schema_gloas_payload_envelope_json_size
            _json_encoder = _spy.lib.spy_schema_gloas_payload_envelope_encode_json
            _ssz_sizer = _spy.lib.spy_schema_gloas_payload_envelope_ssz_size
            _ssz_encoder = _spy.lib.spy_schema_gloas_payload_envelope_encode_ssz
        else:
            _json_decoder = bind_decoder(
                _spy.lib.spy_schema_gloas_signing_decode_json_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _ssz_decoder = bind_decoder(
                _spy.lib.spy_schema_gloas_signing_decode_ssz_owned,
                _definition.fork,
                _definition.kind,
                _definition.schema_id,
                _preset,
            )
            _json_sizer = _spy.lib.spy_schema_signing_json_size
            _json_encoder = _spy.lib.spy_schema_signing_encode_json
            _ssz_sizer = _spy.lib.spy_schema_signing_ssz_size
            _ssz_encoder = _spy.lib.spy_schema_signing_encode_ssz

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
        if _definition.codec == "gloas_signing":
            register_json_array_encoder(
                _definition.fork,
                _definition.kind,
                _spy.lib.spy_schema_signing_json_array_size,
                _spy.lib.spy_schema_signing_encode_json_array,
                _preset,
            )
        register_ssz_encoder(
            _definition.fork,
            _definition.kind,
            _ssz_sizer,
            _ssz_encoder,
            _preset,
        )
