from pathlib import Path

import pytest

from postpy_ssz.native_deneb import NativeDenebBlock
from postpy_ssz.native_object import Fork, ObjectKind


SAMPLE = Path(__file__).parents[1] / "block-sample-3642900.json"
SSZ_SAMPLE = Path(__file__).parents[1] / "block-sample-3642900.bin"
SIGNED_ROOT = "036ead785909b45549a62c13f1617a3d84e686a0db3dc29e3b0b9a2a410a0821"


def test_spy_decodes_json_into_owned_native_object() -> None:
    raw = SAMPLE.read_bytes()
    block = NativeDenebBlock.from_json(raw)
    try:
        assert block.fork is Fork.DENEB
        assert block.object_kind is ObjectKind.SIGNED_BEACON_BLOCK
        assert block._node_count > 1_000
        assert block.hash_tree_root().hex() == SIGNED_ROOT
    finally:
        block.close()


def test_native_object_owns_its_decoded_input() -> None:
    source = bytearray(SAMPLE.read_bytes())
    block = NativeDenebBlock.from_json(source)
    source[:] = b"x" * len(source)
    try:
        assert block.hash_tree_root().hex() == SIGNED_ROOT
    finally:
        block.close()


def test_spy_decodes_ssz_into_the_same_native_object_shape() -> None:
    with NativeDenebBlock.from_json(SAMPLE.read_bytes()) as from_json:
        with NativeDenebBlock.from_ssz(SSZ_SAMPLE.read_bytes()) as from_ssz:
            assert from_ssz.fork is Fork.DENEB
            assert from_ssz.object_kind is ObjectKind.SIGNED_BEACON_BLOCK
            assert from_ssz._node_count == from_json._node_count
            assert from_ssz.hash_tree_root() == from_json.hash_tree_root()

    with NativeDenebBlock.decode_bytes(SSZ_SAMPLE.read_bytes()) as decoded:
        assert decoded.hash_tree_root().hex() == SIGNED_ROOT


@pytest.mark.parametrize("raw", [b"", b"\x00" * 99, b"\xff" * 100])
def test_ssz_decoder_rejects_malformed_offsets_and_truncation(raw: bytes) -> None:
    with pytest.raises(ValueError, match="invalid SSZ object"):
        NativeDenebBlock.from_ssz(raw)


def test_close_is_idempotent() -> None:
    block = NativeDenebBlock.from_json(SAMPLE.read_bytes())
    block.close()
    block.close()
