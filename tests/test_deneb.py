from pathlib import Path

import pytest

from spy_ssz.deneb import DenebSignedBeaconBlock
from spy_ssz.schema import get_schema
from spy_ssz.ssz import Fork, ObjectKind


SAMPLE = Path(__file__).parents[1] / "block-sample-3642900.json"
SSZ_SAMPLE = Path(__file__).parents[1] / "block-sample-3642900.bin"
SIGNED_ROOT = "036ead785909b45549a62c13f1617a3d84e686a0db3dc29e3b0b9a2a410a0821"


def test_spy_decodes_json_into_owned_ssz() -> None:
    raw = SAMPLE.read_bytes()
    block = DenebSignedBeaconBlock.from_json(raw)
    try:
        assert block.fork is Fork.DENEB
        assert block.object_kind is ObjectKind.SIGNED_BEACON_BLOCK
        assert (
            block.schema_id
            == get_schema(Fork.DENEB, ObjectKind.SIGNED_BEACON_BLOCK).schema_id
        )
        assert block.node_count > 1_000
        assert block.hash_tree_root().hex() == SIGNED_ROOT
    finally:
        block.close()


def test_ssz_owns_its_decoded_input() -> None:
    source = bytearray(SAMPLE.read_bytes())
    block = DenebSignedBeaconBlock.from_json(source)
    source[:] = b"x" * len(source)
    try:
        assert block.hash_tree_root().hex() == SIGNED_ROOT
    finally:
        block.close()


def test_spy_decodes_ssz_into_the_same_ssz_shape() -> None:
    with DenebSignedBeaconBlock.from_json(SAMPLE.read_bytes()) as from_json:
        with DenebSignedBeaconBlock.from_ssz(SSZ_SAMPLE.read_bytes()) as from_ssz:
            assert from_ssz.fork is Fork.DENEB
            assert from_ssz.object_kind is ObjectKind.SIGNED_BEACON_BLOCK
            assert from_ssz.node_count == from_json.node_count
            assert from_ssz.hash_tree_root() == from_json.hash_tree_root()

    with DenebSignedBeaconBlock.decode_bytes(SSZ_SAMPLE.read_bytes()) as decoded:
        assert decoded.hash_tree_root().hex() == SIGNED_ROOT


@pytest.mark.parametrize("raw", [b"", b"\x00" * 99, b"\xff" * 100])
def test_ssz_decoder_rejects_malformed_offsets_and_truncation(raw: bytes) -> None:
    with pytest.raises(ValueError, match="invalid SSZ object"):
        DenebSignedBeaconBlock.from_ssz(raw)


def test_close_is_idempotent() -> None:
    block = DenebSignedBeaconBlock.from_json(SAMPLE.read_bytes())
    block.close()
    block.close()
