# Architectural stage-one performance validation

## Method and identity

Compared the retained `b63927b` runtime baseline with the uncommitted stage-one
cleanup based on `9d0e9c4`. The candidate wheel was rebuilt after the native changes.
Its installed Python modules have the same ASTs as the final executable checkout
sources; later changes only adjusted documentation/comments/formatting.

Both isolated environments use Python 3.12.9, CFFI 2.1.1, msgspec 0.22.0, and
PyYAML 6.0.3 on macOS 26.6.2 ARM64. Imports were verified under `-I`:

- Baseline: `/tmp/spy-ssz-perf-writer-env/bin/python`.
- Candidate: `/tmp/spy-ssz-stage-one-wheel-env/bin/python`.
- Baseline extension SHA-256: `4af41b721b8d55b7ad7cdf4726c7b41a7d9361db11f9db12c02377020d2e30e2`.
- Candidate extension SHA-256: `e0899916d7bb4021bbc1251aed2f975aef3d9702d1cad8a1356a9f13a80ec29d`.
- Candidate wheel SHA-256: `f5be8d7f094a58f9b3c1274e482811b6f73d156b50c15aae2d7e63b3a717c5d2`.

The existing corpus contains 1,000 signed beacon blocks each from mainnet Fulu,
Hoodi Fulu, and Gloas, all using the mainnet preset. Gloas excludes the separate
execution payload envelope. No corpus files were downloaded or changed.

Three primary passes used seeds 1040, 1041, and 1042, five measured calls and two
warmups per operation per block. Run order was baseline/candidate,
candidate/baseline, baseline/candidate. All timing runs were sequential with no
overlapping builds, tests, or other benchmarks.

For each network/slot/operation, the aggregate uses the median across the three
passes. P50 and P99 use nearest ranks (indices 499 and 989 among 1,000 sorted
block medians). Timings below are microseconds; aggregate change is the percentage
change in the sum of the 1,000 per-block medians. Positive means slower.
**P99 describes variation across workload blocks, not production latency tails.**

## Primary results

| Network | Operation | Baseline P50 µs | Candidate P50 µs | Baseline P99 µs | Candidate P99 µs | Aggregate change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| mainnet | JSON decode | 544.375 | 543.625 | 1215.833 | 1216.250 | +0.08% |
| mainnet | SSZ decode | 10.875 | 10.833 | 16.958 | 16.791 | -0.54% |
| mainnet | JSON encode | 243.875 | 243.708 | 438.500 | 443.792 | -0.04% |
| mainnet | SSZ encode | 22.500 | 22.750 | 34.625 | 35.041 | +0.86% |
| mainnet | Fresh hash | 2857.708 | 2831.042 | 5698.583 | 5718.667 | -1.02% |
| mainnet | Cached hash | 1.625 | 1.625 | 1.750 | 1.750 | +0.13% |
| hoodi | JSON decode | 110.958 | 111.000 | 229.959 | 234.500 | -0.09% |
| hoodi | SSZ decode | 5.834 | 5.750 | 7.042 | 6.958 | -1.44% |
| hoodi | JSON encode | 117.167 | 117.042 | 165.709 | 166.417 | -0.20% |
| hoodi | SSZ encode | 11.292 | 11.333 | 20.375 | 20.541 | +0.27% |
| hoodi | Fresh hash | 436.958 | 432.833 | 760.875 | 751.458 | -1.06% |
| hoodi | Cached hash | 1.583 | 1.583 | 1.709 | 1.709 | +0.10% |
| gloas | JSON decode | 27.667 | 27.542 | 33.083 | 33.125 | -0.59% |
| gloas | SSZ decode | 4.500 | 4.375 | 4.875 | 4.709 | -2.54% |
| gloas | JSON encode | 32.834 | 32.625 | 36.625 | 36.000 | -0.76% |
| gloas | SSZ encode | 3.125 | 3.125 | 3.916 | 3.875 | -0.86% |
| gloas | Fresh hash | 67.833 | 67.375 | 81.625 | 81.667 | -0.51% |
| gloas | Cached hash | 1.625 | 1.625 | 1.750 | 1.750 | -0.02% |

The largest primary aggregate slowdown was mainnet SSZ encoding at +0.86%.
Other primary slowdowns were +0.27% or less. These small changes are acceptable
for this cleanup; apparent improvements should not be treated as established
speedups from a single host comparison.

## Variation and followup

Per-pass aggregate totals and paired deltas are retained in `summary.json` and
`summary.csv`. The first Gloas SSZ-decode pair showed -6.42%, while the other two
showed -1.61% and -1.53%. Baseline Gloas decode totals varied from 4.411 to
4.615 ms across passes; candidate totals varied from 4.319 to 4.384 ms.
This prompted a full seed-1040 rerun with reversed candidate/baseline order.

| Network | Followup SSZ decode change | Followup SSZ encode change |
| --- | ---: | ---: |
| mainnet | -1.33% | +1.99% |
| hoodi | -2.21% | +0.87% |
| gloas | -2.70% | -0.49% |

The reversed-order Gloas SSZ-decode result was -2.70%, so the initial -6.42%
is not representative. Mainnet SSZ encoding showed +1.99% in the followup;
its primary paired deltas were +0.12%, +0.54%, and +1.63%. This remains a small
encoding cost, with no material reproducible regression found. The followup
is reported separately and does not replace or alter the three primary passes.

## Integrity and artifacts

All eight runs contain exactly 3,000 complete, unique network/slot rows. Every
run verified JSON and SSZ checksums, canonical SSZ round trips, JSON/SSZ root
equality, and JSON output round trips. All per-block roots and manifest hashes
match across the eight runs and the retained historical `writer-{0,1,2}.json`
baseline results. That is 24,000 successfully verified timing rows with no
excluded blocks or codec failures.

Manifest SHA-256 identifiers:

- `gloas`: `e4221ad99fecbaa39aec0315e255ffdb584f1e536b9faf9ffb34e1d5c80987fb`.
- `hoodi`: `6d64b9f79f7f2a6444569e8f381c4d669aa369381c2f914595bbcf94fe53ce4a`.
- `mainnet`: `122c8faba7e4b78c8e20609678652c7b24d7775b17dd09545996c2b5e02e8055`.

Raw files are retained in `/tmp/spy-ssz-stage-one-performance/`:

- `baseline-{0,1,2}.json` and `candidate-{0,1,2}.json`: primary measurements.
- `baseline-followup-1040.json` and `candidate-followup-1040.json`: followup.
- Matching `.log` files: benchmark progress/output.
- `summary.json`, `summary.csv`, and `followup-summary.json`: aggregates.
- `identities.json` and `candidate.patch`: build identities and measured source changes.

The baseline environment, candidate environment, corpus, and historical baseline
files are preserved for subsequent stages. This is a local macOS ARM64 check;
it does not establish Linux, sanitizer, or other workload performance.

## Reproduction

Use each environment interpreter with the following command and rotate order:

```bash
/path/to/environment/bin/python -I \
  /Users/luca/projects/serenita/spy-ssz/benchmarks/benchmark_native.py \
  /tmp/spy-ssz-real-blocks --limit 1000 --rounds 5 --warmup 2 --seed 1040 \
  --output /tmp/spy-ssz-stage-one-performance/build-name-0.json
```

Repeat with seeds 1041 and 1042. For the followup, run candidate then baseline
with seed 1040 and distinct output names. The aggregation helper is retained at
`/tmp/summarize_spy_stage_one.py`; it verifies row counts, manifests, and roots
before calculating medians and ranks.
