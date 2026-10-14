#include <string.h>

#include "bridge_internal.h"
#include "metadata_constants.h"
#include "electra_block_encode.h"
#include "electra_block_containers_encode.h"

enum {
    SPY_SSZ_OFFSET_SIZE = 4,
    SPY_SIGNED_BLOCK_CONTENTS_FIELD_COUNT = 3,
    SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE =
        SPY_SIGNED_BLOCK_CONTENTS_FIELD_COUNT * SPY_SSZ_OFFSET_SIZE,
    SPY_SIGNED_BLOCK_CONTENTS_LIST_COUNT = 2,
};

typedef enum {
    SPY_SIGNED_BLOCK_CONTENTS_BLOCK = 0,
    SPY_SIGNED_BLOCK_CONTENTS_PROOFS = 1,
    SPY_SIGNED_BLOCK_CONTENTS_BLOBS = 2,
} spy_signed_block_contents_field;

static int32_t spy_ssz_fixed_list_size(spy_ssz_object$SszObject *obj,
                                       int32_t node) {
    spy_ssz_object$SszNode list = obj->nodes.p[node];
    int32_t result = 0;
    for (int32_t i = 0; i < list.child_count; i++) {
        int32_t item = obj->edges.p[list.first_edge + i];
        result += obj->nodes.p[item].data_length;
    }
    return result;
}

int32_t spy_schema_block_containers_ssz_size(spy_raw_ssz_ptr opaque) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj->object_kind != SPY_SSZ_OBJECT_SIGNED_BEACON_BLOCK_CONTENTS)
        return spy_electra_block_containers_encode$block_container_ssz_size(opaque);
    int32_t contents = obj->root_node;
    int32_t signed_block = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_BLOCK);
    int32_t proofs = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_PROOFS);
    int32_t blobs = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_BLOBS);
    int32_t block_size =
        spy_electra_block_encode$electra_ssz_size_at(opaque, signed_block);
    return SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE + block_size
        + spy_ssz_fixed_list_size(obj, proofs)
        + spy_ssz_fixed_list_size(obj, blobs);
}

int32_t spy_schema_block_containers_encode_ssz(spy_raw_ssz_ptr opaque,
                                   spy_BytesObject *output) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj->object_kind != SPY_SSZ_OBJECT_SIGNED_BEACON_BLOCK_CONTENTS)
        return spy_electra_block_containers_encode$block_container_encode_ssz(opaque, output);
    int32_t contents = obj->root_node;
    int32_t signed_block = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_BLOCK);
    int32_t proofs = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_PROOFS);
    int32_t blobs = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_BLOBS);
    int32_t proof_size = spy_ssz_fixed_list_size(obj, proofs);
    int32_t block_size =
        spy_electra_block_encode$electra_ssz_size_at(opaque, signed_block);
    uint32_t offsets[SPY_SIGNED_BLOCK_CONTENTS_FIELD_COUNT] = {
        SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE,
        SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE + block_size,
        SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE + block_size + proof_size,
    };
    memcpy(output->data.p, offsets, sizeof(offsets));
    spy_BytesObject block_output = {
        .length = output->length - SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE,
        .hash = 0,
        .data = {
            .p = output->data.p + SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE,
        },
    };
    spy_electra_block_encode$electra_encode_ssz_at(
        opaque, signed_block, &block_output);
    int32_t position = SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE + block_size;
    int32_t lists[SPY_SIGNED_BLOCK_CONTENTS_LIST_COUNT] = {proofs, blobs};
    for (int32_t list_index = 0;
         list_index < SPY_SIGNED_BLOCK_CONTENTS_LIST_COUNT;
         list_index++) {
        spy_ssz_object$SszNode list = obj->nodes.p[lists[list_index]];
        for (int32_t i = 0; i < list.child_count; i++) {
            int32_t item_index = obj->edges.p[list.first_edge + i];
            spy_ssz_object$SszNode item = obj->nodes.p[item_index];
            memcpy(output->data.p + position, obj->arena.p + item.data_offset,
                   item.data_length);
            position += item.data_length;
        }
    }
    return position;
}
