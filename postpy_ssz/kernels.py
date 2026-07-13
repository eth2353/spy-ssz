from __future__ import annotations

from hashlib import sha256
from threading import local
from typing import Any

try:
    from . import _native
except ImportError as exc:  # pragma: no cover - exercised before building
    raise ImportError(
        "SPy kernels are not built; run `python tools/build_native.py --spy-root PATH`"
    ) from exc


_workspace = local()


def _buffers() -> tuple[bytearray, bytearray]:
    try:
        return _workspace.state, _workspace.schedule
    except AttributeError:
        _workspace.state = bytearray(32)
        _workspace.schedule = bytearray(256)
        return _workspace.state, _workspace.schedule


def _spy_bytes(buffer: bytes | bytearray) -> tuple[Any, Any]:
    view = _native.ffi.from_buffer(buffer)
    value = _native.ffi.new("spy_BytesObject *")
    value.length = len(buffer)
    value.hash = 0
    value.data.p = _native.ffi.cast("uint8_t *", view)
    return value, view


def hash_pair(data: bytes | bytearray | memoryview) -> bytes:
    """Hash one 64-byte SSZ Merkle pair with the compiled SPy kernel."""
    source = bytes(data)
    if len(source) != 64:
        raise ValueError(f"expected exactly 64 bytes, got {len(source)}")

    output = bytearray(32)
    state, schedule = _buffers()
    source_obj, source_view = _spy_bytes(source)
    output_obj, output_view = _spy_bytes(output)
    state_obj, state_view = _spy_bytes(state)
    schedule_obj, schedule_view = _spy_bytes(schedule)
    keepalive = (source_view, output_view, state_view, schedule_view)
    _native.lib.spy_ssz_kernels_hash_pair_into(
        source_obj, 0, output_obj, 0, state_obj, schedule_obj
    )
    assert keepalive
    return bytes(output)


def _padded_work(chunks: bytes | bytearray | memoryview) -> tuple[bytearray, int]:
    raw = bytes(chunks)
    if not raw or len(raw) % 32:
        raise ValueError("chunks must contain a non-empty whole number of 32-byte chunks")
    count = len(raw) // 32
    padded_count = 1 << (count - 1).bit_length()
    work = bytearray(padded_count * 32)
    work[: len(raw)] = raw
    return work, padded_count


def merkleize(chunks: bytes | bytearray | memoryview) -> bytes:
    """Merkleize packed 32-byte leaves, padding to the next power of two."""
    work, leaf_count = _padded_work(chunks)
    state, schedule = _buffers()
    work_obj, work_view = _spy_bytes(work)
    state_obj, state_view = _spy_bytes(state)
    schedule_obj, schedule_view = _spy_bytes(schedule)
    keepalive = (work_view, state_view, schedule_view)
    _native.lib.spy_ssz_kernels_merkleize_in_place(
        work_obj, leaf_count, state_obj, schedule_obj
    )
    assert keepalive
    return bytes(work[:32])


def merkleize_python(chunks: bytes | bytearray | memoryview) -> bytes:
    """Reference implementation using CPython/OpenSSL hashlib."""
    work, count = _padded_work(chunks)
    nodes = [bytes(work[i : i + 32]) for i in range(0, len(work), 32)]
    while count > 1:
        nodes = [
            sha256(nodes[i] + nodes[i + 1]).digest()
            for i in range(0, count, 2)
        ]
        count //= 2
    return nodes[0]
