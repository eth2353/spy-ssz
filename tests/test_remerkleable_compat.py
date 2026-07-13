"""Portable compatibility tests from ethereum/remerkleable.

The upstream suite exercises generic type construction and mutable Merkle views,
which spy-ssz intentionally does not expose.  These tests port the behavioral
contracts that do apply to its concrete consensus containers: object and JSON
conversion, SSZ encoding/decoding, tree hashing, equality, and read-only bitfield
access.  Upstream revision: 97d970e107214b59d146dffa7d837e7144b457e6.
"""

from collections.abc import Callable
from random import Random
from typing import Any

import msgspec
import pytest
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz.signing import (
    AggregateAndProof,
    Attestation,
    AttestationData,
    AttesterSlashing,
    BeaconBlockHeader,
    ContributionAndProof,
    IndexedAttestation,
    ProposerSlashing,
    SignedAggregateAndProof,
    SignedBeaconBlockHeader,
    SignedContributionAndProof,
    SingleAttestation,
    SyncCommitteeContribution,
    SyncCommitteeMessage,
)
from spy_ssz.ssz import Bitfield, SszObject


ReferenceFactory = Callable[[], Any]


@pytest.mark.parametrize(
    ("method", "encoding"),
    [(AttestationData.from_json, "JSON"), (AttestationData.from_ssz, "SSZ")],
)
def test_decode_rejects_inputs_over_native_size_limit(
    monkeypatch: pytest.MonkeyPatch,
    method: Callable[[bytes], SszObject],
    encoding: str,
) -> None:
    monkeypatch.setattr("spy_ssz.ssz._MAX_NATIVE_INPUT_LENGTH", 10)

    with pytest.raises(
        ValueError,
        match=rf"^{encoding} input exceeds the 10-byte implementation limit$",
    ):
        method(b"xxxxxxxxxxx")


def _root(byte: int) -> bytes:
    return bytes([byte]) * 32


def _signature(seed: int) -> bytes:
    return bytes((seed + index) % 256 for index in range(96))


def _attestation_data() -> electra.AttestationData:
    return electra.AttestationData(
        slot=0x0123456789ABCDEF,
        index=0x1020304050607080,
        beacon_block_root=_root(0xA5),
        source=electra.Checkpoint(epoch=0x1112131415161718, root=_root(0x5A)),
        target=electra.Checkpoint(epoch=0x2122232425262728, root=_root(0xC3)),
    )


def _attestation() -> electra.Attestation:
    return electra.Attestation(
        aggregation_bits=[True, False, True, True, False, False, True, False, True],
        data=_attestation_data(),
        signature=_signature(3),
        committee_bits=[index in {0, 7, 8, 31, 63} for index in range(64)],
    )


def _aggregate_and_proof() -> electra.AggregateAndProof:
    return electra.AggregateAndProof(
        aggregator_index=0xFFEEDDCCBBAA9988,
        aggregate=_attestation(),
        selection_proof=_signature(17),
    )


def _sync_contribution() -> electra.SyncCommitteeContribution:
    return electra.SyncCommitteeContribution(
        slot=0x0102030405060708,
        beacon_block_root=_root(0x42),
        subcommittee_index=3,
        aggregation_bits=[index % 3 == 1 for index in range(128)],
        signature=_signature(29),
    )


def _contribution_and_proof() -> electra.ContributionAndProof:
    return electra.ContributionAndProof(
        aggregator_index=0x8877665544332211,
        contribution=_sync_contribution(),
        selection_proof=_signature(41),
    )


def _header(seed: int) -> electra.BeaconBlockHeader:
    return electra.BeaconBlockHeader(
        slot=seed * 11,
        proposer_index=seed * 13,
        parent_root=_root(seed),
        state_root=_root(seed + 1),
        body_root=_root(seed + 2),
    )


CASES: list[tuple[str, type[SszObject], ReferenceFactory]] = [
    ("attestation_data", AttestationData, _attestation_data),
    ("attestation", Attestation, _attestation),
    ("aggregate_and_proof", AggregateAndProof, _aggregate_and_proof),
    (
        "signed_aggregate_and_proof",
        SignedAggregateAndProof,
        lambda: electra.SignedAggregateAndProof(
            message=_aggregate_and_proof(), signature=_signature(53)
        ),
    ),
    ("sync_committee_contribution", SyncCommitteeContribution, _sync_contribution),
    ("contribution_and_proof", ContributionAndProof, _contribution_and_proof),
    (
        "signed_contribution_and_proof",
        SignedContributionAndProof,
        lambda: electra.SignedContributionAndProof(
            message=_contribution_and_proof(), signature=_signature(67)
        ),
    ),
    (
        "single_attestation",
        SingleAttestation,
        lambda: electra.SingleAttestation(
            committee_index=12,
            attester_index=34,
            data=_attestation_data(),
            signature=_signature(79),
        ),
    ),
    (
        "sync_committee_message",
        SyncCommitteeMessage,
        lambda: electra.SyncCommitteeMessage(
            slot=56,
            beacon_block_root=_root(0x91),
            validator_index=78,
            signature=_signature(83),
        ),
    ),
    (
        "indexed_attestation",
        IndexedAttestation,
        lambda: electra.IndexedAttestation(
            attesting_indices=[0, 1, 2, 31, 2**32, 2**64 - 1],
            data=_attestation_data(),
            signature=_signature(97),
        ),
    ),
    (
        "attester_slashing",
        AttesterSlashing,
        lambda: electra.AttesterSlashing(
            attestation_1=electra.IndexedAttestation(
                attesting_indices=[1, 3, 5],
                data=_attestation_data(),
                signature=_signature(101),
            ),
            attestation_2=electra.IndexedAttestation(
                attesting_indices=[2, 4, 6, 8],
                data=_attestation_data(),
                signature=_signature(103),
            ),
        ),
    ),
    ("beacon_block_header", BeaconBlockHeader, lambda: _header(7)),
    (
        "signed_beacon_block_header",
        SignedBeaconBlockHeader,
        lambda: electra.SignedBeaconBlockHeader(
            message=_header(9), signature=_signature(107)
        ),
    ),
    (
        "proposer_slashing",
        ProposerSlashing,
        lambda: electra.ProposerSlashing(
            signed_header_1=electra.SignedBeaconBlockHeader(
                message=_header(11), signature=_signature(109)
            ),
            signed_header_2=electra.SignedBeaconBlockHeader(
                message=_header(13), signature=_signature(113)
            ),
        ),
    ),
]


@pytest.mark.parametrize(("name", "spy_type", "reference_factory"), CASES)
def test_populated_containers_port_remerkleable_value_operations(
    name: str,
    spy_type: type[SszObject],
    reference_factory: ReferenceFactory,
) -> None:
    del name
    reference = reference_factory()
    expected_obj = reference.to_obj()
    expected_ssz = reference.encode_bytes()
    expected_root = reference.hash_tree_root()

    with spy_type.from_obj(expected_obj) as from_obj:
        assert from_obj.to_ssz() == expected_ssz
        assert from_obj.hash_tree_root() == expected_root
        assert reference.__class__.from_obj(from_obj.to_obj()) == reference

        encoded_obj = msgspec.json.decode(from_obj.to_json())
        assert reference.__class__.from_obj(encoded_obj) == reference

    with spy_type.from_json(msgspec.json.encode(expected_obj)) as from_json:
        assert from_json.to_ssz() == expected_ssz
        assert from_json.hash_tree_root() == expected_root
        assert reference.__class__.from_obj(from_json.to_obj()) == reference

    with spy_type.from_ssz(expected_ssz) as from_ssz:
        assert from_ssz.to_ssz() == expected_ssz
        assert from_ssz.hash_tree_root() == expected_root
        assert reference.__class__.from_obj(from_ssz.to_obj()) == reference


@pytest.mark.parametrize(("name", "spy_type", "reference_factory"), CASES)
def test_populated_containers_port_remerkleable_equality(
    name: str,
    spy_type: type[SszObject],
    reference_factory: ReferenceFactory,
) -> None:
    del name
    reference = reference_factory()
    with (
        spy_type.from_obj(reference.to_obj()) as from_obj,
        spy_type.from_ssz(reference.encode_bytes()) as from_ssz,
        spy_type.from_json(msgspec.json.encode(reference.to_obj())) as from_json,
    ):
        assert from_obj == from_ssz == from_json
        assert len({from_obj, from_ssz, from_json}) == 1


@pytest.mark.parametrize(("name", "spy_type", "reference_factory"), CASES)
def test_ssz_decoders_reject_noncanonical_container_lengths(
    name: str,
    spy_type: type[SszObject],
    reference_factory: ReferenceFactory,
) -> None:
    del name
    encoded = reference_factory().encode_bytes()

    if spy_type not in {Attestation, AggregateAndProof, SignedAggregateAndProof}:
        with pytest.raises(ValueError, match="invalid SSZ object"):
            spy_type.from_ssz(encoded[:-1])
    with pytest.raises(ValueError, match="invalid SSZ object"):
        spy_type.from_ssz(encoded + b"\x00")


@pytest.mark.parametrize("invalid", ["", str(2**64), str(2**80), 2**64])
def test_json_uint64_rejects_values_remerkleable_considers_out_of_bounds(
    invalid: str | int,
) -> None:
    value = electra.AttestationData().to_obj()
    value["slot"] = invalid

    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(msgspec.json.encode(value))


def test_json_uint64_accepts_its_upper_bound_without_truncation() -> None:
    reference = electra.AttestationData(slot=2**64 - 1)

    with AttestationData.from_obj(reference.to_obj()) as value:
        assert value.slot == 2**64 - 1
        assert value.to_ssz() == reference.encode_bytes()
        assert value.hash_tree_root() == reference.hash_tree_root()


def test_json_uint64_accepts_remerkleable_little_endian_hex() -> None:
    value = electra.AttestationData().to_obj()
    value["slot"] = "0x0302010000000000"
    reference = electra.AttestationData.from_obj(value)

    with AttestationData.from_obj(value) as decoded:
        assert decoded.slot == 0x010203
        assert decoded.to_ssz() == reference.encode_bytes()
        assert decoded.hash_tree_root() == reference.hash_tree_root()


def _malformed_json_cases() -> list[bytes]:
    raw = msgspec.json.encode(electra.AttestationData().to_obj())
    return [
        raw.replace(b":", b"", 1),
        raw.replace(b",", b"", 1),
        raw.replace(b":", b"::", 1),
        raw.replace(b",", b",,", 1),
        raw[:-1] + b",}",
        raw[:-1] + b"]",
        raw + b"true",
        b"true" + raw,
    ]


@pytest.mark.parametrize("raw", _malformed_json_cases())
def test_json_decoder_rejects_malformed_container_syntax(raw: bytes) -> None:
    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(raw)


def test_json_decoder_rejects_leading_zero_in_uint64() -> None:
    raw = msgspec.json.encode(electra.AttestationData().to_obj()).replace(
        b'"slot":0', b'"slot":01'
    )

    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(raw)


def test_json_decoder_rejects_leading_zero_in_basic_uint_list() -> None:
    raw = msgspec.json.encode(
        electra.IndexedAttestation(attesting_indices=[12]).to_obj()
    ).replace(b"[12]", b"[012]")

    with pytest.raises(ValueError, match="invalid JSON object"):
        IndexedAttestation.from_json(raw)


@pytest.mark.parametrize(
    "unknown_key",
    [b'"\xc6\xec"', b'"\\q"', b'"\x01"', b'"\xed\xa0\x80"'],
)
def test_json_decoder_rejects_invalid_ignored_object_keys(
    unknown_key: bytes,
) -> None:
    raw = msgspec.json.encode(electra.AttestationData().to_obj())
    malformed = raw[:-1] + b"," + unknown_key + b":0}"

    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(malformed)


@pytest.mark.parametrize("primitive", [b"truth", b"01", b"1.", b"1e", b"-"])
def test_json_decoder_rejects_invalid_ignored_primitives(primitive: bytes) -> None:
    raw = msgspec.json.encode(electra.AttestationData().to_obj())
    malformed = raw[:-1] + b',"ignored":' + primitive + b"}"

    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(malformed)


def test_json_decoder_rejects_valid_unrecognized_fields() -> None:
    reference = electra.AttestationData(slot=123)
    raw = msgspec.json.encode(reference.to_obj())
    extended = raw[:-1] + b',"snowman":"\xe2\x98\x83","escaped":"\\n"}'

    with pytest.raises(ValueError, match="^unrecognized JSON object field 'snowman'$"):
        AttestationData.from_json(extended)


def test_json_decoder_rejects_duplicate_object_keys() -> None:
    raw = msgspec.json.encode(electra.AttestationData().to_obj())
    duplicated = raw.replace(b'"slot":0', b'"slot":1,"slot":0')

    with pytest.raises(ValueError, match="invalid JSON object"):
        AttestationData.from_json(duplicated)


def test_ssz_decoder_rejects_extreme_variable_offsets_without_crashing() -> None:
    encoded = bytearray(_attestation().encode_bytes())
    encoded[:4] = b"\xff\xff\xff\x7f"

    with pytest.raises(ValueError, match="invalid SSZ object"):
        Attestation.from_ssz(encoded)


UPSTREAM_BITFIELD_CASES = [
    ("0x01", True, []),
    ("0x2b01", True, [True, True, False, True, False, True, False, False]),
    ("0x1a", True, [False, True, False, True]),
    ("0x0a", True, [False, True, False]),
    ("0xc506", True, [True, False, True, False, False, False, True, True, False, True]),
    ("0x2b", False, [True, True, False, True, False, True, False, False]),
    ("0x0a", False, [False, True, False, True, False, False, False, False]),
    (
        "0xc502",
        False,
        [
            True,
            False,
            True,
            False,
            False,
            False,
            True,
            True,
            False,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
        ],
    ),
]


@pytest.mark.parametrize(("encoded", "bitlist", "expected"), UPSTREAM_BITFIELD_CASES)
def test_upstream_bitfield_iteration_indexing_and_count(
    encoded: str, bitlist: bool, expected: list[bool]
) -> None:
    value = Bitfield.from_hex(encoded, bitlist=bitlist)

    assert len(value) == len(expected)
    assert list(value) == expected
    assert value.count() == expected.count(True)
    assert value.count(False) == expected.count(False)
    for index, bit in enumerate(expected):
        assert value[index] is bit
        assert value[index - len(expected)] is bit
    with pytest.raises(IndexError):
        _ = value[len(expected)]
    with pytest.raises(IndexError):
        _ = value[-len(expected) - 1]


@pytest.mark.parametrize("encoded", ["0x", "0x00", "0x0000"])
def test_bitlist_rejects_a_missing_termination_bit(encoded: str) -> None:
    with pytest.raises(ValueError, match="termination bit"):
        Bitfield.from_hex(encoded, bitlist=True)


BITFIELD_SIZES = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    15,
    16,
    17,
    31,
    32,
    33,
    63,
    64,
    65,
    255,
    256,
    257,
    511,
    512,
    513,
    1023,
    1024,
    1025,
]


def _encode_bits(bits: list[bool], *, bitlist: bool) -> str:
    bit_count = len(bits) + bitlist
    data = bytearray((bit_count + 7) // 8)
    for index, bit in enumerate(bits):
        if bit:
            data[index // 8] |= 1 << (index % 8)
    if bitlist:
        marker = len(bits)
        data[marker // 8] |= 1 << (marker % 8)
    return f"0x{data.hex()}"


@pytest.mark.parametrize("size", [8, 16, 32, 64, 128, 256, 512, 1024])
def test_upstream_bitvector_readonly_iteration_for_boundary_sizes(size: int) -> None:
    rng = Random(123 + size)
    expected = [bool(rng.randint(0, 1)) for _ in range(size)]
    value = Bitfield.from_hex(_encode_bits(expected, bitlist=False), bitlist=False)

    assert list(value) == expected


@pytest.mark.parametrize("limit", BITFIELD_SIZES)
def test_upstream_bitlist_readonly_iteration_for_boundary_sizes(limit: int) -> None:
    rng = Random(456 + limit)
    for length in {0, 1, limit // 2, limit}:
        expected = [bool(rng.randint(0, 1)) for _ in range(length)]
        value = Bitfield.from_hex(_encode_bits(expected, bitlist=True), bitlist=True)

        assert list(value) == expected
