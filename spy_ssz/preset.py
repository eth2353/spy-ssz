"""Consensus-preset selection for SPy SSZ schemas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from importlib.resources import files
from typing import Any

import yaml


@lru_cache(maxsize=1)
def _sources() -> dict[str, dict[str, Any]]:
    directory = files(__package__).joinpath("presets")
    result = {}
    for resource in directory.iterdir():
        if resource.name.endswith(".yaml"):
            result[resource.name.removesuffix(".yaml").upper()] = yaml.safe_load(
                resource.read_text()
            )
    return result


Preset = IntEnum(
    "Preset",
    {
        name: int(values["PRESET_ID"])
        for name, values in sorted(
            _sources().items(), key=lambda item: int(item[1]["PRESET_ID"])
        )
    },
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
        **{
            key.lower(): int(value)
            for key, value in values.items()
            if key != "PRESET_ID"
        },
    )
