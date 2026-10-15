from importlib import import_module

import pytest

from spy_ssz import Fork, ObjectKind, Preset, get_ssz_type


@pytest.fixture(
    params=[
        (fork, preset)
        for fork in (Fork.ELECTRA, Fork.FULU, Fork.GLOAS)
        for preset in (Preset.MAINNET, Preset.MINIMAL)
    ]
)
def block_codec(request):
    fork, preset = request.param
    spec = import_module(
        f"eth_consensus_specs.{fork.name.lower()}.{preset.name.lower()}"
    )
    codec = get_ssz_type(fork, ObjectKind.SIGNED_BEACON_BLOCK, preset)
    return spec, codec


@pytest.mark.parametrize(
    ("entry", "offset"),
    [
        (0, 0),
        (0, 3),
        (0, 0x7FFFFFFC),
        (0, 0xFFFFFFFF),
        (1, 4),
        (1, 0x7FFFFFFF),
        (1, 0xFFFFFFFF),
    ],
)
def test_variable_list_rejects_invalid_offsets(block_codec, entry, offset):
    spec, codec = block_codec
    reference = spec.SignedBeaconBlock(
        message=spec.BeaconBlock(
            body=spec.BeaconBlockBody(
                attestations=[spec.Attestation(), spec.Attestation()]
            )
        )
    )
    raw = bytearray(reference.encode_bytes())
    body_start = 100 + int.from_bytes(raw[180:184], "little")
    list_start = body_start + int.from_bytes(
        raw[body_start + 208 : body_start + 212], "little"
    )
    position = list_start + entry * 4
    raw[position : position + 4] = offset.to_bytes(4, "little")
    with pytest.raises(ValueError, match="invalid SSZ object"):
        codec.from_ssz(raw)


@pytest.mark.parametrize("delta", [-1, 1])
def test_fixed_list_rejects_partial_items(block_codec, delta):
    spec, codec = block_codec
    reference = spec.SignedBeaconBlock(
        message=spec.BeaconBlock(
            body=spec.BeaconBlockBody(proposer_slashings=[spec.ProposerSlashing()])
        )
    )
    raw = bytearray(reference.encode_bytes())
    body_start = 100 + int.from_bytes(raw[180:184], "little")
    position = (
        body_start + 204
    )  # End of proposer slashings / start of attester slashings.
    end = int.from_bytes(raw[position : position + 4], "little")
    raw[position : position + 4] = (end + delta).to_bytes(4, "little")
    with pytest.raises(ValueError, match="invalid SSZ object"):
        codec.from_ssz(raw)


@pytest.mark.parametrize("fork", [Fork.ELECTRA, Fork.FULU])
@pytest.mark.parametrize("preset", [Preset.MAINNET, Preset.MINIMAL])
@pytest.mark.parametrize(
    ("field", "item_type", "limit_name"),
    [
        ("proposer_slashings", "ProposerSlashing", "MAX_PROPOSER_SLASHINGS"),
        ("attestations", "Attestation", "MAX_ATTESTATIONS_ELECTRA"),
        ("voluntary_exits", "SignedVoluntaryExit", "MAX_VOLUNTARY_EXITS"),
    ],
)
def test_bounded_list_limits(fork, preset, field, item_type, limit_name):
    spec = import_module(
        f"eth_consensus_specs.{fork.name.lower()}.{preset.name.lower()}"
    )
    codec = get_ssz_type(fork, ObjectKind.SIGNED_BEACON_BLOCK, preset)
    item = getattr(spec, item_type)()
    limit = int(getattr(spec, limit_name))
    reference = spec.SignedBeaconBlock(
        message=spec.BeaconBlock(body=spec.BeaconBlockBody(**{field: [item] * limit}))
    )
    # The boundary is valid in both formats; mutate the JSON beyond its limit.
    with codec.from_ssz(reference.encode_bytes()) as decoded:
        assert decoded.hash_tree_root() == reference.hash_tree_root()
    value = reference.to_obj()
    with codec.from_obj(value) as decoded:
        assert decoded.to_ssz() == reference.encode_bytes()
    value["message"]["body"][field].append(item.to_obj())
    with pytest.raises(ValueError, match="invalid JSON object"):
        codec.from_obj(value)
