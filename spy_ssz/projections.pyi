"""Generated immutable projections from consensus_types.json; do not edit."""

from typing import Any

from ._schema_enums import Fork

class Projection:
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def to_obj(self) -> dict[str, Any]: ...

def project_value(fork: Fork, type_id: int, value: Any) -> Any: ...
def project_field(fork: Fork, consensus_type: str, name: str, value: Any) -> Any: ...

class AggregateAndProofElectra(Projection):
    def __init__(
        self,
        aggregator_index: int,
        aggregate: AttestationElectra,
        selection_proof: bytes,
    ) -> None: ...
    @property
    def aggregator_index(self) -> int: ...
    @property
    def aggregate(self) -> AttestationElectra: ...
    @property
    def selection_proof(self) -> bytes: ...

class AggregateAndProofFulu(Projection):
    def __init__(
        self,
        aggregator_index: int,
        aggregate: AttestationFulu,
        selection_proof: bytes,
    ) -> None: ...
    @property
    def aggregator_index(self) -> int: ...
    @property
    def aggregate(self) -> AttestationFulu: ...
    @property
    def selection_proof(self) -> bytes: ...

class AggregateAndProofGloas(Projection):
    def __init__(
        self,
        aggregator_index: int,
        aggregate: AttestationGloas,
        selection_proof: bytes,
    ) -> None: ...
    @property
    def aggregator_index(self) -> int: ...
    @property
    def aggregate(self) -> AttestationGloas: ...
    @property
    def selection_proof(self) -> bytes: ...

class AttestationData(Projection):
    def __init__(
        self,
        slot: int,
        index: int,
        beacon_block_root: bytes,
        source: Checkpoint,
        target: Checkpoint,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def index(self) -> int: ...
    @property
    def beacon_block_root(self) -> bytes: ...
    @property
    def source(self) -> Checkpoint: ...
    @property
    def target(self) -> Checkpoint: ...

class AttestationElectra(Projection):
    def __init__(
        self,
        aggregation_bits: bytes,
        data: AttestationData,
        signature: bytes,
        committee_bits: bytes,
    ) -> None: ...
    @property
    def aggregation_bits(self) -> bytes: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...
    @property
    def committee_bits(self) -> bytes: ...

class AttestationFulu(Projection):
    def __init__(
        self,
        aggregation_bits: bytes,
        data: AttestationData,
        signature: bytes,
        committee_bits: bytes,
    ) -> None: ...
    @property
    def aggregation_bits(self) -> bytes: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...
    @property
    def committee_bits(self) -> bytes: ...

class AttestationGloas(Projection):
    def __init__(
        self,
        aggregation_bits: bytes,
        data: AttestationData,
        signature: bytes,
        committee_bits: bytes,
    ) -> None: ...
    @property
    def aggregation_bits(self) -> bytes: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...
    @property
    def committee_bits(self) -> bytes: ...

class AttesterSlashingElectra(Projection):
    def __init__(
        self,
        attestation_1: IndexedAttestationElectra,
        attestation_2: IndexedAttestationElectra,
    ) -> None: ...
    @property
    def attestation_1(self) -> IndexedAttestationElectra: ...
    @property
    def attestation_2(self) -> IndexedAttestationElectra: ...

class AttesterSlashingFulu(Projection):
    def __init__(
        self,
        attestation_1: IndexedAttestationFulu,
        attestation_2: IndexedAttestationFulu,
    ) -> None: ...
    @property
    def attestation_1(self) -> IndexedAttestationFulu: ...
    @property
    def attestation_2(self) -> IndexedAttestationFulu: ...

class AttesterSlashingGloas(Projection):
    def __init__(
        self,
        attestation_1: IndexedAttestationGloas,
        attestation_2: IndexedAttestationGloas,
    ) -> None: ...
    @property
    def attestation_1(self) -> IndexedAttestationGloas: ...
    @property
    def attestation_2(self) -> IndexedAttestationGloas: ...

class BLSToExecutionChange(Projection):
    def __init__(
        self,
        validator_index: int,
        from_bls_pubkey: bytes,
        to_execution_address: bytes,
    ) -> None: ...
    @property
    def validator_index(self) -> int: ...
    @property
    def from_bls_pubkey(self) -> bytes: ...
    @property
    def to_execution_address(self) -> bytes: ...

class BeaconBlockBodyElectra(Projection):
    def __init__(
        self,
        randao_reveal: bytes,
        eth1_data: Eth1Data,
        graffiti: bytes,
        proposer_slashings: tuple[ProposerSlashing, ...],
        attester_slashings: tuple[AttesterSlashingElectra, ...],
        attestations: tuple[AttestationElectra, ...],
        deposits: tuple[Deposit, ...],
        voluntary_exits: tuple[SignedVoluntaryExit, ...],
        sync_aggregate: SyncAggregate,
        execution_payload: ExecutionPayload,
        bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...],
        blob_kzg_commitments: tuple[bytes, ...],
        execution_requests: ExecutionRequestsElectra,
    ) -> None: ...
    @property
    def randao_reveal(self) -> bytes: ...
    @property
    def eth1_data(self) -> Eth1Data: ...
    @property
    def graffiti(self) -> bytes: ...
    @property
    def proposer_slashings(self) -> tuple[ProposerSlashing, ...]: ...
    @property
    def attester_slashings(self) -> tuple[AttesterSlashingElectra, ...]: ...
    @property
    def attestations(self) -> tuple[AttestationElectra, ...]: ...
    @property
    def deposits(self) -> tuple[Deposit, ...]: ...
    @property
    def voluntary_exits(self) -> tuple[SignedVoluntaryExit, ...]: ...
    @property
    def sync_aggregate(self) -> SyncAggregate: ...
    @property
    def execution_payload(self) -> ExecutionPayload: ...
    @property
    def bls_to_execution_changes(self) -> tuple[SignedBLSToExecutionChange, ...]: ...
    @property
    def blob_kzg_commitments(self) -> tuple[bytes, ...]: ...
    @property
    def execution_requests(self) -> ExecutionRequestsElectra: ...

class BeaconBlockBodyFulu(Projection):
    def __init__(
        self,
        randao_reveal: bytes,
        eth1_data: Eth1Data,
        graffiti: bytes,
        proposer_slashings: tuple[ProposerSlashing, ...],
        attester_slashings: tuple[AttesterSlashingFulu, ...],
        attestations: tuple[AttestationFulu, ...],
        deposits: tuple[Deposit, ...],
        voluntary_exits: tuple[SignedVoluntaryExit, ...],
        sync_aggregate: SyncAggregate,
        execution_payload: ExecutionPayload,
        bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...],
        blob_kzg_commitments: tuple[bytes, ...],
        execution_requests: ExecutionRequestsFulu,
    ) -> None: ...
    @property
    def randao_reveal(self) -> bytes: ...
    @property
    def eth1_data(self) -> Eth1Data: ...
    @property
    def graffiti(self) -> bytes: ...
    @property
    def proposer_slashings(self) -> tuple[ProposerSlashing, ...]: ...
    @property
    def attester_slashings(self) -> tuple[AttesterSlashingFulu, ...]: ...
    @property
    def attestations(self) -> tuple[AttestationFulu, ...]: ...
    @property
    def deposits(self) -> tuple[Deposit, ...]: ...
    @property
    def voluntary_exits(self) -> tuple[SignedVoluntaryExit, ...]: ...
    @property
    def sync_aggregate(self) -> SyncAggregate: ...
    @property
    def execution_payload(self) -> ExecutionPayload: ...
    @property
    def bls_to_execution_changes(self) -> tuple[SignedBLSToExecutionChange, ...]: ...
    @property
    def blob_kzg_commitments(self) -> tuple[bytes, ...]: ...
    @property
    def execution_requests(self) -> ExecutionRequestsFulu: ...

class BeaconBlockBodyGloas(Projection):
    def __init__(
        self,
        randao_reveal: bytes,
        eth1_data: Eth1Data,
        graffiti: bytes,
        proposer_slashings: tuple[ProposerSlashing, ...],
        attester_slashings: tuple[AttesterSlashingGloas, ...],
        attestations: tuple[AttestationGloas, ...],
        deposits: tuple[Deposit, ...],
        voluntary_exits: tuple[SignedVoluntaryExit, ...],
        sync_aggregate: SyncAggregate,
        bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...],
        signed_execution_payload_bid: SignedExecutionPayloadBid,
        payload_attestations: tuple[PayloadAttestation, ...],
        parent_execution_requests: ExecutionRequestsGloas,
    ) -> None: ...
    @property
    def randao_reveal(self) -> bytes: ...
    @property
    def eth1_data(self) -> Eth1Data: ...
    @property
    def graffiti(self) -> bytes: ...
    @property
    def proposer_slashings(self) -> tuple[ProposerSlashing, ...]: ...
    @property
    def attester_slashings(self) -> tuple[AttesterSlashingGloas, ...]: ...
    @property
    def attestations(self) -> tuple[AttestationGloas, ...]: ...
    @property
    def deposits(self) -> tuple[Deposit, ...]: ...
    @property
    def voluntary_exits(self) -> tuple[SignedVoluntaryExit, ...]: ...
    @property
    def sync_aggregate(self) -> SyncAggregate: ...
    @property
    def bls_to_execution_changes(self) -> tuple[SignedBLSToExecutionChange, ...]: ...
    @property
    def signed_execution_payload_bid(self) -> SignedExecutionPayloadBid: ...
    @property
    def payload_attestations(self) -> tuple[PayloadAttestation, ...]: ...
    @property
    def parent_execution_requests(self) -> ExecutionRequestsGloas: ...

class BeaconBlockElectra(Projection):
    def __init__(
        self,
        slot: int,
        proposer_index: int,
        parent_root: bytes,
        state_root: bytes,
        body: BeaconBlockBodyElectra,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def proposer_index(self) -> int: ...
    @property
    def parent_root(self) -> bytes: ...
    @property
    def state_root(self) -> bytes: ...
    @property
    def body(self) -> BeaconBlockBodyElectra: ...

class BeaconBlockFulu(Projection):
    def __init__(
        self,
        slot: int,
        proposer_index: int,
        parent_root: bytes,
        state_root: bytes,
        body: BeaconBlockBodyFulu,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def proposer_index(self) -> int: ...
    @property
    def parent_root(self) -> bytes: ...
    @property
    def state_root(self) -> bytes: ...
    @property
    def body(self) -> BeaconBlockBodyFulu: ...

class BeaconBlockGloas(Projection):
    def __init__(
        self,
        slot: int,
        proposer_index: int,
        parent_root: bytes,
        state_root: bytes,
        body: BeaconBlockBodyGloas,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def proposer_index(self) -> int: ...
    @property
    def parent_root(self) -> bytes: ...
    @property
    def state_root(self) -> bytes: ...
    @property
    def body(self) -> BeaconBlockBodyGloas: ...

class BeaconBlockHeader(Projection):
    def __init__(
        self,
        slot: int,
        proposer_index: int,
        parent_root: bytes,
        state_root: bytes,
        body_root: bytes,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def proposer_index(self) -> int: ...
    @property
    def parent_root(self) -> bytes: ...
    @property
    def state_root(self) -> bytes: ...
    @property
    def body_root(self) -> bytes: ...

class BuilderDepositRequest(Projection):
    def __init__(
        self,
        pubkey: bytes,
        withdrawal_credentials: bytes,
        amount: int,
        signature: bytes,
    ) -> None: ...
    @property
    def pubkey(self) -> bytes: ...
    @property
    def withdrawal_credentials(self) -> bytes: ...
    @property
    def amount(self) -> int: ...
    @property
    def signature(self) -> bytes: ...

class BuilderExitRequest(Projection):
    def __init__(
        self,
        source_address: bytes,
        pubkey: bytes,
    ) -> None: ...
    @property
    def source_address(self) -> bytes: ...
    @property
    def pubkey(self) -> bytes: ...

class Checkpoint(Projection):
    def __init__(
        self,
        epoch: int,
        root: bytes,
    ) -> None: ...
    @property
    def epoch(self) -> int: ...
    @property
    def root(self) -> bytes: ...

class ConsolidationRequest(Projection):
    def __init__(
        self,
        source_address: bytes,
        source_pubkey: bytes,
        target_pubkey: bytes,
    ) -> None: ...
    @property
    def source_address(self) -> bytes: ...
    @property
    def source_pubkey(self) -> bytes: ...
    @property
    def target_pubkey(self) -> bytes: ...

class ContributionAndProof(Projection):
    def __init__(
        self,
        aggregator_index: int,
        contribution: SyncCommitteeContribution,
        selection_proof: bytes,
    ) -> None: ...
    @property
    def aggregator_index(self) -> int: ...
    @property
    def contribution(self) -> SyncCommitteeContribution: ...
    @property
    def selection_proof(self) -> bytes: ...

class Deposit(Projection):
    def __init__(
        self,
        proof: tuple[bytes, ...],
        data: DepositData,
    ) -> None: ...
    @property
    def proof(self) -> tuple[bytes, ...]: ...
    @property
    def data(self) -> DepositData: ...

class DepositData(Projection):
    def __init__(
        self,
        pubkey: bytes,
        withdrawal_credentials: bytes,
        amount: int,
        signature: bytes,
    ) -> None: ...
    @property
    def pubkey(self) -> bytes: ...
    @property
    def withdrawal_credentials(self) -> bytes: ...
    @property
    def amount(self) -> int: ...
    @property
    def signature(self) -> bytes: ...

class DepositRequest(Projection):
    def __init__(
        self,
        pubkey: bytes,
        withdrawal_credentials: bytes,
        amount: int,
        signature: bytes,
        index: int,
    ) -> None: ...
    @property
    def pubkey(self) -> bytes: ...
    @property
    def withdrawal_credentials(self) -> bytes: ...
    @property
    def amount(self) -> int: ...
    @property
    def signature(self) -> bytes: ...
    @property
    def index(self) -> int: ...

class Eth1Data(Projection):
    def __init__(
        self,
        deposit_root: bytes,
        deposit_count: int,
        block_hash: bytes,
    ) -> None: ...
    @property
    def deposit_root(self) -> bytes: ...
    @property
    def deposit_count(self) -> int: ...
    @property
    def block_hash(self) -> bytes: ...

class ExecutionPayload(Projection):
    def __init__(
        self,
        parent_hash: bytes,
        fee_recipient: bytes,
        state_root: bytes,
        receipts_root: bytes,
        logs_bloom: bytes,
        prev_randao: bytes,
        block_number: int,
        gas_limit: int,
        gas_used: int,
        timestamp: int,
        extra_data: bytes,
        base_fee_per_gas: int,
        block_hash: bytes,
        transactions: tuple[bytes, ...],
        withdrawals: tuple[Withdrawal, ...],
        blob_gas_used: int,
        excess_blob_gas: int,
    ) -> None: ...
    @property
    def parent_hash(self) -> bytes: ...
    @property
    def fee_recipient(self) -> bytes: ...
    @property
    def state_root(self) -> bytes: ...
    @property
    def receipts_root(self) -> bytes: ...
    @property
    def logs_bloom(self) -> bytes: ...
    @property
    def prev_randao(self) -> bytes: ...
    @property
    def block_number(self) -> int: ...
    @property
    def gas_limit(self) -> int: ...
    @property
    def gas_used(self) -> int: ...
    @property
    def timestamp(self) -> int: ...
    @property
    def extra_data(self) -> bytes: ...
    @property
    def base_fee_per_gas(self) -> int: ...
    @property
    def block_hash(self) -> bytes: ...
    @property
    def transactions(self) -> tuple[bytes, ...]: ...
    @property
    def withdrawals(self) -> tuple[Withdrawal, ...]: ...
    @property
    def blob_gas_used(self) -> int: ...
    @property
    def excess_blob_gas(self) -> int: ...

class ExecutionPayloadBid(Projection):
    def __init__(
        self,
        parent_block_hash: bytes,
        parent_block_root: bytes,
        block_hash: bytes,
        prev_randao: bytes,
        fee_recipient: bytes,
        gas_limit: int,
        builder_index: int,
        slot: int,
        value: int,
        execution_payment: int,
        blob_kzg_commitments: tuple[bytes, ...],
        execution_requests_root: bytes,
    ) -> None: ...
    @property
    def parent_block_hash(self) -> bytes: ...
    @property
    def parent_block_root(self) -> bytes: ...
    @property
    def block_hash(self) -> bytes: ...
    @property
    def prev_randao(self) -> bytes: ...
    @property
    def fee_recipient(self) -> bytes: ...
    @property
    def gas_limit(self) -> int: ...
    @property
    def builder_index(self) -> int: ...
    @property
    def slot(self) -> int: ...
    @property
    def value(self) -> int: ...
    @property
    def execution_payment(self) -> int: ...
    @property
    def blob_kzg_commitments(self) -> tuple[bytes, ...]: ...
    @property
    def execution_requests_root(self) -> bytes: ...

class ExecutionRequestsElectra(Projection):
    def __init__(
        self,
        deposits: tuple[DepositRequest, ...],
        withdrawals: tuple[WithdrawalRequest, ...],
        consolidations: tuple[ConsolidationRequest, ...],
    ) -> None: ...
    @property
    def deposits(self) -> tuple[DepositRequest, ...]: ...
    @property
    def withdrawals(self) -> tuple[WithdrawalRequest, ...]: ...
    @property
    def consolidations(self) -> tuple[ConsolidationRequest, ...]: ...

class ExecutionRequestsFulu(Projection):
    def __init__(
        self,
        deposits: tuple[DepositRequest, ...],
        withdrawals: tuple[WithdrawalRequest, ...],
        consolidations: tuple[ConsolidationRequest, ...],
    ) -> None: ...
    @property
    def deposits(self) -> tuple[DepositRequest, ...]: ...
    @property
    def withdrawals(self) -> tuple[WithdrawalRequest, ...]: ...
    @property
    def consolidations(self) -> tuple[ConsolidationRequest, ...]: ...

class ExecutionRequestsGloas(Projection):
    def __init__(
        self,
        deposits: tuple[DepositRequest, ...],
        withdrawals: tuple[WithdrawalRequest, ...],
        consolidations: tuple[ConsolidationRequest, ...],
        builder_deposits: tuple[BuilderDepositRequest, ...],
        builder_exits: tuple[BuilderExitRequest, ...],
    ) -> None: ...
    @property
    def deposits(self) -> tuple[DepositRequest, ...]: ...
    @property
    def withdrawals(self) -> tuple[WithdrawalRequest, ...]: ...
    @property
    def consolidations(self) -> tuple[ConsolidationRequest, ...]: ...
    @property
    def builder_deposits(self) -> tuple[BuilderDepositRequest, ...]: ...
    @property
    def builder_exits(self) -> tuple[BuilderExitRequest, ...]: ...

class IndexedAttestationElectra(Projection):
    def __init__(
        self,
        attesting_indices: tuple[int, ...],
        data: AttestationData,
        signature: bytes,
    ) -> None: ...
    @property
    def attesting_indices(self) -> tuple[int, ...]: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...

class IndexedAttestationFulu(Projection):
    def __init__(
        self,
        attesting_indices: tuple[int, ...],
        data: AttestationData,
        signature: bytes,
    ) -> None: ...
    @property
    def attesting_indices(self) -> tuple[int, ...]: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...

class IndexedAttestationGloas(Projection):
    def __init__(
        self,
        attesting_indices: tuple[int, ...],
        data: AttestationData,
        signature: bytes,
    ) -> None: ...
    @property
    def attesting_indices(self) -> tuple[int, ...]: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...

class PayloadAttestation(Projection):
    def __init__(
        self,
        aggregation_bits: bytes,
        data: PayloadAttestationData,
        signature: bytes,
    ) -> None: ...
    @property
    def aggregation_bits(self) -> bytes: ...
    @property
    def data(self) -> PayloadAttestationData: ...
    @property
    def signature(self) -> bytes: ...

class PayloadAttestationData(Projection):
    def __init__(
        self,
        beacon_block_root: bytes,
        slot: int,
        payload_present: bool,
        blob_data_available: bool,
    ) -> None: ...
    @property
    def beacon_block_root(self) -> bytes: ...
    @property
    def slot(self) -> int: ...
    @property
    def payload_present(self) -> bool: ...
    @property
    def blob_data_available(self) -> bool: ...

class PayloadAttestationMessage(Projection):
    def __init__(
        self,
        validator_index: int,
        data: PayloadAttestationData,
        signature: bytes,
    ) -> None: ...
    @property
    def validator_index(self) -> int: ...
    @property
    def data(self) -> PayloadAttestationData: ...
    @property
    def signature(self) -> bytes: ...

class ProposerPreferences(Projection):
    def __init__(
        self,
        dependent_root: bytes,
        proposal_slot: int,
        validator_index: int,
        fee_recipient: bytes,
        target_gas_limit: int,
    ) -> None: ...
    @property
    def dependent_root(self) -> bytes: ...
    @property
    def proposal_slot(self) -> int: ...
    @property
    def validator_index(self) -> int: ...
    @property
    def fee_recipient(self) -> bytes: ...
    @property
    def target_gas_limit(self) -> int: ...

class ProposerSlashing(Projection):
    def __init__(
        self,
        signed_header_1: SignedBeaconBlockHeader,
        signed_header_2: SignedBeaconBlockHeader,
    ) -> None: ...
    @property
    def signed_header_1(self) -> SignedBeaconBlockHeader: ...
    @property
    def signed_header_2(self) -> SignedBeaconBlockHeader: ...

class SignedAggregateAndProofElectra(Projection):
    def __init__(
        self,
        message: AggregateAndProofElectra,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> AggregateAndProofElectra: ...
    @property
    def signature(self) -> bytes: ...

class SignedAggregateAndProofFulu(Projection):
    def __init__(
        self,
        message: AggregateAndProofFulu,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> AggregateAndProofFulu: ...
    @property
    def signature(self) -> bytes: ...

class SignedAggregateAndProofGloas(Projection):
    def __init__(
        self,
        message: AggregateAndProofGloas,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> AggregateAndProofGloas: ...
    @property
    def signature(self) -> bytes: ...

class SignedBLSToExecutionChange(Projection):
    def __init__(
        self,
        message: BLSToExecutionChange,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> BLSToExecutionChange: ...
    @property
    def signature(self) -> bytes: ...

class SignedBeaconBlockElectra(Projection):
    def __init__(
        self,
        message: BeaconBlockElectra,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> BeaconBlockElectra: ...
    @property
    def signature(self) -> bytes: ...

class SignedBeaconBlockFulu(Projection):
    def __init__(
        self,
        message: BeaconBlockFulu,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> BeaconBlockFulu: ...
    @property
    def signature(self) -> bytes: ...

class SignedBeaconBlockGloas(Projection):
    def __init__(
        self,
        message: BeaconBlockGloas,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> BeaconBlockGloas: ...
    @property
    def signature(self) -> bytes: ...

class SignedBeaconBlockHeader(Projection):
    def __init__(
        self,
        message: BeaconBlockHeader,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> BeaconBlockHeader: ...
    @property
    def signature(self) -> bytes: ...

class SignedContributionAndProof(Projection):
    def __init__(
        self,
        message: ContributionAndProof,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> ContributionAndProof: ...
    @property
    def signature(self) -> bytes: ...

class SignedExecutionPayloadBid(Projection):
    def __init__(
        self,
        message: ExecutionPayloadBid,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> ExecutionPayloadBid: ...
    @property
    def signature(self) -> bytes: ...

class SignedProposerPreferences(Projection):
    def __init__(
        self,
        message: ProposerPreferences,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> ProposerPreferences: ...
    @property
    def signature(self) -> bytes: ...

class SignedVoluntaryExit(Projection):
    def __init__(
        self,
        message: VoluntaryExit,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> VoluntaryExit: ...
    @property
    def signature(self) -> bytes: ...

class SingleAttestation(Projection):
    def __init__(
        self,
        committee_index: int,
        attester_index: int,
        data: AttestationData,
        signature: bytes,
    ) -> None: ...
    @property
    def committee_index(self) -> int: ...
    @property
    def attester_index(self) -> int: ...
    @property
    def data(self) -> AttestationData: ...
    @property
    def signature(self) -> bytes: ...

class SyncAggregate(Projection):
    def __init__(
        self,
        sync_committee_bits: bytes,
        sync_committee_signature: bytes,
    ) -> None: ...
    @property
    def sync_committee_bits(self) -> bytes: ...
    @property
    def sync_committee_signature(self) -> bytes: ...

class SyncCommitteeContribution(Projection):
    def __init__(
        self,
        slot: int,
        beacon_block_root: bytes,
        subcommittee_index: int,
        aggregation_bits: bytes,
        signature: bytes,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def beacon_block_root(self) -> bytes: ...
    @property
    def subcommittee_index(self) -> int: ...
    @property
    def aggregation_bits(self) -> bytes: ...
    @property
    def signature(self) -> bytes: ...

class SyncCommitteeMessage(Projection):
    def __init__(
        self,
        slot: int,
        beacon_block_root: bytes,
        validator_index: int,
        signature: bytes,
    ) -> None: ...
    @property
    def slot(self) -> int: ...
    @property
    def beacon_block_root(self) -> bytes: ...
    @property
    def validator_index(self) -> int: ...
    @property
    def signature(self) -> bytes: ...

class VoluntaryExit(Projection):
    def __init__(
        self,
        epoch: int,
        validator_index: int,
    ) -> None: ...
    @property
    def epoch(self) -> int: ...
    @property
    def validator_index(self) -> int: ...

class Withdrawal(Projection):
    def __init__(
        self,
        index: int,
        validator_index: int,
        address: bytes,
        amount: int,
    ) -> None: ...
    @property
    def index(self) -> int: ...
    @property
    def validator_index(self) -> int: ...
    @property
    def address(self) -> bytes: ...
    @property
    def amount(self) -> int: ...

class WithdrawalRequest(Projection):
    def __init__(
        self,
        source_address: bytes,
        validator_pubkey: bytes,
        amount: int,
    ) -> None: ...
    @property
    def source_address(self) -> bytes: ...
    @property
    def validator_pubkey(self) -> bytes: ...
    @property
    def amount(self) -> int: ...
