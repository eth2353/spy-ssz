# Architectural stage-two Python performance validation

## Change and compatibility

This checkpoint separates native buffer validation/decode allocation (`_native.py`),
Python values and projections (`_values.py`), Beacon API envelope policies
(`_json_policy.py`), and typed signing composition (`_composition.py`) from public
object ownership in `ssz.py`. `_codecs.py` builds one frozen codec descriptor per
schema/preset in a single private registry, independently of public module imports.
Internal allocations adopt handles through `_from_owned_handle()`, bypassing public
field constructors and destroying failed adoptions exactly once. Direct public
handle construction remains supported.

Documented public classes, aliases, schema/preset behavior, value semantics, JSON
policies, and native ABI are preserved. The undocumented `register_*` helpers
formerly exported from `spy_ssz.ssz` are removed; third-party code using those
helpers must change. Native code and hashing are unchanged in this checkpoint.

## Verification and build identity

The checkpoint passed all 477 tests, generated metadata verification, isolated
wheel smoke verification, and the full pinned pre-commit checks before these timing
runs. The parent reviews and commits the checkpoint separately. Installed package
identity was reverified after aggregation under isolated Python (`-I`): baseline
50 Python/stub/resource files match accepted stage-one commit `d856972` byte for
byte; candidate 54 files match the checkout (Python AST equality and exact bytes
for stubs/resources). This report does not rely on the earlier lost timing files.

Both environments use Python 3.12.9, CFFI 2.1.1, msgspec 0.22.0, and PyYAML 6.0.3.
Host: `macOS-26.6.2-arm64-arm-64bit`.

The baseline wheel was reconstructed from the exact stage-one Git files and the
retained unchanged native extension. The candidate wheel contains the refactored
Python implementation and the same extension:

- Baseline wheel SHA-256: `2694c3ebfded12f12905a9a9e500bf5846a4dbe99e007a710113f944e99ec2e8`.
- Candidate wheel SHA-256: `9d4e9aa5ee4810fa800cae1054268cfb7b69b08fdd14fb1c75e996e8ed1262c1`.
- Both extension SHA-256: `e0899916d7bb4021bbc1251aed2f975aef3d9702d1cad8a1356a9f13a80ec29d`.

## Corpus and method

The corpus contains 1,000 real signed beacon blocks each from mainnet Fulu, Hoodi
Fulu, and Gloas, using the mainnet preset. Gloas excludes the separate execution
payload envelope. After the original temporary corpus was lost, it was restored
from the same user-provided nodes and slot ranges:

| Network | Source | Slot range |
| --- | --- | --- |
| mainnet | `http://validator-monitoring-mainnet:5555` | 15422933–15423936 |
| hoodi | `http://validator-monitoring-hoodi:5555` | 4140389–4141504 |
| gloas | `http://production-plataberget-serenita-cl-el-vc-1:5555` | 439360–440736 |

The restored manifests contain new provenance metadata and checksums. Their
hashes are new identifiers; equality with the lost original manifests is not
claimed. Every restored block is included in every timing run.

Three sequential baseline/candidate pairs used seeds 1040, 1041, and 1042 with
five measured calls and two warmups per operation/block. Order rotated
baseline/candidate, candidate/baseline, baseline/candidate. No builds, tests, or
other benchmarks overlapped. Imports used each installed environment under `-I`.
Disk reads and integrity checks are outside measured intervals. Decode includes
closing the new object; fresh hash excludes object construction and closing.

For each network/slot/operation, take the median of the three pass medians. P50
and P99 use nearest ranks: indices 499 and 989 of 1,000 sorted block medians.
Aggregate change compares sums of the 1,000 per-block medians; the absolute delta
is that difference divided by 1,000 blocks. Positive means slower. P99 describes
variation across workload blocks, rather than production latency tails.

## Results

| Network | Operation | Baseline P50 µs | Candidate P50 µs | Baseline P99 µs | Candidate P99 µs | Aggregate change | Mean delta µs/block |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mainnet | JSON decode | 533.000 | 535.042 | 1205.250 | 1181.541 | +0.49% | +2.764 |
| mainnet | SSZ decode | 10.542 | 10.750 | 16.625 | 16.750 | +1.53% | +0.164 |
| mainnet | JSON encode | 239.500 | 241.042 | 434.416 | 451.375 | +0.43% | +1.076 |
| mainnet | SSZ encode | 22.417 | 22.417 | 33.625 | 35.333 | +0.38% | +0.084 |
| mainnet | Fresh hash | 2799.167 | 2818.125 | 5745.458 | 5652.291 | +0.20% | +5.724 |
| mainnet | Cached hash | 1.583 | 1.583 | 1.708 | 1.709 | +0.62% | +0.010 |
| hoodi | JSON decode | 109.166 | 109.417 | 229.584 | 232.209 | +0.55% | +0.668 |
| hoodi | SSZ decode | 5.625 | 5.750 | 6.916 | 7.000 | +2.43% | +0.138 |
| hoodi | JSON encode | 114.709 | 115.084 | 161.416 | 164.333 | +0.55% | +0.652 |
| hoodi | SSZ encode | 11.000 | 11.041 | 19.792 | 20.167 | +0.24% | +0.028 |
| hoodi | Fresh hash | 428.083 | 430.667 | 745.208 | 754.417 | +0.32% | +1.401 |
| hoodi | Cached hash | 1.542 | 1.542 | 1.667 | 1.667 | +0.67% | +0.010 |
| gloas | JSON decode | 27.000 | 27.250 | 32.333 | 32.542 | +0.93% | +0.232 |
| gloas | SSZ decode | 4.250 | 4.417 | 4.625 | 4.792 | +3.79% | +0.160 |
| gloas | JSON encode | 32.041 | 32.125 | 35.792 | 36.041 | +0.40% | +0.115 |
| gloas | SSZ encode | 3.083 | 3.083 | 3.834 | 3.833 | -0.15% | -0.005 |
| gloas | Fresh hash | 66.500 | 66.875 | 81.292 | 81.333 | +0.50% | +0.303 |
| gloas | Cached hash | 1.583 | 1.584 | 1.708 | 1.750 | +1.26% | +0.020 |

SSZ decoding shows a consistent small cost across the paired passes: +0.138 to
+0.164 µs/block in the aggregate, or +1.53% to +3.79%. The individual paired
SSZ-decode deltas were mainnet +1.94%, +0.63%, +1.91%; Hoodi +3.10%, +1.10%,
+2.62%; Gloas +6.78%, +1.69%, +3.28%. The first Gloas pair is larger than the
other two, so it should not be treated as the typical effect. The median
aggregation includes all three passes without selecting or excluding any pair.

Other aggregate changes range from -0.15% to +1.26%. Cached-hash mean costs are
0.010–0.020 µs/block. JSON and fresh-hash timing variations do not establish a
causal regression from this local comparison. The observed decode overhead is
accepted under the user's allowance for tiny performance costs in exchange for
clearer ownership and module boundaries. This local macOS ARM64 comparison does
not establish Linux, sanitizer, or other workload performance.

## Integrity and retained artifacts

All six runs completed exactly 3,000 unique network/slot rows, 1,000 per network:
18,000 verified timing rows. Each runner verified JSON and SSZ file checksums,
canonical SSZ round trips, JSON/SSZ root equality, and JSON output decode root
equality. Aggregation verified identical manifest identifiers, network/slot sets,
and all 3,000 per-block roots across the six runs, plus seeds, round counts, and
complete positive measurements for all six operations. No blocks were excluded.

Restored manifest SHA-256 identifiers:

- `mainnet`: `d124ba051e177672ced2b8bc159fbe9e813a25528170d3fb3accbcb9d91cb3f3`.
- `hoodi`: `3eaa3142f8f17adff9ab3f1f02bc9ac8d3bbff31479f1c8fa5b0660f7b0bcdcd`.
- `gloas`: `9e2821d73ee478e71f45f7c8710bdbdfd7b8d0794b19b47ad773454d50816c80`.

Artifacts are retained under `.deps/performance/stage-two-python/`:

- `baseline-env/`, `candidate-env/`, and `wheels/`: isolated measured installations.
- `baseline-identity.json`, `candidate-identity.json`: verified installed identities.
- `results/baseline-{0,1,2}.json`, `results/candidate-{0,1,2}.json` and matching logs.
- `results/summary.json`, `results/summary.csv`: per-network ranks, aggregate totals,
  per-pass totals, and paired changes.
- `run_benchmarks.py`, `summarize.py`, `verify_identity.py`: run and verification helpers.

The restored corpus is retained under `.deps/performance/real-blocks/` for the
next checkpoint. Raw artifacts are local ignored files; this report is tracked.

## Reproduction

Run from the repository root with the retained environment interpreters:

```bash
.deps/performance/stage-two-python/candidate-env/bin/python \
  .deps/performance/stage-two-python/run_benchmarks.py
.deps/performance/stage-two-python/candidate-env/bin/python \
  .deps/performance/stage-two-python/summarize.py
.deps/performance/stage-two-python/baseline-env/bin/python -I \
  .deps/performance/stage-two-python/verify_identity.py baseline
.deps/performance/stage-two-python/candidate-env/bin/python -I \
  .deps/performance/stage-two-python/verify_identity.py candidate
```

The runner invokes `benchmarks/benchmark_native.py` with each target interpreter,
`-I`, the restored corpus, `--limit 1000 --rounds 5 --warmup 2`, each seed, and a
separate output file. Preserve existing raw outputs before repeating a run.
