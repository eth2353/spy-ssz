import pytest
from eth_consensus_specs.electra import mainnet as electra

from spy_ssz import Checkpoint
from spy_ssz._repr import format_value
from spy_ssz.signing import (
    AttestationDataElectra,
    AttestationDataElectraGnosis,
    AttestationDataElectraMinimal,
    AttestationElectra,
)


def test_projection_repr_formats_bytes_as_lowercase_hex() -> None:
    value = Checkpoint(
        epoch=108722,
        root=bytes.fromhex("E5513371" + "00" * 28),
    )

    expected = (
        "Checkpoint(epoch=108722, "
        "root=0xe551337100000000000000000000000000000000000000000000000000000000)"
    )
    assert repr(value) == expected
    assert str(value) == expected


def test_recursive_collection_repr_handles_empty_values() -> None:
    assert format_value([b"", (b"\xab",), []]) == "[0x, (0xab,), []]"


@pytest.mark.parametrize(
    ("ssz_type", "type_name"),
    [
        (AttestationDataElectra, "AttestationDataElectra"),
        (AttestationDataElectraMinimal, "AttestationDataElectraMinimal"),
        (AttestationDataElectraGnosis, "AttestationDataElectraGnosis"),
    ],
)
def test_ssz_object_repr_is_recursive_and_preserves_value_semantics(
    ssz_type, type_name: str
) -> None:
    reference = electra.AttestationData(
        slot=3479136,
        source=electra.Checkpoint(epoch=108722, root=bytes.fromhex("AA" * 32)),
        target=electra.Checkpoint(epoch=108723, root=bytes.fromhex("BB" * 32)),
    )
    with (
        ssz_type.from_obj(reference.to_obj()) as value,
        ssz_type.from_ssz(reference.encode_bytes()) as equal_value,
    ):
        before = (
            value.hash_tree_root(),
            hash(value),
            value.to_json(),
            value.to_ssz(),
        )

        rendered = repr(value)

        assert rendered.startswith(f"{type_name}(slot=3479136, index=0, ")
        assert "beacon_block_root=0x" + "00" * 32 in rendered
        assert "source=Checkpoint(epoch=108722, root=0x" + "aa" * 32 in rendered
        assert "target=Checkpoint(epoch=108723, root=0x" + "bb" * 32 in rendered
        assert "b'" not in rendered
        assert str(value) == rendered
        assert value == equal_value
        assert (
            value.hash_tree_root(),
            hash(value),
            value.to_json(),
            value.to_ssz(),
        ) == before


def test_bitfields_have_deterministic_nested_repr() -> None:
    with AttestationElectra.from_obj(electra.Attestation().to_obj()) as value:
        rendered = repr(value)

    assert "aggregation_bits=Bitfield(length=0, data=0x00)" in rendered
    assert "committee_bits=Bitfield(length=64, data=0x" + "00" * 8 in rendered
    assert "object at 0x" not in rendered
