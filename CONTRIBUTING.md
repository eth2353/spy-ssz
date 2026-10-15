# Development

Use Python 3.12 or newer and the pinned development dependencies:

```bash
uv sync --locked --dev
uvx pre-commit run --all-files
uv run python -m pytest -q
```

Pytest discovers only `tests/`. Downloaded upstream vectors under
`tools/spec-tests/` are checked separately with `tools/check_consensus_vectors.py`.

## Code boundaries

| Layer | Responsibility |
| --- | --- |
| Schema and preset YAML | Stable IDs, supported schemas, public names, and limits |
| `_codecs.py` | One immutable codec descriptor per schema/preset, built independently of public types |
| `_variants.py` | Export preset classes while preserving mainnet aliases and module identity |
| `electra/`, `fulu/`, `gloas/`, `signing.py` | Public type definitions and historical JSON policy attributes |
| `ssz.py` | Native ownership, locking, and orchestration of value/codec operations |
| `_native.py`, `_composition.py` | Native buffers, decode allocations, and typed child-graph composition |
| `_json_policy.py`, `_values.py` | Beacon API envelope transforms and JSON-backed Python values |
| `_projection.py`, generated `projections.py` | Copied native field snapshots and schema-derived immutable projection types |
| `src/` | Parsing, graph construction, hashing, and encoding |
| `tools/` | Generation, compilation, and artifact verification |

Keep fork-specific behavior explicit. Extract a shared abstraction only when
it has at least three actual consumers. Do not add a framework for a future
fork or object kind. Preserve public names and class identity when moving code.

Every native allocation must have one owner. Use `_use_handle()` throughout a
native operation: CFFI releases the GIL, so retaining a Python reference alone
does not prevent another thread from closing the object. Multiple-owner
operations acquire locks in object-ID order. Internal allocation sites adopt
through `_from_owned_handle()`, which bypasses public field constructors and
destroys failed adoptions exactly once. Never copy a raw handle into a second
owner; Python copies reconstruct an independent graph from SSZ.

Consensus-backed attribute reads traverse only the selected native field while
holding the owner lock, then cache detached immutable Python projections. Cached
reads still require a live owner; returned snapshots survive owner close. Native
metadata and payload buffers contain copies, never borrowed graph pointers. API-only
block containers without consensus catalog descriptors retain JSON-backed field
access until their descriptors are represented in the authoritative schema.

## Generated sources

Edit `spy_ssz/schemas.yaml`, preset YAML, or the relevant generator, rather than
editing generated Python enums, projections, type stubs, or SPy/C constants.

```bash
uv run python tools/generate_spy_metadata.py
uv run python tools/generate_spy_metadata.py --check
```

`--check` is read-only and fails if committed outputs are stale. CI also checks
for tracked changes after installation, since the build regenerates metadata.
`tools/generate_consensus_types.py` refreshes the catalog from the installed
consensus-specs package; review catalog changes alongside dependency updates.

Native builds flatten SPy source files into `src/build/input/` for the pinned
compiler. Module basenames must be unique. Build output is disposable and is
excluded from source distributions. `SPY_ROOT` explicitly selects a local
compiler checkout; an invalid path fails instead of choosing another compiler.

## Validation and releases

Behavior changes need tests against the relevant contract: canonical bytes,
reference Merkle roots, malformed input rejection, or ownership under copying
and concurrent close. The schema matrix checks all types with an upstream
reference on both mainnet and minimal; dedicated tests cover API-only
containers and Gnosis differences.

Build both distributions and check the wheel outside the development environment:

```bash
uv build
uv venv /tmp/spy-ssz-wheel-check
uv pip install --python /tmp/spy-ssz-wheel-check/bin/python dist/*.whl
/tmp/spy-ssz-wheel-check/bin/python -I tools/check_installed_package.py
```

Use a clean `dist/` or an explicit wheel path if it contains multiple versions.
The `-I` flag prevents the checkout from masking missing package files. The
smoke check exercises public exports, shipped resources, presets, decoding,
encoding, batch output, and hashing.

CI runs Linux amd64 and arm64 builds, installed-wheel checks, and a separate
ASan/UBSan job. Before release, also run the upstream static-vector check
described in the README. A local test pass does not substitute for platform
and sanitizer results.
