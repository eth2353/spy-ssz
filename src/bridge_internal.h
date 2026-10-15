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

enum {
    SPY_KIND_UINT = 1,
    SPY_KIND_FIXED_BYTES = 2,
    SPY_KIND_BYTE_LIST = 3,
    SPY_KIND_BITLIST = 4,
    SPY_KIND_CONTAINER = 5,
    SPY_KIND_LIST = 6,
    SPY_KIND_PROGRESSIVE_CONTAINER = 7,
    SPY_KIND_PROGRESSIVE_LIST = 8,
    SPY_KIND_PROGRESSIVE_BITLIST = 9,
    SPY_KIND_PROGRESSIVE_BASIC_LIST = 11,
    SPY_KIND_BASIC_LIST = 10,
};

/* Records are copied in preorder, followed recursively by each node's children
 * in field/list order. Each record consumes data_length bytes from a separate
 * concatenated payload buffer; bitlists include their canonical marker.
 * Python owns both output buffers. No graph pointer or native allocation
 * crosses this projection API. */
typedef struct {
    int32_t kind;
    int32_t data_length;
    int32_t child_count;
    int32_t element_width;
} spy_projection_node;

int32_t spy_ssz_object_projection_size(
    spy_raw_ssz_ptr object, int32_t field, int32_t *sizes);
int32_t spy_ssz_object_projection_copy(
    spy_raw_ssz_ptr object, int32_t field, spy_projection_node *nodes,
    int32_t node_count, spy_BytesObject *output);

/* Internal graph hashing entry point; absent from the public CFFI API. */
int32_t spy_ssz_fast_node_hash_tree_root(
    spy_raw_ssz_ptr object, int32_t node, spy_BytesObject *output);

int32_t spy_schema_block_containers_ssz_size(spy_raw_ssz_ptr object);
int32_t spy_schema_block_containers_encode_ssz(
    spy_raw_ssz_ptr object, spy_BytesObject *output);
int32_t spy_ssz_object_block_header(
    spy_raw_ssz_ptr object, spy_BytesObject *output);

#endif
