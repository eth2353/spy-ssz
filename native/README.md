# Native layout

`ssz_object.spy` owns a fork-independent typed SSZ graph. Each object records
its fork, object kind, schema id, root node, node/edge arrays, decoded-byte
arena, Merkle workspace, and cached root. Composite nodes point to ordered
child edges; scalar nodes point into the arena.

`json_parser.spy` and `ssz_reader.spy` are temporary input infrastructure used
only while a schema lowerer runs. The C ownership wrapper destroys their source
copy before the opaque SSZ object reaches Python. JSON and SSZ therefore create
the same retained graph layout.

Fork modules such as `schema_deneb.spy` and `schema_gloas.spy` contain concrete
field layouts and validation limits. New block, attestation, or fork schemas
reuse the same node constructors and generic hasher.

`schema_electra.spy` and `schema_electra_ssz.spy` are shared by Electra and
Fulu signed blocks. Named SPy entry points supply the correct fork and schema
ids before values cross the C bridge. They cover every block operation family
and execution-request list. `schema_electra_encode.spy` provides their shared
JSON and SSZ output path.

`bridge.c` is deliberately small and contains only ownership transfer, object
destruction, metadata accessors, and CFFI-visible function aliases. Codec and
hashing logic stays in SPy.

Progressive nodes implement progressive Merkleization and active-field/length
mix-ins. The Gloas attestation test exercises a progressive container and a
300-bit progressive bitlist against `eth-consensus-specs`.
