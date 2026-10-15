# Architectural stage-three projection validation

## Change and compatibility

Consensus-backed field reads now copy only the selected native subtree into
Python-owned metadata and payload buffers, then construct the existing immutable
projection dataclasses, tuples, integers, and bytes from the authoritative
consensus catalog. Generated field/index/type mappings come from
`tools/generate_spy_metadata.py`, `schemas.yaml`, and `consensus_types.json`.
The public JSON projection helper retains support for named catalog types without
registered native codecs through a cached descriptor fallback.

The private `bridge_projection.c` module performs selected-subtree sizing and
copying in two CFFI calls, independently of subtree node count. Copied preorder
records describe node kinds, payload lengths, child counts, and packed integer
widths. A separate copied payload buffer preserves full uint256 storage and
canonical bitlist termination. No borrowed pointers or additional native owners
escape the bridge. Buffer capacities, size overflow, invalid field indices, and
complete metadata/payload consumption are checked.

Each owner lazily caches completed immutable field snapshots. Repeated reads
reuse those snapshots while still requiring a live owner. Closing clears the
cache; already returned values remain independent and usable. One owner lock
covers sizing, copying, projection construction, and cache publication, preserving
concurrent-close safety. Python copies retain independent native ownership and
projection caches. Canonical SSZ, hashing, JSON envelopes, presets, public
projection classes, aliases, and module identities remain unchanged.

API-only block containers without consensus catalog descriptors retain their
existing JSON-backed attribute access. `to_obj()` still uses the detached,
canonical JSON-backed object representation. This stage does not introduce a
schema compiler or replace the wire parsers.

## Verification and build identity

The normal pinned `uv build` pipeline produced the source distribution and wheel.
All 529 tests passed against the final native extension, including schema-wide
native-versus-JSON projection equivalence on both mainnet and minimal;
Electra/Fulu/Gloas bitlists of lengths 0, 8, and 9 on all three presets;
nonempty packed uint64 lists containing 2**64-1; nested full-width uint256;
projection cache/copy/close behavior; invalid field and buffer bounds; and
concurrent close during projection. Existing populated Gloas envelope tests also
cover progressive containers, lists, withdrawals, and byte payloads.

Generated metadata verification, touched-file Ruff checks, and isolated
installed-wheel package smoke checks passed. Both distributions include the new
runtime and independently compiled C source through the existing package and
source-distribution rules.

The baseline is the retained installed native stage-two candidate at commit
`86f7c82`. Its 54 Python/stub/resource files were checked against that commit.
The candidate has 55 Python/stub/resource files checked against the working tree.
Python files use AST equivalence to permit formatting-only changes; other resource
files use exact bytes. During measurement verification, the measured wheel,
installed candidate, and checkout native extension bytes matched exactly. `uv build` builds its wheel from an isolated source-distribution
tree, so its verified extension was copied into the ignored checkout extension
before the final development test run.

Both installations use Python 3.12.9, CFFI 2.1.1, msgspec 0.22.0, and PyYAML 6.0.3.
Validation and timings ran locally on macOS ARM64. Linux builds and ASan/UBSan
checks were not run locally; those remain covered by the configured CI jobs.
Identity records include interpreter and package paths, wheel/native hashes,
source/resource hashes, and native/build source hashes.

After timing, commit checks normalized generated mapping string quotes and
added precise private mapping declarations to `projections.pyi`. The generator
now emits formatter-stable quotes and those declarations. All 21 runtime Python
ASTs still match the measured candidate; these changes affect source formatting
and static typing only. The measured wheel/environment and their identity
records remain retained unchanged.

## Corpus and method

The retained 3,000-real-block corpus is unchanged: 1,000 signed beacon blocks each
from mainnet Fulu, Hoodi Fulu, and Gloas, all using the mainnet preset. Gloas blocks
exclude their separate execution payload envelope. Manifest identities are checked
against the accepted stage-two native run; no equality with an earlier lost
corpus is claimed.

For codecs/hashing and separately for field access, three sequential pairs use
seeds 1040, 1041, and 1042, five measured calls and two warmups per operation/block.
Order rotates baseline/candidate, candidate/baseline, baseline/candidate. All runs
use the retained installed interpreters with `-I` and absolute benchmark script
paths. No builds, tests, or other benchmark runs execute concurrently.

The codec harness checks both input checksums, canonical SSZ equality, JSON decode
roundtrips, JSON/SSZ hash-root equality, and per-block root agreement across
both builds outside timing. Independent consensus hash comparisons are covered
by the test suite. The field harness
checks SSZ input checksums and complete `.message` equality against the existing
JSON projection path, recording a stable digest of the full projected message
for comparison across all six field passes. It measures first and repeated reads
of signatures, complete messages, a nested message field, a scalar on a small
AttestationData object, and that object's nested checkpoint. Each first-read
sample uses a fresh native owner; decoding, close, warmup, result destruction,
verification, and disk reads are outside timed intervals. Repeated reads warm
that exact field/path on the same owner before timing.

For each network/slot/operation, take the median across the three pass medians.
P50/P99 use nearest ranks at indices 499/989 of 1,000 sorted per-block medians.
Aggregate changes compare sums of the 1,000 block medians. Mean deltas divide
that sum difference by 1,000. Absolute timings depend on the session; conclusions
use the paired runs below.

## Preliminary traversal correction

An initial 20-block-per-network smoke comparison found that crossing CFFI for
each node materially regressed first access to Gloas messages (+62%). That
implementation was replaced with copied subtree metadata/payload batching before
the comprehensive runs. Its raw smoke data is retained and is not included in
the final results. A second paired smoke confirmed first-message improvements
on mainnet/Hoodi and reduced the Gloas difference to approximately 11 microseconds;
the final reader also avoids per-node imports and unused C struct field reads.

## Final paired results

All six codec runs and all six field runs completed: 36,000 block rows, 3,000
matching roots against the accepted stage-two baseline, and 3,000 matching full
projection digests across all six field passes. Every manifest, block count,
seed, operation set, and warmup/round setting matched the protocol.

Codec/hash table entries are baseline → candidate P50/P99 in microseconds.
The change column compares summed per-block medians, not the displayed quantiles.

| Network | Operation | Baseline P50/P99 µs | Candidate P50/P99 µs | Aggregate change | Mean delta µs/block |
| --- | --- | ---: | ---: | ---: | ---: |
| mainnet | json_decode | 534.208/1224.167 | 532.667/1196.667 | -0.50% | -2.850 |
| mainnet | ssz_decode | 10.709/16.583 | 10.750/16.750 | +0.06% | +0.007 |
| mainnet | json_encode | 239.500/452.833 | 238.917/431.291 | -0.50% | -1.248 |
| mainnet | ssz_encode | 22.166/34.375 | 22.167/34.292 | -0.34% | -0.074 |
| mainnet | hash_cold | 2824.417/5734.416 | 2783.000/5683.500 | -1.48% | -42.667 |
| mainnet | hash_cached | 1.583/1.709 | 1.542/1.667 | -1.60% | -0.025 |
| hoodi | json_decode | 109.625/231.000 | 108.708/229.041 | -0.90% | -1.103 |
| hoodi | ssz_decode | 5.709/7.084 | 5.708/7.000 | -0.70% | -0.041 |
| hoodi | json_encode | 115.417/159.458 | 114.542/162.958 | -0.74% | -0.886 |
| hoodi | ssz_encode | 11.000/19.667 | 10.958/19.958 | -0.40% | -0.045 |
| hoodi | hash_cold | 428.625/745.583 | 424.917/738.417 | -1.37% | -6.084 |
| hoodi | hash_cached | 1.583/1.708 | 1.542/1.667 | -1.60% | -0.025 |
| gloas | json_decode | 27.167/32.625 | 26.917/32.083 | -1.25% | -0.314 |
| gloas | ssz_decode | 4.416/4.791 | 4.333/4.667 | -1.65% | -0.071 |
| gloas | json_encode | 32.125/36.334 | 32.000/35.666 | -0.93% | -0.265 |
| gloas | ssz_encode | 3.083/3.833 | 3.000/3.791 | -1.82% | -0.056 |
| gloas | hash_cold | 66.792/81.792 | 66.084/79.959 | -1.22% | -0.746 |
| gloas | hash_cached | 1.584/1.750 | 1.583/1.708 | -1.83% | -0.029 |

There is no material codec/hash regression. Mainnet SSZ decode changes by
+0.06% (+0.007 microseconds per block); all other aggregate changes range from
-0.34% to -1.83%. The implementation does not change the hashing algorithm, so
these small codec/hash differences should be treated as measurement variation.

Field entries below are average microseconds per block, computed from the sums
of the three-pass per-block medians. “Repeated” warms the same field/path before
timing. `.message` and the nested path both copy the complete top-level message
on first access; the nested path then reads `.body.randao_reveal`. Small scalar
and checkpoint cases use AttestationData with the real block slot.

| Network | Field/path | First baseline → candidate µs | First change | Repeated baseline → candidate µs | Repeated change |
| --- | --- | ---: | ---: | ---: | ---: |
| mainnet | signature | 435.710 → 4.777 | -98.90% | 5.948 → 1.115 | -81.26% |
| mainnet | message | 840.851 → 361.068 | -57.06% | 405.494 → 1.246 | -99.69% |
| mainnet | message.body.randao_reveal | 845.624 → 360.003 | -57.43% | 410.142 → 1.198 | -99.71% |
| mainnet | small.slot | 11.700 → 4.456 | -61.91% | 5.702 → 1.141 | -79.99% |
| mainnet | small.source | 12.635 → 6.001 | -52.50% | 6.986 → 1.109 | -84.12% |
| hoodi | signature | 238.596 → 4.642 | -98.05% | 5.917 → 1.115 | -81.15% |
| hoodi | message | 422.505 → 214.419 | -49.25% | 188.957 → 1.199 | -99.37% |
| hoodi | message.body.randao_reveal | 424.277 → 213.882 | -49.59% | 191.197 → 1.153 | -99.40% |
| hoodi | small.slot | 11.385 → 4.443 | -60.98% | 5.695 → 1.140 | -79.99% |
| hoodi | small.source | 12.340 → 6.002 | -51.36% | 6.976 → 1.112 | -84.06% |
| gloas | signature | 66.843 → 4.463 | -93.32% | 5.919 → 1.107 | -81.30% |
| gloas | message | 155.828 → 112.775 | -27.63% | 95.187 → 1.169 | -98.77% |
| gloas | message.body.randao_reveal | 156.616 → 112.218 | -28.35% | 96.345 → 1.132 | -98.83% |
| gloas | small.slot | 11.100 → 4.433 | -60.06% | 5.726 → 1.152 | -79.88% |
| gloas | small.source | 12.082 → 6.008 | -50.27% | 7.026 → 1.119 | -84.07% |

First complete-message access improves by 57.06% on mainnet, 49.25% on Hoodi,
and 27.63% on Gloas. Repeated complete-message access improves by 98.77–99.69%.
First direct scalar access improves by 60.06–61.91%. No measured field operation
regresses; the per-pair direction agrees for all three pairs. First access still
constructs the selected subtree eagerly, and caches retain those Python
snapshots until close. No memory-use improvement is claimed.

The accompanying CSV contains exact P50/P99, aggregate percentage, and mean
delta for every codec/hash and first/repeated field operation. Raw JSON also
records every per-block median and each pair’s aggregate totals.

## Retained artifacts

- Baseline environment: `.deps/performance/stage-two-native/candidate-env`.
- Candidate environment and distributions: `.deps/performance/stage-three-projections/{candidate-env,wheels}`.
- Final raw runs, CSV, and JSON summary: `.deps/performance/stage-three-projections/results`.
- Pair runner, summarizer, source/native identity verifier, and logs: `.deps/performance/stage-three-projections`.
- Initial per-node and subsequent batched smoke results: `.deps/performance/stage-three-projections/field-smoke`.
- Reusable field benchmark: `benchmarks/benchmark_fields.py`.

## Final binary identities

- Baseline extension SHA-256: `5b2919173392d961901a1816ada0c3518d7859fe9b47466c839cdc8b909fc6d1`.
- Baseline wheel SHA-256: `ae916d1c7eb037ff7480d72d505e86bb61471b359762b88dab3c3a795b6b5c47`.
- Candidate extension SHA-256: `2e55021ff063e6e43d08d9a4dbdb487b14b457e75982493c988e41e471896da1`.
- Candidate wheel SHA-256: `2fbdff64cf8acabc0609858eb16a77c4506954824e0f8129e7403fa5f392027c`.

## Final distribution verification after commit checks

The formatter/static-typing corrections were rebuilt through the normal source
and wheel pipeline into `final-distributions`, then installed into a separate
`final-env`. The measured `candidate-env`, `wheels`, results, and binary identities
remain unchanged. All 55 final installed Python/stub/resource files match the
current source bytes exactly, including corrected private stub declarations.
All 21 runtime Python ASTs match the measured installation. The 38 unchanged
native/build source files match their measured hashes; the metadata generator
has only the previously described quote/stub changes, and the native README
has documentation changes. Selected native/build/generated sources in the final
source distribution were also compared byte-for-byte with the checkout.

The isolated final installed-package smoke check passed. The final wheel's exact
extension was copied into the ignored checkout extension and all 529 tests passed
again in 2.09 seconds. Generated metadata verification and final diff checks pass.
The separate final identity record is retained at
`.deps/performance/stage-three-projections/final-identity.json`.

- Final source distribution SHA-256: `6d320db91ebc1f99cceb6ba48ff7edc5d46271d0ea0f0afae39a6f85c1ca06b1`.
- Final wheel SHA-256: `4dc901c090a5fb2f77d3ae46cb2b613c2f77a2c656dc6f8d3954d3cbde6d9a8a`.
- Final extension SHA-256: `d3c197d3992d3b566ff9e97d099174f815962eee34aef32846c4e26a2643047f`.
