# spy-ssz

`spy-ssz` is a compiled Ethereum SSZ library for Python 3.12 and newer. It decodes
Beacon API JSON and canonical SSZ directly into SPy-owned C object graphs, so
hashing and encoding do not traverse ordinary Python objects.

This is currently a proof of concept focused on the operations needed by
validator clients. It is not yet a complete replacement for
`eth-remerkleable`; see [Current scope](#current-scope).

## Install

Install directly from Git with [uv](https://docs.astral.sh/uv/):

```bash
uv add 'spy-ssz @ git+https://github.com/eth2353/spy-ssz.git@REVISION'
```

The package builds a platform-specific C extension during installation. For
local development, set `SPY_ROOT` to reuse an existing SPy checkout:

```bash
SPY_ROOT=/path/to/spy uv sync
```

Without `SPY_ROOT`, the build uses `.deps/spy` when present or checks out the
pinned SPy revision in a temporary directory.

## Quick start

Import the class for the fork, object, and preset you are decoding. The
mainnet Electra signed-block class accepts the standard Beacon API
`{"data": ...}` JSON envelope:

```python
from spy_ssz import ElectraSignedBeaconBlock

with ElectraSignedBeaconBlock.from_json(response.content) as block:
    root: bytes = block.hash_tree_root()
    canonical_ssz: bytes = block.to_ssz()
    beacon_api_json: bytes = block.to_json()

    print(block.message.slot)
    print(root.hex())
```

Decode canonical SSZ into the same object type:

```python
from spy_ssz import ElectraSignedBeaconBlock

with ElectraSignedBeaconBlock.from_ssz(ssz_bytes) as block:
    assert block.to_ssz() == ssz_bytes
    print(block.hash_tree_root().hex())
```

Objects own compiled memory. Prefer a context manager as shown above, or call
`close()` explicitly. Accessing a closed object raises `RuntimeError`.

## Presets

Mainnet is the default. Minimal and Gnosis use explicit class suffixes:

```python
from spy_ssz import (
    ElectraSignedBeaconBlock,
    ElectraSignedBeaconBlockGnosis,
    ElectraSignedBeaconBlockMinimal,
)

mainnet_block = ElectraSignedBeaconBlock.from_ssz(mainnet_ssz)
minimal_block = ElectraSignedBeaconBlockMinimal.from_ssz(minimal_ssz)
gnosis_block = ElectraSignedBeaconBlockGnosis.from_ssz(gnosis_ssz)
```

The canonical YAML files under `spy_ssz/presets/<preset>/` are the source of
truth for preset-dependent consensus limits. `load_preset()` exposes the
limits used by the compiled codecs:

```python
from spy_ssz import Preset, load_preset

config = load_preset(Preset.MINIMAL)
assert config.sync_committee_size == 32
```

## Generic decoding

When the concrete class is selected dynamically, use the generic registry:

```python
from spy_ssz import Fork, ObjectKind, Preset, decode_json, decode_ssz

from_json = decode_json(
    json_bytes,
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    Preset.MAINNET,
)
from_ssz = decode_ssz(
    ssz_bytes,
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    Preset.MAINNET,
)

try:
    assert from_json.hash_tree_root() == from_ssz.hash_tree_root()
finally:
    from_json.close()
    from_ssz.close()
```

## Validator-client objects

Electra signing objects accept bare JSON objects rather than a Beacon API
`data` envelope. They support JSON, SSZ, Python-object conversion, field
projection, and tree hashing:

```python
from spy_ssz import AttestationData

with AttestationData.from_obj(
    {
        "slot": "123",
        "index": "0",
        "beacon_block_root": "0x" + "00" * 32,
        "source": {"epoch": "2", "root": "0x" + "11" * 32},
        "target": {"epoch": "3", "root": "0x" + "22" * 32},
    }
) as data:
    wire_bytes = data.to_ssz()
    root = data.hash_tree_root()
```

Available signing classes are:

- `AttestationData`
- `Attestation`
- `AggregateAndProof`
- `SignedAggregateAndProof`
- `SingleAttestation`
- `SyncCommitteeContribution`
- `SyncCommitteeMessage`
- `ContributionAndProof`
- `SignedContributionAndProof`
- `IndexedAttestation`
- `AttesterSlashing`
- `BeaconBlockHeader`
- `SignedBeaconBlockHeader`
- `ProposerSlashing`

Each also has `Minimal` and `Gnosis` variants, such as
`AttestationMinimal` and `AttestationGnosis`.

## Block contents and blinded blocks

Electra block-container types provide helpers used during block proposal:

```python
from spy_ssz import ElectraBeaconBlockContentsMainnet

with ElectraBeaconBlockContentsMainnet.from_json(response.content) as contents:
    header = contents.header_dict()
    block_root = contents.block_hash_tree_root()

    signed = contents.sign(bls_signature)
    try:
        publish_body = signed.to_json()
        publish_ssz = signed.to_ssz()
    finally:
        signed.close()
```

The corresponding blinded types are `ElectraBlindedBeaconBlockMainnet` and
`ElectraSignedBlindedBeaconBlockMainnet`. Minimal and Gnosis variants use the
same suffix convention.

## API summary

All concrete objects inherit from `SszObject` and expose:

- `from_json(bytes)`, `from_ssz(bytes)`, and `from_obj(value)`
- `hash_tree_root() -> bytes`
- `to_json() -> bytes`, `to_ssz() -> bytes`, and `to_obj()` when an encoder is
  implemented for that schema
- immutable attribute projection such as `block.message.slot` for schemas with
  JSON output support
- `fork`, `object_kind`, `preset`, `schema_id`, and `node_count` metadata
- `close()` and context-manager ownership

## Current scope

| Fork/object | JSON decode | SSZ decode | JSON encode | SSZ encode |
| --- | ---: | ---: | ---: | ---: |
| Deneb `SignedBeaconBlock` | yes | yes | no | no |
| Deneb `Attestation` | yes | yes | no | no |
| Electra `SignedBeaconBlock` | yes | yes | yes | yes |
| Fulu `SignedBeaconBlock` | yes | yes | yes | yes |
| Electra signing objects | yes | yes | yes | yes |
| Electra block contents and blinded blocks | yes | yes | yes | yes |

Fulu blocks reuse the unchanged Electra block layout with Fulu metadata.
The generated type catalog covers every named mainnet SSZ type in
`eth-consensus-specs` 1.7.0a12 for Electra and Fulu, but most cataloged types
do not yet have executable codecs.

Generalized-index views and mutation APIs are also not implemented yet.

## Architecture and sources of truth

- `spy_ssz/schemas.yaml` defines fork IDs, object-kind IDs, schema IDs, codec
  modules, supported presets, and public type names.
- `spy_ssz/presets/<preset>/*.yaml` contains canonical preset definitions
  copied from the consensus specification repositories.
- `tools/generate_spy_metadata.py` derives Python, SPy, and C constants from
  those definitions during builds.
- `src/ssz_object.spy` owns typed nodes, SSZ hashing, and the root cache.
- `src/json_parser.spy` and `src/ssz_reader.spy` decode JSON and SSZ input.
- `src/writer.spy` provides JSON and SSZ output primitives.
- `src/schema_*.spy` implements concrete fork/object codecs.
- `src/bridge.c` is the ownership and CFFI boundary.
- `spy_ssz/ssz.py` owns Python lifetimes and codec dispatch.

Fork identifiers follow consensus chronology: Phase0 is `0`, Altair is `1`,
Bellatrix is `2`, Capella is `3`, Deneb is `4`, Electra is `5`, and Fulu is
`6`.

## Development and benchmarks

Run the full checks:

```bash
uvx pre-commit run --all-files
uv run python -m pytest -q
```

Benchmark a directory containing raw `.json`, `.ssz`, or `.bin` blocks:

```bash
uv run python -m benchmarks.benchmark_corpus \
  /Users/luca/Downloads/eth-blocks/beacon_blocks
```

Use `--csv timings.csv` for per-block results, `--limit` for a quick sample,
`--fork deneb` when a standalone file's fork cannot be inferred, or `--no-spy`
to measure only the consensus-spec codecs.

On a 592-block Fulu corpus, representative p50 results were 0.901 ms for SPy
JSON decode, 0.451 ms for SPy JSON encode, 0.269 ms for SPy SSZ decode, and
0.491 ms for SPy SSZ encode. The corresponding consensus-spec operations took
7.696, 15.067, 7.885, and 17.085 ms.
