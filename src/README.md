# SPy layout

`ssz_object.spy` owns a fork-independent typed SSZ graph. Each object records
its fork, object kind, schema id, root node, node/edge arrays, decoded-byte
arena, Merkle workspace, and cached root. Composite nodes point to ordered
child edges; scalar nodes point into the arena.

`json_parser.spy` and `ssz_reader.spy` are temporary input infrastructure used
only while a schema lowerer runs. The C ownership wrapper destroys their source
copy before the opaque SSZ object reaches Python. JSON and SSZ therefore create
the same retained graph layout.

Fulu's unchanged wire schemas use the Electra lowerers with the logical fork
and schema ID supplied as decoder parameters. Shared JSON and SSZ lowering
primitives live in `json_lowering.spy` and `ssz_lowering.spy`; the root also
contains the shared runtime and build infrastructure. Schema IDs come from
`spy_ssz/schemas.yaml`; validation limits come from canonical
`spy_ssz/presets/<preset>/*.yaml` files. The build regenerates `metadata.spy`
and `preset_config.spy` from those authoritative inputs. New block,
attestation, or fork schemas reuse the same node constructors and generic
hasher.

`electra/electra_block.spy` and `electra/electra_block_ssz.spy` are shared by
Electra and Fulu signed blocks. Parameterized SPy entry points receive the fork
and schema IDs before values cross the C bridge. They cover every block
operation family and execution-request list. `electra/electra_block_encode.spy`
provides their shared JSON and SSZ output path.

The pinned SPy compiler does not yet support packages, so module basenames are
globally unique even inside fork directories. The extension build flattens
those source modules into a temporary build input; the repository layout
remains the source of truth and no compatibility modules are maintained.

`bridge.c` is deliberately small and contains only ownership transfer, object
destruction, metadata accessors, and CFFI-visible function aliases. Codec and
hashing logic stays in SPy.
