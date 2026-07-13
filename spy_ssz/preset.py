"""Consensus-preset selection for SPy SSZ schemas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from importlib.resources import files
from typing import Any

import yaml


# Preset identifiers are part of spy-ssz's ABI, not the canonical consensus
# preset definitions. Keep them here rather than adding project metadata to the
# copied YAML files.
_PRESET_IDS = {
    "mainnet": 0,
    "minimal": 1,
    "gnosis": 2,
}

# Only values consumed by the compiled codecs are exposed through PresetConfig
# and generated into SPy. The canonical files remain the source for the values.
SSZ_LIMIT_KEYS = (
    "MAX_COMMITTEES_PER_SLOT",
    "MAX_VALIDATORS_PER_COMMITTEE",
    "SYNC_COMMITTEE_SIZE",
    "MAX_PROPOSER_SLASHINGS",
    "MAX_ATTESTER_SLASHINGS",
    "MAX_ATTESTER_SLASHINGS_ELECTRA",
    "MAX_ATTESTATIONS",
    "MAX_ATTESTATIONS_ELECTRA",
    "MAX_DEPOSITS",
    "MAX_VOLUNTARY_EXITS",
    "MAX_WITHDRAWALS_PER_PAYLOAD",
    "MAX_BLS_TO_EXECUTION_CHANGES",
    "MAX_BLOB_COMMITMENTS_PER_BLOCK",
    "FIELD_ELEMENTS_PER_BLOB",
    "MAX_TRANSACTIONS_PER_PAYLOAD",
    "MAX_BYTES_PER_TRANSACTION",
    "MAX_DEPOSIT_REQUESTS_PER_PAYLOAD",
    "MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD",
    "MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD",
)


def _load_directory(directory: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    sources: dict[str, str] = {}
    resources = sorted(
        (resource for resource in directory.iterdir() if resource.name.endswith(".yaml")),
        key=lambda resource: resource.name,
    )
    if not resources:
        raise ValueError(f"preset directory {directory} contains no YAML files")
    for resource in resources:
        document = yaml.safe_load(resource.read_text())
        if not isinstance(document, dict):
            raise ValueError(f"{resource} must contain a mapping")
        for key, value in document.items():
            if key in values:
                raise ValueError(
                    f"duplicate preset key {key} in {sources[key]} and {resource.name}"
                )
            values[key] = value
            sources[key] = resource.name
    return values


@lru_cache(maxsize=1)
def _sources() -> dict[str, dict[str, Any]]:
    directory = files(__package__).joinpath("presets")
    result = {
        name.upper(): _load_directory(directory.joinpath(name))
        for name in _PRESET_IDS
    }
    for name, values in result.items():
        missing = set(SSZ_LIMIT_KEYS).difference(values)
        if missing:
            raise ValueError(
                f"{name.lower()} preset is missing: {', '.join(sorted(missing))}"
            )
    return result


Preset = IntEnum(
    "Preset",
    {name.upper(): identifier for name, identifier in _PRESET_IDS.items()},
    module=__name__,
)


@dataclass(frozen=True, slots=True)
class PresetConfig:
    preset: Preset
    max_committees_per_slot: int
    max_validators_per_committee: int
    sync_committee_size: int
    max_proposer_slashings: int
    max_attester_slashings: int
    max_attester_slashings_electra: int
    max_attestations: int
    max_attestations_electra: int
    max_deposits: int
    max_voluntary_exits: int
    max_withdrawals_per_payload: int
    max_bls_to_execution_changes: int
    max_blob_commitments_per_block: int
    field_elements_per_blob: int
    max_transactions_per_payload: int
    max_bytes_per_transaction: int
    max_deposit_requests_per_payload: int
    max_withdrawal_requests_per_payload: int
    max_consolidation_requests_per_payload: int


def load_preset(preset: Preset | str) -> PresetConfig:
    if isinstance(preset, str):
        preset = Preset[preset.upper()]
    values = _sources()[preset.name]
    return PresetConfig(
        preset=preset,
        **{key.lower(): int(values[key]) for key in SSZ_LIMIT_KEYS},
    )
