# Native cleanup performance comparison

## Corpus and method

Collected 1,000 finalized signed beacon blocks per network from the supplied
Beacon nodes on 2026-10-13. Both JSON and SSZ came from
`GET /eth/v2/beacon/blocks/{slot}` with the appropriate `Accept` header.
Missed slots were skipped while walking backward from a fixed finalized header.

| Network | Fork | Slots | Missed slots | Median SSZ size |
| --- | --- | --- | ---: | ---: |
| Mainnet | Fulu | 15,422,933–15,423,936 | 4 | 162.08 KiB |
| Hoodi | Fulu | 4,140,389–4,141,504 | 116 | 27.16 KiB |
| Devnet | Gloas | 439,360–440,736 | 377 | 3.87 KiB |

All use the mainnet preset. Gloas beacon blocks do not include the separate
execution payload envelope, so these measurements do not cover that codec.

The baseline wheels were built from unmodified Git archives using the same
pinned SPy compiler and release flags:

- `612c3f7`: original code, before all cleanup.
- `9cfdcc9`: Python/build cleanup, before native dead-code removal and list refactoring.
- `27af326`: completed native cleanup.
- `f3257f6`: restored the Python bytes-input fast path, retaining input validation.
- `b63927b`: final version; shared variable SSZ writers reuse their loop count.

Each wheel runs in its own virtual environment with Python 3.12.9, CFFI 2.1.1,
msgspec 0.22.0, and PyYAML 6.0.3 on macOS 26.6.2 ARM64. Python runs with `-I`
and the benchmark records the imported package path, preventing accidental
imports from the checkout.

Three sequential passes rotate build order and use seeds 1040, 1041, and 1042.
Within a pass all builds see the same shuffled block order. Each operation has
two warmups and five measured calls per block; each block's timing is the median.
GC is disabled only during the operation loop and its previous state is restored.
There are no concurrent benchmark or build processes.

The original three builds used the rotated order described above. The two small
performance fixes were each measured in three subsequent passes with the same
seeds and settings. A separate SSZ-encoding check loaded the original,
pre-native-refactor, and final packages under independent names in one process.
It shuffled build order for each block over eight rounds of twenty encodes,
reducing process and CPU-frequency effects when checking the small difference.

Before timing each block, the runner verifies input SHA-256 hashes, exact SSZ
round trips, JSON/SSZ root equality, and a JSON output round trip. Hash roots are
also compared across every build and pass. Disk I/O and verification are outside
the timed intervals. Decode timings include object destruction. Cold hashing
uses a newly decoded object for each call, with decoding and destruction outside
the timer; cached hashing is reported separately.

One interrupted download initially contained concatenated curl retry output.
Both the reference decoder and native builds rejected it. It was re-downloaded
and its manifest updated before the recorded comparison. No blocks were excluded
for codec failures.

## Results

Final `b63927b` versus original `612c3f7`, using aggregate timings across
1,000 blocks per network. Positive percentages mean slower; negative mean faster.

| Network | JSON decode | SSZ decode | JSON encode | SSZ encode | Fresh hash | Cached hash |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mainnet | -0.01% | +0.73% | -0.01% | +0.73% | -0.01% | +1.40% |
| hoodi | -0.02% | +0.37% | +0.22% | +1.10% | -0.19% | +0.76% |
| gloas | +0.38% | +1.99% | +0.41% | +0.31% | +0.19% | +0.74% |

Most differences are around 1% or less. The largest aggregate difference is
Gloas SSZ decoding at +1.99%: approximately 4.28 to 4.37 microseconds per block,
an increase of about 0.09 microseconds. These small differences are retained as
an acceptable tradeoff for the shared code; they are not reported as zero cost.
Fresh hashing and JSON measurements stay within about 0.5% of the original.

The comparison exposed Python input-validation overhead that was avoidable.
`f3257f6` keeps exact `bytes` on a fast path and skips JSON envelope handling for
SSZ, while preserving size checks, typed-memoryview byte counts, input rejection,
and copying of mutable buffers. An interleaved same-native-build check measured
about 3% lower Gloas decode time for that change. Full-run results still include
small differences from compiler layout, process scheduling, and run variation.

The shared SSZ writers have a small measurable encoding cost. The interleaved
encoding check measured +1.18% on mainnet, +0.33% on Hoodi, and -0.19% on Gloas
versus the original. The final code retains these shared writers; `b63927b`
reuses the item count for both offset and payload passes without adding a
schema-specific special case.

All 3,000 blocks passed input integrity checks and JSON/SSZ round trips in every
recorded build and pass; their roots agree across builds. Final validation also
passed 468 tests, 6,784 upstream consensus vectors, and the isolated-wheel smoke
check. The Gloas execution-payload-envelope codec is covered by those correctness
checks but was not performance-tested with this beacon-block corpus.

[Detailed measurements](native-cleanup-2026-10-13.csv) include every revision,
per-block p50/p95, aggregate times, and individual pass totals. Results were
collected across October 13–14; baseline/follow-up processes were sequential,
not simultaneous. This is a local macOS ARM64 comparison, not a guarantee for
other platforms or workloads.

## Reproduction

The collected corpus is `/tmp/spy-ssz-real-blocks`; raw timing files and aggregated
results are `/tmp/spy-ssz-performance`. Raw blocks are not checked into Git.

Each network directory contains paired block files and a `manifest.json`:

```json
{
  "network": "mainnet",
  "fork": "fulu",
  "preset": "MAINNET",
  "blocks": [{
    "slot": 15423936,
    "json": "15423936.json",
    "ssz": "15423936.ssz",
    "json_sha256": "<SHA-256 of JSON input>",
    "ssz_sha256": "<SHA-256 of SSZ input>"
  }]
}
```

Run the same script with each installed wheel's interpreter, rotating their order:

```bash
/path/to/environment/bin/python -I benchmarks/benchmark_native.py \
  /tmp/spy-ssz-real-blocks --rounds 5 --warmup 2 --seed 1040 \
  --output /tmp/build-name-0.json
```

Repeat with seeds 1041 and 1042. The reported aggregate uses each block's median
across passes, then sums those medians within each network. Per-block p95 and
individual pass totals are retained to expose tail behavior and run variation.
This is a local regression check on recent blocks, not a claim about every
platform or historical workload.

Corpus manifest SHA-256 identifiers:

- `gloas`: `e4221ad99fecbaa39aec0315e255ffdb584f1e536b9faf9ffb34e1d5c80987fb`
- `hoodi`: `6d64b9f79f7f2a6444569e8f381c4d669aa369381c2f914595bbcf94fe53ce4a`
- `mainnet`: `122c8faba7e4b78c8e20609678652c7b24d7775b17dd09545996c2b5e02e8055`
