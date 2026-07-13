"""Canonical consensus preset resources and their loading boundary."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

import yaml


# These identifiers are spy-ssz ABI metadata, not part of the canonical files.
PRESET_IDS = {
    "mainnet": 0,
    "minimal": 1,
    "gnosis": 2,
}

# Values currently consumed by the compiled codecs. Their values always come
# from the canonical YAML resources.
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


def _load_directory(directory: Traversable) -> dict[str, Any]:
    values: dict[str, Any] = {}
    sources: dict[str, str] = {}
    resources = sorted(
        (
            resource
            for resource in directory.iterdir()
            if resource.name.endswith(".yaml")
        ),
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
def preset_sources() -> dict[str, dict[str, Any]]:
    """Load and merge the canonical fork files for every supported preset."""
    directory = files(__package__)
    result = {
        name.upper(): _load_directory(directory.joinpath(name)) for name in PRESET_IDS
    }
    for name, values in result.items():
        missing = set(SSZ_LIMIT_KEYS).difference(values)
        if missing:
            raise ValueError(
                f"{name.lower()} preset is missing: {', '.join(sorted(missing))}"
            )
    return result
