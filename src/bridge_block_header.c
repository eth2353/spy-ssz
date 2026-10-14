#include <string.h>

#include "bridge_internal.h"
#include "metadata_constants.h"

enum {
    SPY_SSZ_UINT64_SIZE = 8,
    SPY_SSZ_ROOT_SIZE = 32,
    SPY_BEACON_BLOCK_FIELD_COUNT = 5,
    SPY_BEACON_BLOCK_HEADER_SIZE =
        2 * SPY_SSZ_UINT64_SIZE + 3 * SPY_SSZ_ROOT_SIZE,
};

typedef enum {
    SPY_BEACON_BLOCK_SLOT = 0,
    SPY_BEACON_BLOCK_PROPOSER = 1,
    SPY_BEACON_BLOCK_PARENT_ROOT = 2,
    SPY_BEACON_BLOCK_STATE_ROOT = 3,
    SPY_BEACON_BLOCK_BODY = 4,
} spy_beacon_block_field;

enum { SPY_BEACON_BLOCK_CONTENTS_BLOCK = 0 };

int32_t spy_ssz_object_block_header(
    spy_raw_ssz_ptr opaque, spy_BytesObject *output) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj == NULL || output->length < SPY_BEACON_BLOCK_HEADER_SIZE) return 0;

    int32_t block = obj->root_node;
    if (obj->object_kind == SPY_SSZ_OBJECT_BEACON_BLOCK_CONTENTS)
        block = spy_ssz_child(obj, block, SPY_BEACON_BLOCK_CONTENTS_BLOCK);
    else if (obj->object_kind != SPY_SSZ_OBJECT_BLINDED_BEACON_BLOCK &&
             obj->object_kind != SPY_SSZ_OBJECT_BEACON_BLOCK)
        return 0;

    spy_ssz_object$SszNode block_node = obj->nodes.p[block];
    if (block_node.child_count != SPY_BEACON_BLOCK_FIELD_COUNT) return 0;
    int32_t slot = spy_ssz_child(obj, block, SPY_BEACON_BLOCK_SLOT);
    int32_t proposer = spy_ssz_child(obj, block, SPY_BEACON_BLOCK_PROPOSER);
    int32_t parent = spy_ssz_child(obj, block, SPY_BEACON_BLOCK_PARENT_ROOT);
    int32_t state = spy_ssz_child(obj, block, SPY_BEACON_BLOCK_STATE_ROOT);
    int32_t body = spy_ssz_child(obj, block, SPY_BEACON_BLOCK_BODY);
    spy_ssz_object$SszNode slot_node = obj->nodes.p[slot];
    spy_ssz_object$SszNode proposer_node = obj->nodes.p[proposer];
    spy_ssz_object$SszNode parent_node = obj->nodes.p[parent];
    spy_ssz_object$SszNode state_node = obj->nodes.p[state];
    if (slot_node.data_length < SPY_SSZ_UINT64_SIZE ||
        proposer_node.data_length < SPY_SSZ_UINT64_SIZE ||
        parent_node.data_length != SPY_SSZ_ROOT_SIZE ||
        state_node.data_length != SPY_SSZ_ROOT_SIZE)
        return 0;

    memcpy(output->data.p, obj->arena.p + slot_node.data_offset,
           SPY_SSZ_UINT64_SIZE);
    memcpy(output->data.p + SPY_SSZ_UINT64_SIZE,
           obj->arena.p + proposer_node.data_offset, SPY_SSZ_UINT64_SIZE);
    memcpy(output->data.p + 2 * SPY_SSZ_UINT64_SIZE,
           obj->arena.p + parent_node.data_offset, SPY_SSZ_ROOT_SIZE);
    memcpy(output->data.p + 2 * SPY_SSZ_UINT64_SIZE + SPY_SSZ_ROOT_SIZE,
           obj->arena.p + state_node.data_offset, SPY_SSZ_ROOT_SIZE);
    spy_BytesObject body_root = {
        .length = SPY_SSZ_ROOT_SIZE,
        .hash = 0,
        .data = {
            .p = output->data.p + 2 * SPY_SSZ_UINT64_SIZE
                + 2 * SPY_SSZ_ROOT_SIZE,
        },
    };
    return spy_ssz_fast_node_hash_tree_root(opaque, body, &body_root);
}
