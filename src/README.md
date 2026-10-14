# SPy layout

`ssz_object.spy` owns a fork-independent typed SSZ graph. Each object records
its fork, object kind, schema id, root node, node/edge arrays, decoded-byte
arena, 128-byte decimal-writer scratch buffer, and cached root. Composite nodes
point to ordered child edges; scalar nodes point into the arena.

`json_parser.spy` and `ssz_reader.spy` are temporary input infrastructure used
only while a schema lowerer runs. Their documents borrow the Python-owned input
for the synchronous native call. The C ownership wrapper destroys those
temporary documents before the opaque SSZ object reaches Python. JSON and SSZ
therefore create the same retained graph layout.

Fulu's unchanged wire schemas use the Electra lowerers with the logical fork
and schema ID supplied as decoder parameters. Shared JSON and SSZ lowering
primitives live in `json_lowering.spy` and `ssz_lowering.spy`; the root also
contains the shared runtime and build infrastructure. Schema IDs come from
`spy_ssz/schemas.yaml`; validation limits come from canonical
`spy_ssz/presets/<preset>/*.yaml` files. The build regenerates `metadata.spy`
and `preset_config.spy` from those authoritative inputs. New block,
attestation, or fork schemas reuse the same node constructors and generic
graph representation and C Merkleizer.

`electra/electra_block.spy` and `electra/electra_block_ssz.spy` are shared by
Electra and Fulu signed blocks. Parameterized SPy entry points receive the fork
and schema IDs before values cross the C bridge. They cover every block
operation family and execution-request list. `electra/electra_block_encode.spy`
provides their shared JSON and SSZ output path.

Repeated list loops are compile-time specializations: `writer.spy` supplies
JSON, fixed-item SSZ, and variable-item SSZ sequence writers; the lowering
modules supply composite-list readers. Each specialization calls its item
codec directly. Bounded lists retain preset limits, while progressive lists
retain their distinct node kind. Variable-item readers check relative offsets
before converting them to positions in the input. Keep schema field layouts
explicit, and add shared helpers only for patterns used in more than two places.

The pinned SPy compiler does not yet support packages, so module basenames are
globally unique even inside fork directories. The extension build flattens
those source modules into a temporary build input; the repository layout
remains the source of truth and no compatibility modules are maintained.

SPy implements parsing, schema lowering, graph construction, signing by graph
cloning, and most JSON/SSZ sizing and encoding. `bridge.c` owns transfer and
destruction of native objects, metadata accessors, and CFFI-visible aliases.
It also implements batch encoding, signed block-contents SSZ sizing/encoding,
and block-header extraction. Signed block-contents encoding temporarily selects
the signed child as `root_node` and restores the original root before returning;
the Python ownership layer holds the object's lock throughout the native call.

Public object and subtree hashing use `merkle.c`, included by `bridge.c`.
This bounded-stack C Merkleizer uses the object-owned zero-subtree roots from
`ssz_kernels.spy`, owns lazy node-root caches, and uses the fixed
64-byte SHA-256 pair kernel in `sha256_pair.c`. The zero-subtree table, retained
root buffer, and node caches belong to the object and are freed by the bridge
destructor. Writer scratch is exclusively for decimal output and is not a
hashing workspace.
There is no second SPy object-hashing implementation or generated hash-kernel
replacement step in the build.
