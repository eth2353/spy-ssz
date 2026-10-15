"""Native buffer validation and decode allocation; no public type imports."""

from __future__ import annotations

from collections.abc import Buffer
from enum import IntEnum
from typing import Any

import msgspec

from . import _spy
from ._codecs import Decoder


def _spy_bytes(buffer: bytes | bytearray) -> tuple[Any, Any]:
    view = _spy.ffi.from_buffer(buffer)
    value = _spy.ffi.new("spy_BytesObject *")
    value.length = len(buffer)
    value.hash = 0
    value.data.p = _spy.ffi.cast("uint8_t *", view)
    return value, view


class _DecodeStatus(IntEnum):
    UNRECOGNIZED_FIELD = _spy.lib.SPY_SSZ_DECODE_UNRECOGNIZED_FIELD
    MALFORMED_INPUT = _spy.lib.SPY_SSZ_DECODE_MALFORMED_INPUT
    VALID = _spy.lib.SPY_SSZ_DECODE_VALID


# The largest decoder arena is ``input_length * 3 + 16 KiB`` and all native
# lengths and offsets are signed 32-bit integers.
_MAX_NATIVE_SIZE = (1 << 31) - 1
_MAX_NATIVE_INPUT_LENGTH = (_MAX_NATIVE_SIZE - 16 * 1024) // 3


def input_bytes(data: Buffer, encoding: str, limit: int) -> bytes:
    # Validate before copying or parsing a Python-managed JSON envelope.
    if type(data) is bytes:
        if len(data) > limit:
            raise ValueError(
                f"{encoding} input exceeds the {limit}-byte implementation limit"
            )
        return data
    try:
        view = memoryview(data)
    except TypeError:
        raise TypeError(f"{encoding} input must support the buffer protocol") from None
    with view:
        # nbytes counts bytes even for typed or multidimensional buffers.
        if view.nbytes > limit:
            raise ValueError(
                f"{encoding} input exceeds the {limit}-byte implementation limit"
            )
        return view.tobytes()


def decode_owned(source: bytes, decoder: Decoder, encoding: str) -> Any:
    source_obj, source_view = _spy_bytes(source)
    handle = decoder(source_obj)
    assert source_view
    raw_status = (
        int(_spy.lib.spy_ssz_object_decode_status(handle))
        if handle.p
        else int(_DecodeStatus.MALFORMED_INPUT)
    )
    if raw_status != _DecodeStatus.VALID:
        error_start = _spy.lib.spy_ssz_object_error_start(handle)
        error_end = _spy.lib.spy_ssz_object_error_end(handle)
        if handle.p:
            _spy.lib.spy_ssz_object_destroy(handle)
        try:
            status = _DecodeStatus(raw_status)
        except ValueError:
            raise ValueError(f"unknown native decode status {raw_status}") from None
        if (
            encoding == "JSON"
            and status is _DecodeStatus.UNRECOGNIZED_FIELD
            and 1 <= error_start <= error_end < len(source)
        ):
            field = msgspec.json.decode(source[error_start - 1 : error_end + 1])
            raise ValueError(
                f"unrecognized JSON object field {field!r} "
                f"(status={status.name}, "
                f"byte_range={error_start}:{error_end + 1})"
            )
        detail = f"status={status.name}"
        if 0 <= error_start <= error_end < len(source):
            detail += f", byte_range={error_start}:{error_end + 1}"
        raise ValueError(f"invalid {encoding} object ({detail})")
    return handle
