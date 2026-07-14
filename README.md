# spy-ssz

`spy-ssz` is a compiled Ethereum SSZ library for Python 3.12 and newer. It decodes
Beacon API JSON and canonical SSZ directly into [SPy](https://github.com/spylang/spy)-owned C object graphs, so
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
local development, set `SPY_ROOT` to reuse an existing [SPy](https://github.com/spylang/spy) checkout:

```bash
SPY_ROOT=/path/to/spy uv sync
```

Without `SPY_ROOT`, the build uses `.deps/spy` when present or checks out the
pinned [SPy](https://github.com/spylang/spy) revision in a temporary directory.

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
from spy_ssz import Fork, ObjectKind, Preset, decode_json, decode_ssz, get_ssz_type

block_type = get_ssz_type(
    Fork.ELECTRA,
    ObjectKind.SIGNED_BEACON_BLOCK,
    Preset.GNOSIS,
)

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

Fulu requests always resolve to dedicated Fulu concrete classes, even where the
wire schema is unchanged from Electra. The shared codec records Fulu as the
logical fork and uses the Fulu schema ID, so class identity, object metadata,
construction, and diagnostics all agree with the requested fork.

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

Compatible typed children can be passed directly to the common composition
containers. The child graph is cloned natively, so this does not encode or
decode JSON and the resulting parent owns its memory independently:

```python
aggregate_and_proof = AggregateAndProof(
    aggregator_index=validator_index,
    aggregate=attestation,
    selection_proof=selection_proof,
)
signed = SignedAggregateAndProof(
    message=aggregate_and_proof,
    signature=signature,
)
```

This native path also covers `ContributionAndProof`,
`SignedContributionAndProof`, and `SingleAttestation`. Other constructor shapes
retain the existing JSON-compatible fallback.

Publication batches of same-type bare-object values can be encoded into one
output buffer:

```python
from spy_ssz import encode_json_array

request_body = encode_json_array(attestations)
```

The iterable is materialized to retain object ownership during encoding, but
individual `to_json()` byte strings are not allocated.

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
| Electra `SignedBeaconBlock` | yes | yes | yes | yes |
| Fulu `SignedBeaconBlock` | yes | yes | yes | yes |
| Electra signing objects | yes | yes | yes | yes |
| Fulu signing objects | yes | yes | yes | yes |
| Electra block contents and blinded blocks | yes | yes | yes | yes |
| Fulu block contents and blinded blocks | yes | yes | yes | yes |

Fulu types reuse the unchanged Electra wire layouts with Fulu class identity,
schema IDs, and object metadata.
The generated type catalog covers every named mainnet SSZ type in
`eth-consensus-specs` 1.7.0a12 for Electra and Fulu, but most cataloged types
do not yet have executable codecs.

Generalized-index views and mutation APIs are also not implemented yet.

JSON and SSZ inputs are limited to 715,822,421 bytes. This keeps the largest
native arena-capacity calculation within the signed 32-bit positions and
offsets used by the compiled decoder. Larger inputs are rejected at the Python
boundary before native decoding.

JSON decoding rejects duplicate and unrecognized object fields. Standard
endpoint-specific Beacon API response metadata is recognized alongside the
required `data` field; metadata from a different endpoint is rejected.

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

Check the implemented Electra and Fulu codecs against extracted
`consensus-specs` SSZ static vectors:

```bash
uv run --with python-snappy python tools/check_consensus_vectors.py \
  /path/to/consensus-spec-tests
```

The path may be the extraction root containing `tests/minimal` and
`tests/mainnet`, or the `tests` directory itself. Use `--preset minimal` or
`--preset mainnet` to check only one preset. The runner verifies SSZ decode,
canonical re-encoding, and hash-tree roots for every vector matching an
implemented Electra or Fulu codec.

The upstream archives are hundreds of megabytes, so this check is intended for
scheduled or release CI rather than the per-commit pre-commit suite.

Benchmark a directory containing raw `.json`, `.ssz`, or `.bin` blocks:

```bash
uv run python -m benchmarks.benchmark_corpus \
  /tmp/beacon_blocks
```

Use `--csv timings.csv` for per-block results, `--limit` for a quick sample,
`--fork electra` or `--fork fulu` when a standalone file's fork cannot be
inferred, or `--no-spy` to measure only the consensus-spec codecs.

### Performance

The following results use 100 consecutive canonical Ethereum mainnet Fulu
signed beacon blocks, covering every slot from **14,762,749 through
14,762,848**, inclusive. The corpus contains 35.56 MiB of Beacon API JSON and
17.75 MiB of SSZ data.

The benchmark ran on an Apple M1 with macOS 13.2.1 (`arm64`), Python 3.12.9,
and Rust 1.92.0. `spy-ssz` was compiled with Clang 19 using `-O3` and LTO;
the Rust implementations were compiled in release mode. Implementations ran
sequentially to avoid contention. The measured revisions were `spy-ssz`
`eeee194`, Grandine `94e8ad1` (the pre-Zisk revision used by the harness),
`libssz` `f4d682b`, and Lighthouse `120c3c6`.

For each block and operation, the harness performed one unmeasured warmup and
five measured runs, then retained the median. The table reports the median
(p50) and 95th percentile (p95) across those 100 per-block medians. File reads
and initial corpus preparation were outside the timed region. Decode timings
include construction of the typed block; encode timings start with an already
decoded block and include producing the output byte buffer. JSON measurements
include the Beacon API `{"data": ...}` wrapper.

Hash-tree-root measurements were cold: roots were recomputed without using a
previously populated object-root cache. Before timing, the harnesses checked
exact SSZ byte round trips. `spy-ssz` roots were also checked against the
consensus-spec implementation for all 100 blocks, and the JSON-capable Rust
harnesses checked that JSON and SSZ decoding produced the same root.

Times below are **p50 ms (p95 ms)**.

| Implementation | SSZ decode | SSZ encode | Cold hash-tree root |
| --- | ---: | ---: | ---: |
| `spy-ssz` | **0.023 (0.056)** | 0.022 (0.040) | 3.195 (7.471) |
| Grandine SSZ | 0.026 (0.063) | 0.015 (0.025) | 5.046 (11.741) |
| `libssz` | 0.029 (0.069) | **0.009 (0.020)** | 6.249 (13.752) |
| Lighthouse `ethereum_ssz` | 0.223 (0.331) | 0.118 (0.234) | **3.081 (6.356)** |

| Implementation | JSON decode | JSON encode |
| --- | ---: | ---: |
| `spy-ssz` | 0.617 (1.113) | 0.246 (0.416) |
| Grandine SSZ | **0.122 (0.208)** | **0.170 (0.344)** |
| Lighthouse | 1.299 (2.140) | 0.902 (1.655) |

`libssz` is omitted from the JSON table because the benchmark consensus types
do not implement Ethereum JSON serde. Lodestar-z is not included because its
public bindings do not expose a standalone signed-beacon-block codec and root
operation.

For this corpus, `spy-ssz`, Grandine, and `libssz` have SSZ codec performance
in the same general range. `spy-ssz` had the fastest SSZ decode, while Grandine
and `libssz` encoded SSZ faster. `spy-ssz` decoded and encoded SSZ faster than
Lighthouse's `ethereum_ssz`; their cold hash-tree-root measurements were
similar, with Lighthouse slightly faster in this run. Grandine remained the
fastest JSON implementation, while `spy-ssz` JSON encoding narrowed the gap
to roughly 1.4x.

These numbers describe this corpus and machine rather than every SSZ schema or
workload. In particular, list sizes, execution-payload contents, allocator
behavior, and compiler settings can materially change the result. The corpus
benchmark above can be used to reproduce the same methodology on another
machine or dataset.
