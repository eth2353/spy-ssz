from pathlib import Path

import msgspec
from eth_consensus_specs.deneb import mainnet as deneb
from eth_consensus_specs.gloas import mainnet as gloas

from postpy_ssz.native_deneb import NativeDenebAttestation
from postpy_ssz.native_gloas import NativeGloasAttestation
from postpy_ssz.native_object import Fork, ObjectKind, decode_native_json


SAMPLE = Path(__file__).parents[1] / "block-sample-3642900.json"


def test_fork_ids_follow_consensus_chronology() -> None:
    assert list(Fork) == [
        Fork.PHASE0,
        Fork.ALTAIR,
        Fork.BELLATRIX,
        Fork.CAPELLA,
        Fork.DENEB,
        Fork.ELECTRA,
        Fork.FULU,
        Fork.GLOAS,
        Fork.HEZE,
    ]
    assert [fork.value for fork in Fork] == list(range(9))


def test_deneb_attestation_is_an_independent_native_schema() -> None:
    value = msgspec.json.decode(SAMPLE.read_bytes())["data"]["message"]["body"][
        "attestations"
    ][0]
    reference = deneb.Attestation.from_obj(value)
    with NativeDenebAttestation.from_json(msgspec.json.encode(value)) as native:
        assert native.fork is Fork.DENEB
        assert native.object_kind is ObjectKind.ATTESTATION
        assert native.schema_id == 403
        assert native.hash_tree_root() == reference.hash_tree_root()
    with NativeDenebAttestation.from_ssz(reference.encode_bytes()) as native:
        assert native.hash_tree_root() == reference.hash_tree_root()


def test_generic_registry_dispatches_by_fork_and_object_kind() -> None:
    raw = SAMPLE.read_bytes()
    with decode_native_json(
        raw, Fork.DENEB, ObjectKind.SIGNED_BEACON_BLOCK
    ) as native:
        assert native.hash_tree_root().hex() == (
            "036ead785909b45549a62c13f1617a3d"
            "84e686a0db3dc29e3b0b9a2a410a0821"
        )


def test_gloas_progressive_attestation_matches_consensus_spec() -> None:
    aggregation = bytearray(38)
    aggregation[0] = 0b0000_1001
    aggregation[32] = 0b0000_0010
    aggregation[37] = 0b0001_1000  # bit 299 and the bit-length delimiter at 300
    value = gloas.Attestation().to_obj()
    value["aggregation_bits"] = "0x" + aggregation.hex()
    value["data"]["slot"] = 123
    value["data"]["index"] = 7
    value["committee_bits"] = "0x0500000000000000"
    reference = gloas.Attestation.from_obj(value)
    raw = msgspec.json.encode(reference.to_obj())
    with NativeGloasAttestation.from_json(raw) as native:
        assert native.fork is Fork.GLOAS
        assert native.object_kind is ObjectKind.ATTESTATION
        assert native.schema_id == 703
        assert native.hash_tree_root() == reference.hash_tree_root()
    with NativeGloasAttestation.from_ssz(reference.encode_bytes()) as native:
        assert native.hash_tree_root() == reference.hash_tree_root()
