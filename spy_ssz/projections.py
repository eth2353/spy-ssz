"""Generated immutable projections from consensus_types.json; do not edit."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from .consensus_types import get_type_definition, get_type_shape
from ._repr import format_container
from ._schema_enums import Fork


_BYTE_KINDS = {
    "bitlist",
    "bitvector",
    "byte_list",
    "byte_vector",
    "progressive_bitlist",
    "progressive_byte_list",
}
_CONTAINER_KINDS = {"container", "progressive_container"}
_SEQUENCE_KINDS = {"list", "progressive_list", "vector"}


class Projection:
    def __repr__(self) -> str:
        return format_container(
            type(self).__name__,
            ((field.name, getattr(self, field.name)) for field in fields(self)),
        )

    __str__ = __repr__

    def to_obj(self) -> dict[str, Any]:
        return {
            field.name: _json_value(getattr(self, field.name)) for field in fields(self)
        }


def _json_value(value: Any) -> Any:
    if isinstance(value, Projection):
        return value.to_obj()
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, bytes):
        return f"0x{value.hex()}"
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _hex_bytes(value: Any) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise TypeError("expected 0x-prefixed hex string")
    return bytes.fromhex(value[2:])


@dataclass(frozen=True, slots=True, repr=False)
class AggregateAndProofElectra(Projection):
    aggregator_index: int
    aggregate: AttestationElectra
    selection_proof: bytes


@dataclass(frozen=True, slots=True, repr=False)
class AggregateAndProofFulu(Projection):
    aggregator_index: int
    aggregate: AttestationFulu
    selection_proof: bytes


@dataclass(frozen=True, slots=True, repr=False)
class AggregateAndProofGloas(Projection):
    aggregator_index: int
    aggregate: AttestationGloas
    selection_proof: bytes


@dataclass(frozen=True, slots=True, repr=False)
class AttestationData(Projection):
    slot: int
    index: int
    beacon_block_root: bytes
    source: Checkpoint
    target: Checkpoint


@dataclass(frozen=True, slots=True, repr=False)
class AttestationElectra(Projection):
    aggregation_bits: bytes
    data: AttestationData
    signature: bytes
    committee_bits: bytes


@dataclass(frozen=True, slots=True, repr=False)
class AttestationFulu(Projection):
    aggregation_bits: bytes
    data: AttestationData
    signature: bytes
    committee_bits: bytes


@dataclass(frozen=True, slots=True, repr=False)
class AttestationGloas(Projection):
    aggregation_bits: bytes
    data: AttestationData
    signature: bytes
    committee_bits: bytes


@dataclass(frozen=True, slots=True, repr=False)
class AttesterSlashingElectra(Projection):
    attestation_1: IndexedAttestationElectra
    attestation_2: IndexedAttestationElectra


@dataclass(frozen=True, slots=True, repr=False)
class AttesterSlashingFulu(Projection):
    attestation_1: IndexedAttestationFulu
    attestation_2: IndexedAttestationFulu


@dataclass(frozen=True, slots=True, repr=False)
class AttesterSlashingGloas(Projection):
    attestation_1: IndexedAttestationGloas
    attestation_2: IndexedAttestationGloas


@dataclass(frozen=True, slots=True, repr=False)
class BLSToExecutionChange(Projection):
    validator_index: int
    from_bls_pubkey: bytes
    to_execution_address: bytes


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockBodyElectra(Projection):
    randao_reveal: bytes
    eth1_data: Eth1Data
    graffiti: bytes
    proposer_slashings: tuple[ProposerSlashing, ...]
    attester_slashings: tuple[AttesterSlashingElectra, ...]
    attestations: tuple[AttestationElectra, ...]
    deposits: tuple[Deposit, ...]
    voluntary_exits: tuple[SignedVoluntaryExit, ...]
    sync_aggregate: SyncAggregate
    execution_payload: ExecutionPayload
    bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...]
    blob_kzg_commitments: tuple[bytes, ...]
    execution_requests: ExecutionRequestsElectra


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockBodyFulu(Projection):
    randao_reveal: bytes
    eth1_data: Eth1Data
    graffiti: bytes
    proposer_slashings: tuple[ProposerSlashing, ...]
    attester_slashings: tuple[AttesterSlashingFulu, ...]
    attestations: tuple[AttestationFulu, ...]
    deposits: tuple[Deposit, ...]
    voluntary_exits: tuple[SignedVoluntaryExit, ...]
    sync_aggregate: SyncAggregate
    execution_payload: ExecutionPayload
    bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...]
    blob_kzg_commitments: tuple[bytes, ...]
    execution_requests: ExecutionRequestsFulu


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockBodyGloas(Projection):
    randao_reveal: bytes
    eth1_data: Eth1Data
    graffiti: bytes
    proposer_slashings: tuple[ProposerSlashing, ...]
    attester_slashings: tuple[AttesterSlashingGloas, ...]
    attestations: tuple[AttestationGloas, ...]
    deposits: tuple[Deposit, ...]
    voluntary_exits: tuple[SignedVoluntaryExit, ...]
    sync_aggregate: SyncAggregate
    bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...]
    signed_execution_payload_bid: SignedExecutionPayloadBid
    payload_attestations: tuple[PayloadAttestation, ...]
    parent_execution_requests: ExecutionRequestsGloas


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockElectra(Projection):
    slot: int
    proposer_index: int
    parent_root: bytes
    state_root: bytes
    body: BeaconBlockBodyElectra


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockFulu(Projection):
    slot: int
    proposer_index: int
    parent_root: bytes
    state_root: bytes
    body: BeaconBlockBodyFulu


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockGloas(Projection):
    slot: int
    proposer_index: int
    parent_root: bytes
    state_root: bytes
    body: BeaconBlockBodyGloas


@dataclass(frozen=True, slots=True, repr=False)
class BeaconBlockHeader(Projection):
    slot: int
    proposer_index: int
    parent_root: bytes
    state_root: bytes
    body_root: bytes


@dataclass(frozen=True, slots=True, repr=False)
class BuilderDepositRequest(Projection):
    pubkey: bytes
    withdrawal_credentials: bytes
    amount: int
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class BuilderExitRequest(Projection):
    source_address: bytes
    pubkey: bytes


@dataclass(frozen=True, slots=True, repr=False)
class Checkpoint(Projection):
    epoch: int
    root: bytes


@dataclass(frozen=True, slots=True, repr=False)
class ConsolidationRequest(Projection):
    source_address: bytes
    source_pubkey: bytes
    target_pubkey: bytes


@dataclass(frozen=True, slots=True, repr=False)
class ContributionAndProof(Projection):
    aggregator_index: int
    contribution: SyncCommitteeContribution
    selection_proof: bytes


@dataclass(frozen=True, slots=True, repr=False)
class Deposit(Projection):
    proof: tuple[bytes, ...]
    data: DepositData


@dataclass(frozen=True, slots=True, repr=False)
class DepositData(Projection):
    pubkey: bytes
    withdrawal_credentials: bytes
    amount: int
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class DepositRequest(Projection):
    pubkey: bytes
    withdrawal_credentials: bytes
    amount: int
    signature: bytes
    index: int


@dataclass(frozen=True, slots=True, repr=False)
class Eth1Data(Projection):
    deposit_root: bytes
    deposit_count: int
    block_hash: bytes


@dataclass(frozen=True, slots=True, repr=False)
class ExecutionPayload(Projection):
    parent_hash: bytes
    fee_recipient: bytes
    state_root: bytes
    receipts_root: bytes
    logs_bloom: bytes
    prev_randao: bytes
    block_number: int
    gas_limit: int
    gas_used: int
    timestamp: int
    extra_data: bytes
    base_fee_per_gas: int
    block_hash: bytes
    transactions: tuple[bytes, ...]
    withdrawals: tuple[Withdrawal, ...]
    blob_gas_used: int
    excess_blob_gas: int


@dataclass(frozen=True, slots=True, repr=False)
class ExecutionPayloadBid(Projection):
    parent_block_hash: bytes
    parent_block_root: bytes
    block_hash: bytes
    prev_randao: bytes
    fee_recipient: bytes
    gas_limit: int
    builder_index: int
    slot: int
    value: int
    execution_payment: int
    blob_kzg_commitments: tuple[bytes, ...]
    execution_requests_root: bytes


@dataclass(frozen=True, slots=True, repr=False)
class ExecutionRequestsElectra(Projection):
    deposits: tuple[DepositRequest, ...]
    withdrawals: tuple[WithdrawalRequest, ...]
    consolidations: tuple[ConsolidationRequest, ...]


@dataclass(frozen=True, slots=True, repr=False)
class ExecutionRequestsFulu(Projection):
    deposits: tuple[DepositRequest, ...]
    withdrawals: tuple[WithdrawalRequest, ...]
    consolidations: tuple[ConsolidationRequest, ...]


@dataclass(frozen=True, slots=True, repr=False)
class ExecutionRequestsGloas(Projection):
    deposits: tuple[DepositRequest, ...]
    withdrawals: tuple[WithdrawalRequest, ...]
    consolidations: tuple[ConsolidationRequest, ...]
    builder_deposits: tuple[BuilderDepositRequest, ...]
    builder_exits: tuple[BuilderExitRequest, ...]


@dataclass(frozen=True, slots=True, repr=False)
class IndexedAttestationElectra(Projection):
    attesting_indices: tuple[int, ...]
    data: AttestationData
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class IndexedAttestationFulu(Projection):
    attesting_indices: tuple[int, ...]
    data: AttestationData
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class IndexedAttestationGloas(Projection):
    attesting_indices: tuple[int, ...]
    data: AttestationData
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class PayloadAttestation(Projection):
    aggregation_bits: bytes
    data: PayloadAttestationData
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class PayloadAttestationData(Projection):
    beacon_block_root: bytes
    slot: int
    payload_present: bool
    blob_data_available: bool


@dataclass(frozen=True, slots=True, repr=False)
class PayloadAttestationMessage(Projection):
    validator_index: int
    data: PayloadAttestationData
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class ProposerPreferences(Projection):
    dependent_root: bytes
    proposal_slot: int
    validator_index: int
    fee_recipient: bytes
    target_gas_limit: int


@dataclass(frozen=True, slots=True, repr=False)
class ProposerSlashing(Projection):
    signed_header_1: SignedBeaconBlockHeader
    signed_header_2: SignedBeaconBlockHeader


@dataclass(frozen=True, slots=True, repr=False)
class SignedAggregateAndProofElectra(Projection):
    message: AggregateAndProofElectra
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedAggregateAndProofFulu(Projection):
    message: AggregateAndProofFulu
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedAggregateAndProofGloas(Projection):
    message: AggregateAndProofGloas
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedBLSToExecutionChange(Projection):
    message: BLSToExecutionChange
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedBeaconBlockElectra(Projection):
    message: BeaconBlockElectra
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedBeaconBlockFulu(Projection):
    message: BeaconBlockFulu
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedBeaconBlockGloas(Projection):
    message: BeaconBlockGloas
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedBeaconBlockHeader(Projection):
    message: BeaconBlockHeader
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedContributionAndProof(Projection):
    message: ContributionAndProof
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedExecutionPayloadBid(Projection):
    message: ExecutionPayloadBid
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedProposerPreferences(Projection):
    message: ProposerPreferences
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SignedVoluntaryExit(Projection):
    message: VoluntaryExit
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SingleAttestation(Projection):
    committee_index: int
    attester_index: int
    data: AttestationData
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SyncAggregate(Projection):
    sync_committee_bits: bytes
    sync_committee_signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SyncCommitteeContribution(Projection):
    slot: int
    beacon_block_root: bytes
    subcommittee_index: int
    aggregation_bits: bytes
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class SyncCommitteeMessage(Projection):
    slot: int
    beacon_block_root: bytes
    validator_index: int
    signature: bytes


@dataclass(frozen=True, slots=True, repr=False)
class VoluntaryExit(Projection):
    epoch: int
    validator_index: int


@dataclass(frozen=True, slots=True, repr=False)
class Withdrawal(Projection):
    index: int
    validator_index: int
    address: bytes
    amount: int


@dataclass(frozen=True, slots=True, repr=False)
class WithdrawalRequest(Projection):
    source_address: bytes
    validator_pubkey: bytes
    amount: int


_PROJECTION_TYPES = {
    (Fork.ELECTRA, 12): SyncAggregate,
    (Fork.ELECTRA, 22): VoluntaryExit,
    (Fork.ELECTRA, 23): SignedVoluntaryExit,
    (Fork.ELECTRA, 26): SyncCommitteeContribution,
    (Fork.ELECTRA, 28): ContributionAndProof,
    (Fork.ELECTRA, 29): SignedContributionAndProof,
    (Fork.ELECTRA, 30): SyncCommitteeMessage,
    (Fork.ELECTRA, 33): BeaconBlockHeader,
    (Fork.ELECTRA, 34): SignedBeaconBlockHeader,
    (Fork.ELECTRA, 35): ProposerSlashing,
    (Fork.ELECTRA, 36): Eth1Data,
    (Fork.ELECTRA, 37): Checkpoint,
    (Fork.ELECTRA, 38): AttestationData,
    (Fork.ELECTRA, 39): SingleAttestation,
    (Fork.ELECTRA, 43): DepositRequest,
    (Fork.ELECTRA, 48): DepositData,
    (Fork.ELECTRA, 49): Deposit,
    (Fork.ELECTRA, 63): ConsolidationRequest,
    (Fork.ELECTRA, 64): WithdrawalRequest,
    (Fork.ELECTRA, 65): BLSToExecutionChange,
    (Fork.ELECTRA, 66): SignedBLSToExecutionChange,
    (Fork.ELECTRA, 72): Withdrawal,
    (Fork.ELECTRA, 73): ExecutionPayload,
    (Fork.ELECTRA, 110): AttestationElectra,
    (Fork.ELECTRA, 112): AggregateAndProofElectra,
    (Fork.ELECTRA, 113): SignedAggregateAndProofElectra,
    (Fork.ELECTRA, 115): IndexedAttestationElectra,
    (Fork.ELECTRA, 116): AttesterSlashingElectra,
    (Fork.ELECTRA, 120): ExecutionRequestsElectra,
    (Fork.ELECTRA, 121): BeaconBlockBodyElectra,
    (Fork.ELECTRA, 129): BeaconBlockElectra,
    (Fork.ELECTRA, 130): SignedBeaconBlockElectra,
    (Fork.FULU, 12): SyncAggregate,
    (Fork.FULU, 25): VoluntaryExit,
    (Fork.FULU, 26): SignedVoluntaryExit,
    (Fork.FULU, 30): SyncCommitteeContribution,
    (Fork.FULU, 32): ContributionAndProof,
    (Fork.FULU, 33): SignedContributionAndProof,
    (Fork.FULU, 34): SyncCommitteeMessage,
    (Fork.FULU, 37): BeaconBlockHeader,
    (Fork.FULU, 38): SignedBeaconBlockHeader,
    (Fork.FULU, 39): ProposerSlashing,
    (Fork.FULU, 40): Eth1Data,
    (Fork.FULU, 41): Checkpoint,
    (Fork.FULU, 42): AttestationData,
    (Fork.FULU, 43): SingleAttestation,
    (Fork.FULU, 47): DepositRequest,
    (Fork.FULU, 52): DepositData,
    (Fork.FULU, 53): Deposit,
    (Fork.FULU, 67): ConsolidationRequest,
    (Fork.FULU, 68): WithdrawalRequest,
    (Fork.FULU, 69): BLSToExecutionChange,
    (Fork.FULU, 70): SignedBLSToExecutionChange,
    (Fork.FULU, 76): Withdrawal,
    (Fork.FULU, 77): ExecutionPayload,
    (Fork.FULU, 115): AttestationFulu,
    (Fork.FULU, 117): AggregateAndProofFulu,
    (Fork.FULU, 118): SignedAggregateAndProofFulu,
    (Fork.FULU, 120): IndexedAttestationFulu,
    (Fork.FULU, 121): AttesterSlashingFulu,
    (Fork.FULU, 125): ExecutionRequestsFulu,
    (Fork.FULU, 126): BeaconBlockBodyFulu,
    (Fork.FULU, 134): BeaconBlockFulu,
    (Fork.FULU, 135): SignedBeaconBlockFulu,
    (Fork.GLOAS, 14): SyncAggregate,
    (Fork.GLOAS, 27): VoluntaryExit,
    (Fork.GLOAS, 28): SignedVoluntaryExit,
    (Fork.GLOAS, 30): PayloadAttestationData,
    (Fork.GLOAS, 34): PayloadAttestationMessage,
    (Fork.GLOAS, 35): PayloadAttestation,
    (Fork.GLOAS, 39): SyncCommitteeContribution,
    (Fork.GLOAS, 41): ContributionAndProof,
    (Fork.GLOAS, 42): SignedContributionAndProof,
    (Fork.GLOAS, 43): SyncCommitteeMessage,
    (Fork.GLOAS, 46): BeaconBlockHeader,
    (Fork.GLOAS, 47): SignedBeaconBlockHeader,
    (Fork.GLOAS, 48): ProposerSlashing,
    (Fork.GLOAS, 49): Eth1Data,
    (Fork.GLOAS, 50): Checkpoint,
    (Fork.GLOAS, 51): AttestationData,
    (Fork.GLOAS, 52): SingleAttestation,
    (Fork.GLOAS, 56): BuilderDepositRequest,
    (Fork.GLOAS, 58): DepositRequest,
    (Fork.GLOAS, 62): DepositData,
    (Fork.GLOAS, 63): Deposit,
    (Fork.GLOAS, 76): ProposerPreferences,
    (Fork.GLOAS, 77): SignedProposerPreferences,
    (Fork.GLOAS, 78): BuilderExitRequest,
    (Fork.GLOAS, 83): ConsolidationRequest,
    (Fork.GLOAS, 84): WithdrawalRequest,
    (Fork.GLOAS, 85): BLSToExecutionChange,
    (Fork.GLOAS, 86): SignedBLSToExecutionChange,
    (Fork.GLOAS, 99): ExecutionPayloadBid,
    (Fork.GLOAS, 126): SignedExecutionPayloadBid,
    (Fork.GLOAS, 130): AttestationGloas,
    (Fork.GLOAS, 132): AggregateAndProofGloas,
    (Fork.GLOAS, 133): SignedAggregateAndProofGloas,
    (Fork.GLOAS, 135): IndexedAttestationGloas,
    (Fork.GLOAS, 136): AttesterSlashingGloas,
    (Fork.GLOAS, 158): ExecutionRequestsGloas,
    (Fork.GLOAS, 159): BeaconBlockBodyGloas,
    (Fork.GLOAS, 167): BeaconBlockGloas,
    (Fork.GLOAS, 168): SignedBeaconBlockGloas,
}


def project_value(fork: Fork, type_id: int, value: Any) -> Any:
    shape = get_type_shape(fork, type_id)
    kind = shape["kind"]
    if kind == "boolean":
        return bool(value)
    if kind == "uint":
        return int(value)
    if kind in _BYTE_KINDS:
        return _hex_bytes(value)
    if kind in _CONTAINER_KINDS:
        projection = _PROJECTION_TYPES[(fork, type_id)]
        return projection(
            **{
                name: project_value(fork, child, value[name])
                for name, child in shape["fields"]
            }
        )
    if kind in _SEQUENCE_KINDS:
        return tuple(project_value(fork, shape["element"], item) for item in value)
    return value


def project_field(fork: Fork, consensus_type: str, name: str, value: Any) -> Any:
    definition = get_type_definition(fork, consensus_type)
    fields_by_name = dict(definition.descriptor["fields"])
    return project_value(fork, fields_by_name[name], value)
