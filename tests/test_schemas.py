from pathlib import Path

import msgspec
import pytest
from eth_consensus_specs.deneb import mainnet as deneb

from spy_ssz.deneb import DenebAttestation
from spy_ssz.schema import get_schema, schema_for
from spy_ssz.ssz import Fork, ObjectKind, decode_json


SAMPLE = Path(__file__).parent / "fixtures" / "block-sample-3642900.json"


def test_fork_ids_follow_consensus_chronology() -> None:
    assert list(Fork) == [
        Fork.PHASE0,
        Fork.ALTAIR,
        Fork.BELLATRIX,
        Fork.CAPELLA,
        Fork.DENEB,
        Fork.ELECTRA,
        Fork.FULU,
    ]
    assert [fork.value for fork in Fork] == list(range(7))


def test_single_schema_codec_lookup_rejects_multiplexed_codecs() -> None:
    assert schema_for("electra_block").fork is Fork.ELECTRA
    with pytest.raises(ValueError, match="expected one schema for 'signing'"):
        schema_for("signing")


def test_deneb_attestation_is_an_independent_schema() -> None:
    value = msgspec.json.decode(SAMPLE.read_bytes())["data"]["message"]["body"][
        "attestations"
    ][0]
    reference = deneb.Attestation.from_obj(value)
    with DenebAttestation.from_json(msgspec.json.encode(value)) as decoded:
        assert decoded.fork is Fork.DENEB
        assert decoded.object_kind is ObjectKind.ATTESTATION
        assert (
            decoded.schema_id
            == get_schema(Fork.DENEB, ObjectKind.ATTESTATION).schema_id
        )
        assert decoded.hash_tree_root() == reference.hash_tree_root()
    with DenebAttestation.from_ssz(reference.encode_bytes()) as decoded:
        assert decoded.hash_tree_root() == reference.hash_tree_root()


def test_generic_registry_dispatches_by_fork_and_object_kind() -> None:
    raw = SAMPLE.read_bytes()
    with decode_json(raw, Fork.DENEB, ObjectKind.SIGNED_BEACON_BLOCK) as decoded:
        assert decoded.hash_tree_root().hex() == (
            "036ead785909b45549a62c13f1617a3d84e686a0db3dc29e3b0b9a2a410a0821"
        )
