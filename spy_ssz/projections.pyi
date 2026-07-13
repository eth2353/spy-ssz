"""Generated immutable projections from consensus_types.json; do not edit."""

from typing import Any

from ._schema_enums import Fork

class Projection:
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def to_obj(self) -> dict[str, Any]: ...

def project_value(fork: Fork, type_id: int, value: Any) -> Any: ...
def project_field(fork: Fork, consensus_type: str, name: str, value: Any) -> Any: ...

class AggregateAndProof(Projection):
    def __init__(
        self,
        aggregator_index: int,
        aggregate: Attestation,
        selection_proof: bytes,
    ) -> None: ...
    @property
    def aggregator_index(self) -> int: ...
    @property
    def aggregate(self) -> Attestation: ...
    @property
    def selection_proof(self) -> bytes: ...

class Attestation(Projection):
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

class AttesterSlashing(Projection):
    def __init__(
        self,
        attestation_1: IndexedAttestation,
        attestation_2: IndexedAttestation,
    ) -> None: ...
    @property
    def attestation_1(self) -> IndexedAttestation: ...
    @property
    def attestation_2(self) -> IndexedAttestation: ...

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

class BeaconBlock(Projection):
    def __init__(
        self,
        slot: int,
        proposer_index: int,
        parent_root: bytes,
        state_root: bytes,
        body: BeaconBlockBody,
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
    def body(self) -> BeaconBlockBody: ...

class BeaconBlockBody(Projection):
    def __init__(
        self,
        randao_reveal: bytes,
        eth1_data: Eth1Data,
        graffiti: bytes,
        proposer_slashings: tuple[ProposerSlashing, ...],
        attester_slashings: tuple[AttesterSlashing, ...],
        attestations: tuple[Attestation, ...],
        deposits: tuple[Deposit, ...],
        voluntary_exits: tuple[SignedVoluntaryExit, ...],
        sync_aggregate: SyncAggregate,
        execution_payload: ExecutionPayload,
        bls_to_execution_changes: tuple[SignedBLSToExecutionChange, ...],
        blob_kzg_commitments: tuple[bytes, ...],
        execution_requests: ExecutionRequests,
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
    def attester_slashings(self) -> tuple[AttesterSlashing, ...]: ...
    @property
    def attestations(self) -> tuple[Attestation, ...]: ...
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
    def execution_requests(self) -> ExecutionRequests: ...

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

class ExecutionRequests(Projection):
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

class IndexedAttestation(Projection):
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

class SignedAggregateAndProof(Projection):
    def __init__(
        self,
        message: AggregateAndProof,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> AggregateAndProof: ...
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

class SignedBeaconBlock(Projection):
    def __init__(
        self,
        message: BeaconBlock,
        signature: bytes,
    ) -> None: ...
    @property
    def message(self) -> BeaconBlock: ...
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
