"""Beacon API envelope policy around the native JSON representation.

Public classes retain their historical policy attributes. These transforms are
transport operations and do not own or inspect native graphs.
"""

from typing import Any

import msgspec


def json_input(policy: Any, source: bytes) -> bytes:
    envelope_key = policy.json_input_envelope_key
    if envelope_key is not None and not policy.json_decoder_handles_envelope:
        try:
            value = msgspec.json.decode(source)
        except msgspec.DecodeError:
            pass
        else:
            if isinstance(value, dict) and envelope_key in value:
                return msgspec.json.encode(value[envelope_key])
    return source


def json_output(policy: Any, encoded: bytes) -> bytes:
    envelope_key = policy.json_output_envelope_key
    metadata = policy.json_output_metadata
    if envelope_key is None or (
        policy.json_encoder_handles_envelope and metadata is None
    ):
        return encoded
    value = msgspec.json.decode(encoded)
    if not policy.json_encoder_handles_envelope:
        value = {envelope_key: value}
    if metadata is not None:
        value = {**metadata, **value}
    return msgspec.json.encode(value)
