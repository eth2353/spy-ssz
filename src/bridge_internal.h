#ifndef SPY_SSZ_BRIDGE_INTERNAL_H
#define SPY_SSZ_BRIDGE_INTERNAL_H

#include "ssz_object.h"

typedef spy_ssz_object$SszObject spy_ssz_object_handle;
typedef spy_unsafe$raw_ptr__ssz_object$SszObject spy_raw_ssz_ptr;

static inline int32_t spy_ssz_child(spy_ssz_object$SszObject *obj,
                                  int32_t node, int32_t child) {
    spy_ssz_object$SszNode current = obj->nodes.p[node];
    return obj->edges.p[current.first_edge + child];
}

/* Internal graph hashing entry point; absent from the public CFFI API. */
int32_t spy_ssz_fast_node_hash_tree_root(
    spy_raw_ssz_ptr object, int32_t node, spy_BytesObject *output);

int32_t spy_schema_block_containers_ssz_size(spy_raw_ssz_ptr object);
int32_t spy_schema_block_containers_encode_ssz(
    spy_raw_ssz_ptr object, spy_BytesObject *output);
int32_t spy_ssz_object_block_header(
    spy_raw_ssz_ptr object, spy_BytesObject *output);

#endif
