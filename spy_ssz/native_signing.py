"""Native immutable Electra signing types used by validator clients."""

from . import _native
from .native_object import (
    Fork,
    NativeSszObject,
    ObjectKind,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)
from .preset import Preset


class AttestationData(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.ATTESTATION_DATA
    json_input_envelope_key = None
    json_output_envelope_key = None


class Attestation(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.ATTESTATION
    json_input_envelope_key = None
    json_output_envelope_key = None


class AggregateAndProof(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.AGGREGATE_AND_PROOF
    json_input_envelope_key = None
    json_output_envelope_key = None


class SyncCommitteeContribution(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.SYNC_COMMITTEE_CONTRIBUTION
    json_input_envelope_key = None
    json_output_envelope_key = None


class ContributionAndProof(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.CONTRIBUTION_AND_PROOF
    json_input_envelope_key = None
    json_output_envelope_key = None


_SCHEMAS = {
    ObjectKind.ATTESTATION: 503,
    ObjectKind.ATTESTATION_DATA: 504,
    ObjectKind.AGGREGATE_AND_PROOF: 505,
    ObjectKind.SYNC_COMMITTEE_CONTRIBUTION: 506,
    ObjectKind.CONTRIBUTION_AND_PROOF: 507,
}


def _preset_type(name: str, base: type[NativeSszObject], preset: Preset):
    return type(name, (base,), {"expected_preset": preset})


for _base in (
    AttestationData,
    Attestation,
    AggregateAndProof,
    SyncCommitteeContribution,
    ContributionAndProof,
):
    globals()[f"{_base.__name__}Mainnet"] = _base
    globals()[f"{_base.__name__}Minimal"] = _preset_type(
        f"{_base.__name__}Minimal", _base, Preset.MINIMAL
    )
    globals()[f"{_base.__name__}Gnosis"] = _preset_type(
        f"{_base.__name__}Gnosis", _base, Preset.GNOSIS
    )


for _kind, _schema in _SCHEMAS.items():
    for _preset in Preset:
        register_json_decoder(
            Fork.ELECTRA,
            _kind,
            lambda source, kind=_kind, schema=_schema, preset=_preset: (
                _native.lib.spy_schema_signing_decode_json_owned(
                    source, kind, schema, preset
                )
            ),
            _preset,
        )
        register_ssz_decoder(
            Fork.ELECTRA,
            _kind,
            lambda source, kind=_kind, schema=_schema, preset=_preset: (
                _native.lib.spy_schema_signing_decode_ssz_owned(
                    source, kind, schema, preset
                )
            ),
            _preset,
        )
        register_json_encoder(
            Fork.ELECTRA,
            _kind,
            _native.lib.spy_schema_signing_json_size,
            _native.lib.spy_schema_signing_encode_json,
            _preset,
        )
        register_ssz_encoder(
            Fork.ELECTRA,
            _kind,
            _native.lib.spy_schema_signing_ssz_size,
            _native.lib.spy_schema_signing_encode_ssz,
            _preset,
        )
