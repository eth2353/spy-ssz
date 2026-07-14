from unittest import mock

from eth_consensus_specs.electra import mainnet as electra

from spy_ssz.preset import Preset
from spy_ssz.schema import Fork, ObjectKind
from spy_ssz.signing import (
    AttestationData,
    AttestationDataMinimal,
    SyncCommitteeContribution,
)
from spy_ssz.ssz import _JSON_ENCODERS, _SSZ_ENCODERS


def test_ssz_objects_have_schema_and_preset_scoped_value_semantics() -> None:
    reference = electra.AttestationData()
    with (
        AttestationData.from_ssz(reference.encode_bytes()) as first,
        AttestationData.from_obj(reference.to_obj()) as second,
        AttestationDataMinimal.from_ssz(reference.encode_bytes()) as minimal,
        SyncCommitteeContribution.from_obj(
            electra.SyncCommitteeContribution().to_obj()
        ) as different_schema,
    ):
        assert first == second
        assert hash(first) == hash(second)
        assert len({first, second}) == 1
        assert first != minimal
        assert first != different_schema
        assert first != object()


def test_to_obj_returns_a_detached_value() -> None:
    reference = electra.AttestationData(slot=123)
    with AttestationData.from_obj(reference.to_obj()) as value:
        expected = value.to_obj()
        detached = value.to_obj()
        detached["slot"] = "999"
        detached["source"]["epoch"] = "999"

        assert value.slot == 123
        assert value.source.epoch == 0
        assert value.to_obj() == expected


def test_immutable_objects_cache_exact_encoding_sizes() -> None:
    reference = electra.AttestationData(slot=123)
    encoded_ssz = reference.encode_bytes()
    key = (Fork.ELECTRA, ObjectKind.ATTESTATION_DATA, Preset.MAINNET)

    with AttestationData.from_ssz(encoded_ssz) as value:
        ssz_sizer, ssz_encoder = _SSZ_ENCODERS[key]
        json_sizer, json_encoder = _JSON_ENCODERS[key]
        ssz_size_calls = 0
        json_size_calls = 0

        def counted_ssz_size(handle):
            nonlocal ssz_size_calls
            ssz_size_calls += 1
            return ssz_sizer(handle)

        def counted_json_size(handle):
            nonlocal json_size_calls
            json_size_calls += 1
            return json_sizer(handle)

        with (
            mock.patch.dict(_SSZ_ENCODERS, {key: (counted_ssz_size, ssz_encoder)}),
            mock.patch.dict(_JSON_ENCODERS, {key: (counted_json_size, json_encoder)}),
        ):
            assert value.to_ssz() == encoded_ssz
            assert value.to_ssz() == encoded_ssz
            assert value.to_json() == value.to_json()

        assert ssz_size_calls == 0
        assert json_size_calls == 1
