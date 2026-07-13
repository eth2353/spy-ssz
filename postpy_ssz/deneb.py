"""Fast, schema-specialized JSON decoding and SSZ roots for Deneb blocks.

The generic remerkleable decoder eagerly creates a persistent tree node for every
value.  This module keeps the Beacon API object compact and computes its SSZ root
directly.  It is intentionally Deneb-specific: specialization is the source of
most of the speed-up and makes the hot path suitable for native compilation.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

import msgspec


Bytes32 = bytes
ZERO_CHUNK = bytes(32)


class _JSONStruct(msgspec.Struct):
    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)


class _Checkpoint(_JSONStruct):
    epoch: str
    root: str


class _AttestationData(_JSONStruct):
    slot: str
    index: str
    beacon_block_root: str
    source: _Checkpoint
    target: _Checkpoint


class _Attestation(_JSONStruct):
    aggregation_bits: str
    data: _AttestationData
    signature: str


class _Eth1Data(_JSONStruct):
    deposit_root: str
    deposit_count: str
    block_hash: str


class _SyncAggregate(_JSONStruct):
    sync_committee_bits: str
    sync_committee_signature: str


class _Withdrawal(_JSONStruct):
    index: str
    validator_index: str
    address: str
    amount: str


class _VoluntaryExitMessage(_JSONStruct):
    epoch: str
    validator_index: str


class _SignedVoluntaryExit(_JSONStruct):
    message: _VoluntaryExitMessage
    signature: str


class _BLSToExecutionChangeMessage(_JSONStruct):
    validator_index: str
    from_bls_pubkey: str
    to_execution_address: str


class _SignedBLSToExecutionChange(_JSONStruct):
    message: _BLSToExecutionChangeMessage
    signature: str


class _ExecutionPayload(_JSONStruct):
    parent_hash: str
    fee_recipient: str
    state_root: str
    receipts_root: str
    logs_bloom: str
    prev_randao: str
    block_number: str
    gas_limit: str
    gas_used: str
    timestamp: str
    extra_data: str
    base_fee_per_gas: str
    block_hash: str
    transactions: list[str]
    withdrawals: list[_Withdrawal]
    blob_gas_used: str
    excess_blob_gas: str


class _BeaconBlockBody(_JSONStruct):
    randao_reveal: str
    eth1_data: _Eth1Data
    graffiti: str
    proposer_slashings: list[Any]
    attester_slashings: list[Any]
    attestations: list[_Attestation]
    deposits: list[Any]
    voluntary_exits: list[_SignedVoluntaryExit]
    sync_aggregate: _SyncAggregate
    execution_payload: _ExecutionPayload
    bls_to_execution_changes: list[_SignedBLSToExecutionChange]
    blob_kzg_commitments: list[str]


class _BeaconBlock(_JSONStruct):
    slot: str
    proposer_index: str
    parent_root: str
    state_root: str
    body: _BeaconBlockBody


class _SignedBlockJSON(_JSONStruct):
    message: _BeaconBlock
    signature: str


class _BlockEnvelope(_JSONStruct):
    version: str
    execution_optimistic: bool
    finalized: bool
    data: _SignedBlockJSON


_BLOCK_DECODER = msgspec.json.Decoder(_BlockEnvelope)


def _hash(left: bytes, right: bytes) -> bytes:
    return sha256(left + right).digest()


ZERO_HASHES = [ZERO_CHUNK]
for _ in range(64):
    ZERO_HASHES.append(_hash(ZERO_HASHES[-1], ZERO_HASHES[-1]))


def _depth(limit: int) -> int:
    return (limit - 1).bit_length() if limit > 1 else 0


def _merkleize(chunks: list[bytes], limit: int | None = None) -> bytes:
    count = len(chunks)
    if limit is None:
        limit = max(1, count)
    if count > limit:
        raise ValueError(f"{count} chunks exceed SSZ limit {limit}")
    target_depth = _depth(limit)
    if not chunks:
        return ZERO_HASHES[target_depth]

    width = 1 << _depth(count)
    nodes = chunks + [ZERO_CHUNK] * (width - count)
    level = 0
    while len(nodes) > 1:
        nodes = [_hash(nodes[i], nodes[i + 1]) for i in range(0, len(nodes), 2)]
        level += 1
    root = nodes[0]
    while level < target_depth:
        root = _hash(root, ZERO_HASHES[level])
        level += 1
    return root


def _mix_length(root: bytes, length: int) -> bytes:
    return _hash(root, length.to_bytes(32, "little"))


def _hex(value: str | bytes) -> bytes:
    if isinstance(value, bytes):
        return value
    if not value.startswith("0x"):
        raise ValueError("Beacon API byte strings must start with 0x")
    return bytes.fromhex(value[2:])


def _uint(value: str | int, size: int = 8) -> bytes:
    return int(value).to_bytes(size, "little") + bytes(32 - size)


def _fixed_bytes(value: str | bytes, size: int) -> bytes:
    raw = _hex(value)
    if len(raw) != size:
        raise ValueError(f"expected {size} bytes, got {len(raw)}")
    if size <= 32:
        return raw + bytes(32 - size)
    return _merkleize(
        [raw[i : i + 32].ljust(32, b"\0") for i in range(0, size, 32)]
    )


def _byte_list(value: str | bytes, limit: int) -> bytes:
    raw = _hex(value)
    if len(raw) > limit:
        raise ValueError(f"byte list length {len(raw)} exceeds {limit}")
    chunks = [raw[i : i + 32].ljust(32, b"\0") for i in range(0, len(raw), 32)]
    return _mix_length(_merkleize(chunks, (limit + 31) // 32), len(raw))


def _bitlist(value: str | bytes, limit: int) -> bytes:
    encoded = bytearray(_hex(value))
    if not encoded or encoded[-1] == 0:
        raise ValueError("invalid SSZ bitlist delimiter")
    delimiter = encoded[-1].bit_length() - 1
    bit_length = (len(encoded) - 1) * 8 + delimiter
    if bit_length > limit:
        raise ValueError(f"bitlist length {bit_length} exceeds {limit}")
    encoded[-1] ^= 1 << delimiter
    if encoded[-1] == 0:
        encoded.pop()
    chunks = [bytes(encoded[i : i + 32]).ljust(32, b"\0") for i in range(0, len(encoded), 32)]
    return _mix_length(_merkleize(chunks, (limit + 255) // 256), bit_length)


def _container(fields: list[bytes]) -> bytes:
    return _merkleize(fields)


def _composite_list(values: list[Mapping[str, Any]], limit: int, root_fn: Any) -> bytes:
    return _mix_length(_merkleize([root_fn(value) for value in values], limit), len(values))


def _bytes_list(values: list[str], limit: int, size: int) -> bytes:
    return _mix_length(_merkleize([_fixed_bytes(value, size) for value in values], limit), len(values))


def _checkpoint(value: Mapping[str, Any]) -> bytes:
    return _container([_uint(value["epoch"]), _fixed_bytes(value["root"], 32)])


def _attestation_data(value: Mapping[str, Any]) -> bytes:
    return _container(
        [
            _uint(value["slot"]),
            _uint(value["index"]),
            _fixed_bytes(value["beacon_block_root"], 32),
            _checkpoint(value["source"]),
            _checkpoint(value["target"]),
        ]
    )


def _attestation(value: Mapping[str, Any]) -> bytes:
    return _container(
        [
            _bitlist(value["aggregation_bits"], 2048),
            _attestation_data(value["data"]),
            _fixed_bytes(value["signature"], 96),
        ]
    )


def _withdrawal(value: Mapping[str, Any]) -> bytes:
    return _container(
        [
            _uint(value["index"]),
            _uint(value["validator_index"]),
            _fixed_bytes(value["address"], 20),
            _uint(value["amount"]),
        ]
    )


def _voluntary_exit(value: Mapping[str, Any]) -> bytes:
    message = value["message"]
    return _container(
        [
            _container([_uint(message["epoch"]), _uint(message["validator_index"])]),
            _fixed_bytes(value["signature"], 96),
        ]
    )


def _bls_to_execution_change(value: Mapping[str, Any]) -> bytes:
    message = value["message"]
    return _container(
        [
            _container(
                [
                    _uint(message["validator_index"]),
                    _fixed_bytes(message["from_bls_pubkey"], 48),
                    _fixed_bytes(message["to_execution_address"], 20),
                ]
            ),
            _fixed_bytes(value["signature"], 96),
        ]
    )


def _execution_payload(value: Mapping[str, Any]) -> bytes:
    transactions = value["transactions"]
    transaction_roots = [_byte_list(tx, 1 << 30) for tx in transactions]
    transactions_root = _mix_length(
        _merkleize(transaction_roots, 1 << 20), len(transactions)
    )
    withdrawals = value["withdrawals"]
    withdrawals_root = _composite_list(withdrawals, 16, _withdrawal)
    return _container(
        [
            _fixed_bytes(value["parent_hash"], 32),
            _fixed_bytes(value["fee_recipient"], 20),
            _fixed_bytes(value["state_root"], 32),
            _fixed_bytes(value["receipts_root"], 32),
            _fixed_bytes(value["logs_bloom"], 256),
            _fixed_bytes(value["prev_randao"], 32),
            _uint(value["block_number"]),
            _uint(value["gas_limit"]),
            _uint(value["gas_used"]),
            _uint(value["timestamp"]),
            _byte_list(value["extra_data"], 32),
            _uint(value["base_fee_per_gas"], 32),
            _fixed_bytes(value["block_hash"], 32),
            transactions_root,
            withdrawals_root,
            _uint(value["blob_gas_used"]),
            _uint(value["excess_blob_gas"]),
        ]
    )


def _empty_only_list(values: list[Any], limit: int, name: str) -> bytes:
    if values:
        raise NotImplementedError(f"the POC does not yet support non-empty {name}")
    return _mix_length(_merkleize([], limit), 0)


def _body(value: Mapping[str, Any]) -> bytes:
    eth1 = value["eth1_data"]
    sync = value["sync_aggregate"]
    return _container(
        [
            _fixed_bytes(value["randao_reveal"], 96),
            _container(
                [
                    _fixed_bytes(eth1["deposit_root"], 32),
                    _uint(eth1["deposit_count"]),
                    _fixed_bytes(eth1["block_hash"], 32),
                ]
            ),
            _fixed_bytes(value["graffiti"], 32),
            _empty_only_list(value["proposer_slashings"], 16, "proposer slashings"),
            _empty_only_list(value["attester_slashings"], 2, "attester slashings"),
            _composite_list(value["attestations"], 128, _attestation),
            _empty_only_list(value["deposits"], 16, "deposits"),
            _composite_list(value["voluntary_exits"], 16, _voluntary_exit),
            _container(
                [
                    _fixed_bytes(sync["sync_committee_bits"], 64),
                    _fixed_bytes(sync["sync_committee_signature"], 96),
                ]
            ),
            _execution_payload(value["execution_payload"]),
            _composite_list(
                value["bls_to_execution_changes"], 16, _bls_to_execution_change
            ),
            _bytes_list(value["blob_kzg_commitments"], 4096, 48),
        ]
    )


def beacon_block_root(value: Mapping[str, Any]) -> bytes:
    """Return the Deneb ``BeaconBlock`` hash-tree-root for a Beacon API object."""
    return _container(
        [
            _uint(value["slot"]),
            _uint(value["proposer_index"]),
            _fixed_bytes(value["parent_root"], 32),
            _fixed_bytes(value["state_root"], 32),
            _body(value["body"]),
        ]
    )


class DenebSignedBeaconBlock:
    """A lazy typed view over a Deneb Beacon API signed-block object."""

    __slots__ = ("_value", "_root", "_message_root")

    def __init__(self, value: Mapping[str, Any] | _SignedBlockJSON):
        self._value = value
        self._root: bytes | None = None
        self._message_root: bytes | None = None

    @classmethod
    def from_obj(cls, value: Mapping[str, Any]) -> "DenebSignedBeaconBlock":
        return cls(value)

    @classmethod
    def decode(cls, data: bytes | bytearray | memoryview) -> "DenebSignedBeaconBlock":
        envelope = _BLOCK_DECODER.decode(data)
        if envelope.version != "deneb":
            raise ValueError(f"expected a Deneb block, got {envelope.version!r}")
        return cls(envelope.data)

    @property
    def message(self) -> Mapping[str, Any]:
        return self._value["message"]

    @property
    def signature(self) -> str:
        return self._value["signature"]

    def message_hash_tree_root(self) -> bytes:
        if self._message_root is None:
            self._message_root = beacon_block_root(self.message)
        return self._message_root

    def hash_tree_root(self) -> bytes:
        if self._root is None:
            self._root = _container(
                [self.message_hash_tree_root(), _fixed_bytes(self.signature, 96)]
            )
        return self._root


def decode_deneb_block(data: bytes | bytearray | memoryview) -> DenebSignedBeaconBlock:
    return DenebSignedBeaconBlock.decode(data)
