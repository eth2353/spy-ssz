# postpy-ssz

This repository explores a compiled SPy backend for Ethereum SSZ. The native
path decodes Beacon API JSON or canonical SSZ bytes directly into a typed,
heap-owned C object graph;
Python receives only an opaque owner with metadata and `hash_tree_root()`.
The temporary JSON text and token table are freed before decoding returns, so
hashing performs no Python object traversal or JSON/hex parsing.

The reusable value graph supports unsigned integers, fixed bytes, byte lists,
bitlists, containers, and lists. It also implements progressive containers,
progressive lists, and progressive bitlists using the Gloas SSZ rules.

Implemented schemas in this proof:

- Deneb `SignedBeaconBlock`: JSON and SSZ input
- Deneb `Attestation`: JSON and SSZ input
- Electra `SignedBeaconBlock`: JSON and SSZ input
- Fulu `SignedBeaconBlock`: reuses the Electra codec with Fulu metadata
- Gloas progressive `Attestation`: JSON and SSZ input

The generated catalog defines every named mainnet SSZ type in
`eth-consensus-specs` 1.7.0a12 for Electra (92), Fulu (103), Gloas (121), and
Heze (123).
Nested anonymous list/vector shapes are normalized and referenced by type id.
Run `tools/generate_consensus_types.py` after changing the consensus-specs
version.

## Architecture

- `native/json_parser.spy`: temporary, replaceable JSON tokenizer
- `native/ssz_reader.spy`: bounds-checked native SSZ input
- `native/ssz_object.spy`: typed nodes, native storage, SSZ hashing, root cache
- `native/native_writer.spy`: allocation-free JSON and SSZ output primitives
- `native/schema_*.spy`: fork/object-specific codecs
- `native/bridge.c`: narrow ownership and CFFI bridge
- `postpy_ssz/native_object.py`: opaque ownership and `(fork, kind)` registry
- `postpy_ssz/consensus_types.json`: generated Electra-through-Heze definitions
- `postpy_ssz/native_*.py`: concrete public types and decoder registration

`msgspec` remains the Python comparison decoder. Its public JSON API constructs
Python objects, and it does not currently publish a stable C decoder API that
can populate SPy-owned structs. The native tokenizer is isolated specifically
so it can later be replaced by a supported msgspec C API (or another parser)
without changing the SSZ representation.

Fork identifiers follow consensus chronology: Phase0 is `0`, Altair is `1`,
Bellatrix is `2`, Capella is `3`, Deneb is `4`, and subsequent forks continue
in order.

## Native API

```python
from postpy_ssz.native_electra import NativeElectraBlock

block_from_json = NativeElectraBlock.from_json(json_bytes)
block_from_ssz = NativeElectraBlock.from_ssz(ssz_bytes)

assert block_from_json.hash_tree_root() == block_from_ssz.hash_tree_root()
assert block_from_json.to_ssz() == ssz_bytes
beacon_api_json = block_from_ssz.to_json()
block_from_json.close()
block_from_ssz.close()
```

The generic entry points are `decode_native_json(data, fork, kind)` and
`decode_native_ssz(data, fork, kind)`. Native JSON and SSZ output encoding is
available for Electra and Fulu signed blocks; Fulu reuses the unchanged Electra
block schema.

## Build

SPy's wheel does not include the `libspy` C sources, so the build needs a pinned
source checkout:

```bash
git clone https://github.com/spylang/spy.git .deps/spy
git -C .deps/spy checkout 012ae501eb6a0adc3baff261c97ec9b56c80c2d1
uv sync
uv run python tools/build_native.py --spy-root .deps/spy
```

The build compiles the optimized SPy runtime and emits a narrow CFFI extension
in `postpy_ssz/`.

## Verify and benchmark

```bash
uv run python -m pytest -q
uv run python -m benchmarks.benchmark_corpus \
  /Users/luca/Downloads/eth-blocks/beacon_blocks
```

The corpus benchmark discovers paired or standalone `.json`, `.ssz`, `.bin`,
and `.ssz_snappy` blocks, measures JSON/SSZ encode and decode separately, and
prints all-fork and per-fork p50, p95, total time, and throughput. Use
`--csv timings.csv` for per-block results, `--limit` for a quick sample, or
`--fork deneb` when a synthetic/standalone file cannot be identified from its
metadata, path, or slot. Available native Deneb, Electra, and Fulu decode
timings are included, along with native Electra/Fulu JSON and SSZ encode timings;
pass `--no-native` to measure only the consensus-spec codecs.

On a 592-block Fulu corpus, representative p50 results were 0.901 ms for native
JSON decode, 0.451 ms for native JSON encode, 0.269 ms for native SSZ decode,
and 0.491 ms for native SSZ encode. The corresponding consensus-spec codec
operations took 7.696, 15.067, 7.885, and 17.085 ms.

The sample roots match the official consensus types:

- block: `0x784dad99478a2ca8fd04615fb530290655b41f49896e90146318ecec9fbd31e7`
- signed block: `0x036ead785909b45549a62c13f1617a3d84e686a0db3dc29e3b0b9a2a410a0821`

This is still a proof of concept, not a complete `eth-remerkleable`
replacement. Electra+ definitions are complete, but executable native codecs
must still be connected for the remaining non-block cataloged types.
Generalized-index views and mutation APIs also remain to be implemented.
