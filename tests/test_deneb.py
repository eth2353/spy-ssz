from pathlib import Path

import msgspec
from eth_consensus_specs.deneb import mainnet as spec

from postpy_ssz.deneb import DenebSignedBeaconBlock, decode_deneb_block


SAMPLE = Path(__file__).parents[1] / "block-sample-3642900.json"
MESSAGE_ROOT = "784dad99478a2ca8fd04615fb530290655b41f49896e90146318ecec9fbd31e7"
SIGNED_ROOT = "036ead785909b45549a62c13f1617a3d84e686a0db3dc29e3b0b9a2a410a0821"


def test_sample_roots() -> None:
    block = decode_deneb_block(SAMPLE.read_bytes())
    assert block.message_hash_tree_root().hex() == MESSAGE_ROOT
    assert block.hash_tree_root().hex() == SIGNED_ROOT


def test_matches_official_consensus_types() -> None:
    value = msgspec.json.decode(SAMPLE.read_bytes())["data"]
    reference = spec.SignedBeaconBlock.from_obj(value)
    block = DenebSignedBeaconBlock.from_obj(value)
    assert block.message_hash_tree_root() == reference.message.hash_tree_root()
    assert block.hash_tree_root() == reference.hash_tree_root()


def test_roots_are_cached() -> None:
    block = decode_deneb_block(SAMPLE.read_bytes())
    assert block.hash_tree_root() is block.hash_tree_root()
