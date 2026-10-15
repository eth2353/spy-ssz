# Architectural stage-two native performance validation

## Change and compatibility

Signed block-contents SSZ sizing/encoding now passes an explicit signed-child
node index into the Electra SPy encoder. It no longer temporarily replaces the
object's `root_node`. Existing root-based SPy entry points delegate to the new
index-based helpers, preserving their public CFFI ABI and wire behavior.

`bridge_signed_contents.c` and `bridge_block_header.c` are independently compiled
C modules for contents encoding and native header extraction. Their shared handle
types, child access, and internal hash declaration live in `bridge_internal.h`.
The existing subtree-hash entry point gains external linkage so the
header module can call it through a declared dependency; it remains absent from
the public CFFI API. The Merkle algorithm, cache behavior, and hash implementation
bodies are unchanged. Native object ownership remains in `bridge.c`.

No Python package APIs or schema/preset/projection behavior change in this
checkpoint. New C and header sources are covered by the existing source-distribution
manifest (`recursive-include src *.c *.h *.spy`) and explicit build source list.

## Verification and build identity

The native wheel was rebuilt through the normal isolated `uv build --wheel`
pipeline. All 495 tests passed, including 18 added cases spanning Electra/Fulu,
mainnet/minimal/gnosis presets, and zero/one/two nonempty proof/blob pairs. Repeated
signed contents encoding and fresh decoding preserve the signed graph root,
canonical JSON, SSZ bytes, and the original unsigned native header/root. Mainnet
cases also compare exact bytes and roots with the consensus remerkleable types.
Generated metadata verification and isolated installed-wheel smoke checks passed.

Both measured installations have the same 54 Python/stub/resource files as Python
checkpoint `e22a776`: baseline Python ASTs and exact non-Python bytes, candidate
exact bytes for every file. Both use Python 3.12.9, CFFI 2.1.1, msgspec 0.22.0,
and PyYAML 6.0.3 under isolated imports (`-I`).
Host: `macOS-26.6.2-arm64-arm-64bit`.

- Baseline extension SHA-256: `e0899916d7bb4021bbc1251aed2f975aef3d9702d1cad8a1356a9f13a80ec29d`.
- Baseline wheel SHA-256: `9d4e9aa5ee4810fa800cae1054268cfb7b69b08fdd14fb1c75e996e8ed1262c1`.
- Candidate extension SHA-256: `5b2919173392d961901a1816ada0c3518d7859fe9b47466c839cdc8b909fc6d1`.
- Candidate wheel SHA-256: `ae916d1c7eb037ff7480d72d505e86bb61471b359762b88dab3c3a795b6b5c47`.

The baseline is the retained installed candidate from the Python checkpoint;
its native extension is the accepted stage-one build. The candidate is the newly
rebuilt native wheel. Candidate identity verification also compares its installed
extension byte-for-byte with the checkout build and records hashes of all changed
native/build sources. Those sources were frozen before the build and timing runs.
Commit hooks subsequently removed one trailing blank line from each new C module
and reformatted a test expression; executable code remained unchanged. Recorded
native-source hashes describe the measured sources before that whitespace cleanup.

## Corpus and method

Used the restored 3,000-real-block corpus from the Python checkpoint without
changes: 1,000 signed beacon blocks each from mainnet Fulu, Hoodi Fulu, and Gloas,
all using the mainnet preset. Gloas excludes the separate execution payload
envelope. Original temporary corpus files were lost before the Python checkpoint;
the restoration used the same user-provided nodes/ranges with new provenance and
checksum metadata. Equality with the original lost manifest hashes is not claimed.

| Network | Source | Restored slot range |
| --- | --- | --- |
| mainnet | `http://validator-monitoring-mainnet:5555` | 15422933–15423936 |
| hoodi | `http://validator-monitoring-hoodi:5555` | 4140389–4141504 |
| gloas | `http://production-plataberget-serenita-cl-el-vc-1:5555` | 439360–440736 |

Three sequential baseline/candidate pairs used seeds 1040, 1041, and 1042, five
measured calls and two warmups per operation/block. Order rotated baseline/candidate,
candidate/baseline, baseline/candidate. No builds, tests, or other benchmarks
ran concurrently. Disk reads and verification are outside timed intervals. Decode
includes closing the new object; fresh hash excludes construction and closing.

For each network/slot/operation, take the median across the three pass medians.
P50/P99 use nearest ranks (indices 499/989 of 1,000 sorted per-block medians).
Aggregate change compares sums of the 1,000 block medians; mean delta divides the
sum difference by 1,000 blocks. Positive means slower. P99 measures workload-block
variation rather than production latency tails. These timings exercise real signed
beacon blocks; signed block-contents/header extraction correctness is covered by
the focused tests, and their performance is not established by this corpus.

## Results

| Network | Operation | Baseline P50 µs | Candidate P50 µs | Baseline P99 µs | Candidate P99 µs | Aggregate change | Mean delta µs/block |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mainnet | JSON decode | 702.667 | 698.042 | 1558.833 | 1548.083 | -0.14% | -1.048 |
| mainnet | SSZ decode | 14.083 | 13.959 | 21.750 | 21.542 | -0.77% | -0.109 |
| mainnet | JSON encode | 314.958 | 313.958 | 570.625 | 568.167 | -0.13% | -0.415 |
| mainnet | SSZ encode | 29.208 | 29.041 | 43.667 | 43.209 | -0.85% | -0.246 |
| mainnet | Fresh hash | 3686.792 | 3673.083 | 7494.375 | 7410.833 | -0.25% | -9.523 |
| mainnet | Cached hash | 2.083 | 2.042 | 2.209 | 2.167 | -1.82% | -0.038 |
| hoodi | JSON decode | 142.875 | 143.500 | 298.458 | 298.625 | -0.02% | -0.027 |
| hoodi | SSZ decode | 7.541 | 7.500 | 9.042 | 8.959 | -0.58% | -0.044 |
| hoodi | JSON encode | 150.042 | 150.000 | 213.000 | 208.333 | -0.10% | -0.162 |
| hoodi | SSZ encode | 14.375 | 14.292 | 26.083 | 25.958 | -0.57% | -0.085 |
| hoodi | Fresh hash | 561.291 | 560.292 | 976.375 | 982.666 | +0.02% | +0.097 |
| hoodi | Cached hash | 2.042 | 2.000 | 2.167 | 2.167 | -1.45% | -0.030 |
| gloas | JSON decode | 35.542 | 35.459 | 42.500 | 42.417 | -0.32% | -0.104 |
| gloas | SSZ decode | 5.792 | 5.709 | 6.167 | 6.125 | -1.41% | -0.081 |
| gloas | JSON encode | 42.000 | 42.083 | 46.458 | 46.541 | +0.17% | +0.063 |
| gloas | SSZ encode | 4.000 | 4.000 | 5.000 | 4.958 | -0.44% | -0.017 |
| gloas | Fresh hash | 87.166 | 87.125 | 105.333 | 105.500 | +0.00% | +0.001 |
| gloas | Cached hash | 2.083 | 2.042 | 2.209 | 2.208 | -1.21% | -0.025 |

The largest aggregate slowdown is Gloas JSON encoding at +0.17%, or +0.063
µs/block. Hoodi fresh hashing is +0.02% (+0.097 µs/block); Gloas fresh hashing
changes by +0.001 µs/block. All remaining aggregates range from -0.02% to -1.82%.
No material regression appears in this local comparison. Apparent improvements
are timing variation rather than demonstrated speedups from these changes.

All paired pass deltas are retained in `summary.json`. Hoodi JSON encoding varies
from +5.27% to -0.75% and -0.27%, while its aggregate median result is -0.10%.
Hoodi SSZ encoding pairs are +2.17%, -1.63%, and -1.53%; its aggregate is -0.57%.
This illustrates why single-pair results should not be treated as established
regressions or improvements. Median-per-block aggregation includes every pass and
block, without selecting or excluding measurements. The median aggregation can
differ from the aggregate of paired pass totals.

This is a local macOS ARM64 check; it does not establish Linux, sanitizer, or
other workload performance. The native checkpoint's separately compared baseline
is Python checkpoint `e22a776`; absolute times in this session are roughly 30% higher
than the earlier Python session despite using the same baseline environment.
Compare only paired runs within this native session; do not combine checkpoint
percentages or absolute timings to infer cumulative performance.

## Integrity and artifacts

All six native runs contain exactly 3,000 unique network/slot rows, 1,000 per
network: 18,000 verified timing rows. Each runner verifies JSON/SSZ file checksums,
canonical SSZ round trips, JSON/SSZ root equality, and JSON output decode root
equality. Aggregation verifies identical manifest identifiers, network/slot sets,
all 3,000 per-block roots, seeds, rounds/warmups, and complete positive measurements
for all six operations. Manifest/root sets also match the retained Python
checkpoint candidate measurements. No blocks were excluded and no codecs failed.

Restored manifest SHA-256 identifiers:

- `mainnet`: `d124ba051e177672ced2b8bc159fbe9e813a25528170d3fb3accbcb9d91cb3f3`.
- `hoodi`: `3eaa3142f8f17adff9ab3f1f02bc9ac8d3bbff31479f1c8fa5b0660f7b0bcdcd`.
- `gloas`: `9e2821d73ee478e71f45f7c8710bdbdfd7b8d0794b19b47ad773454d50816c80`.

Artifacts retained under `.deps/performance/stage-two-native/`:

- `candidate-env/` and `wheels/`: measured candidate installation and wheel.
- `baseline-identity.json`, `candidate-identity.json`: package/build identities.
- `results/baseline-{0,1,2}.json`, `results/candidate-{0,1,2}.json`, matching logs.
- `results/summary.json`, `results/summary.csv`: ranks, aggregate and per-pass totals.
- `run_benchmarks.py`, `summarize.py`, `verify_identity.py`: reproduction helpers.
- `candidate.patch`: tracked source diff at verification; new native files have
  their full SHA-256 identities in `candidate-identity.json`.

The build log and full test log are `.deps/performance/stage-two-native-build.log`
and `.deps/performance/stage-two-native-tests.log`. The retained baseline remains
in `.deps/performance/stage-two-python/candidate-env/` and corpus in
`.deps/performance/real-blocks/`. Raw artifacts are ignored local files; this report
is tracked.

## Reproduction

From the repository root, preserve existing results before repeating:

```bash
.deps/performance/stage-two-python/candidate-env/bin/python -I \
  .deps/performance/stage-two-native/verify_identity.py baseline
.deps/performance/stage-two-native/candidate-env/bin/python -I \
  .deps/performance/stage-two-native/verify_identity.py candidate
.deps/performance/stage-two-native/candidate-env/bin/python \
  .deps/performance/stage-two-native/run_benchmarks.py
.deps/performance/stage-two-native/candidate-env/bin/python \
  .deps/performance/stage-two-native/summarize.py
```

The runner invokes `benchmarks/benchmark_native.py` under each measured interpreter
with `-I`, the restored corpus, `--limit 1000 --rounds 5 --warmup 2`, each seed,
and separate output paths.
