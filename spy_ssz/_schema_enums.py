"""Generated from spy_ssz/schemas.yaml; do not edit."""

from enum import IntEnum


class Fork(IntEnum):
    PHASE0 = 0
    ALTAIR = 1
    BELLATRIX = 2
    CAPELLA = 3
    DENEB = 4
    ELECTRA = 5
    FULU = 6
    GLOAS = 7
    HEZE = 8


class ObjectKind(IntEnum):
    SIGNED_BEACON_BLOCK = 1
    BEACON_BLOCK = 2
    ATTESTATION = 3
    ATTESTATION_DATA = 4
    AGGREGATE_AND_PROOF = 5
    SYNC_COMMITTEE_CONTRIBUTION = 6
    CONTRIBUTION_AND_PROOF = 7
    BEACON_BLOCK_CONTENTS = 8
    SIGNED_BEACON_BLOCK_CONTENTS = 9
    BLINDED_BEACON_BLOCK = 10
    SIGNED_BLINDED_BEACON_BLOCK = 11
