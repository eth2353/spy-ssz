#include <stdlib.h>

#include "json_parser.h"
#include "metadata.h"
#include "metadata_constants.h"
#include "json_lowering.h"
#include "ssz_lowering.h"
#include "electra_block.h"
#include "electra_block_encode.h"
#include "electra_block_ssz.h"
#include "fulu_block.h"
#include "fulu_block_ssz.h"
#include "electra_signing.h"
#include "electra_block_containers.h"
#include "electra_block_containers_encode.h"
#include "electra_block_containers_ssz.h"
#include "ssz_object.h"
#include "ssz_reader.h"
#include "merkle.c"

typedef spy_unsafe$raw_ptr__json_parser$JsonDocument spy_raw_json_ptr;
typedef spy_unsafe$raw_ptr__ssz_reader$SszDocument spy_raw_ssz_document_ptr;
typedef spy_unsafe$raw_ptr__ssz_object$SszObject spy_raw_ssz_ptr;

static void spy_json_document_destroy(spy_raw_json_ptr opaque) {
    spy_json_parser$JsonDocument *document = opaque.p;
    if (document == NULL) return;
    /* JSON documents borrow the caller-owned input for synchronous lowering. */
    free(document->tokens.p);
    free(document);
}

static void spy_ssz_document_destroy(spy_raw_ssz_document_ptr opaque) {
    spy_ssz_reader$SszDocument *document = opaque.p;
    if (document == NULL) return;
    /* SSZ documents borrow the caller-owned input for synchronous lowering. */
    free(document);
}

spy_raw_ssz_ptr spy_schema_electra_decode_owned(spy_BytesObject *source) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_block$decode_electra_signed_block(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_block$decode_electra_signed_block_preset(source, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_ssz_owned(spy_BytesObject *source) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_block_ssz$decode_electra_signed_block_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_ssz_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_block_ssz$decode_electra_signed_block_ssz_preset(
            source, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_owned(spy_BytesObject *source) {
    spy_json_lowering$JsonDecodeResult result =
        spy_fulu_block$decode_fulu_signed_block(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_fulu_block$decode_fulu_signed_block_preset(source, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_owned(spy_BytesObject *source) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_fulu_block_ssz$decode_fulu_signed_block_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_fulu_block_ssz$decode_fulu_signed_block_ssz_preset(
            source, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_signing_decode_json_owned(
    spy_BytesObject *source, int32_t kind, int32_t schema, int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_signing$decode_signing_json(source, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_signing_decode_ssz_owned(
    spy_BytesObject *source, int32_t kind, int32_t schema, int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_signing$decode_signing_ssz(source, kind, schema, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_containers_decode_json_owned(
    spy_BytesObject *source, int32_t kind, int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_block_containers$decode_block_container_json(source, kind, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_containers_decode_ssz_owned(
    spy_BytesObject *source, int32_t kind, int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_block_containers_ssz$decode_block_container_ssz(source, kind, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

int32_t spy_ssz_object_hash_tree_root(
    spy_raw_ssz_ptr object, spy_BytesObject *output) {
    return spy_ssz_fast_object_hash_tree_root(object, output);
}
#define spy_schema_electra_ssz_size \
    spy_electra_block_encode$electra_ssz_size
#define spy_schema_electra_encode_ssz \
    spy_electra_block_encode$electra_encode_ssz
#define spy_schema_electra_json_size \
    spy_electra_block_encode$electra_json_size
#define spy_schema_electra_encode_json \
    spy_electra_block_encode$electra_encode_json
#define spy_schema_signing_ssz_size spy_electra_signing$signing_ssz_size
#define spy_schema_signing_encode_ssz spy_electra_signing$signing_encode_ssz
#define spy_schema_signing_json_size spy_electra_signing$signing_json_size
#define spy_schema_signing_encode_json spy_electra_signing$signing_encode_json
#define spy_schema_block_containers_json_size spy_electra_block_containers_encode$block_container_json_size
#define spy_schema_block_containers_encode_json spy_electra_block_containers_encode$block_container_encode_json
#define spy_ssz_object_clone_and_sign_block spy_ssz_object$clone_and_sign_block

static int32_t spy_ssz_child(spy_ssz_object$SszObject *obj,
                             int32_t node, int32_t child) {
    spy_ssz_object$SszNode current = obj->nodes.p[node];
    return obj->edges.p[current.first_edge + child];
}

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
    int32_t signed_block = spy_ssz_child(obj, contents, 0);
    int32_t proofs = spy_ssz_child(obj, contents, 1);
    int32_t blobs = spy_ssz_child(obj, contents, 2);
    int32_t saved_root = obj->root_node;
    obj->root_node = signed_block;
    int32_t block_size = spy_electra_block_encode$electra_ssz_size(opaque);
    obj->root_node = saved_root;
    return 12 + block_size + spy_ssz_fixed_list_size(obj, proofs)
        + spy_ssz_fixed_list_size(obj, blobs);
}

int32_t spy_schema_block_containers_encode_ssz(spy_raw_ssz_ptr opaque,
                                   spy_BytesObject *output) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj->object_kind != SPY_SSZ_OBJECT_SIGNED_BEACON_BLOCK_CONTENTS)
        return spy_electra_block_containers_encode$block_container_encode_ssz(opaque, output);
    int32_t contents = obj->root_node;
    int32_t signed_block = spy_ssz_child(obj, contents, 0);
    int32_t proofs = spy_ssz_child(obj, contents, 1);
    int32_t blobs = spy_ssz_child(obj, contents, 2);
    int32_t proof_size = spy_ssz_fixed_list_size(obj, proofs);
    int32_t saved_root = obj->root_node;
    obj->root_node = signed_block;
    int32_t block_size = spy_electra_block_encode$electra_ssz_size(opaque);
    uint32_t offsets[3] = {12, 12 + block_size,
                           12 + block_size + proof_size};
    memcpy(output->data.p, offsets, sizeof(offsets));
    spy_BytesObject block_output = {
        .length = output->length - 12,
        .hash = 0,
        .data = {.p = output->data.p + 12},
    };
    spy_electra_block_encode$electra_encode_ssz(opaque, &block_output);
    obj->root_node = saved_root;
    int32_t position = 12 + block_size;
    int32_t lists[2] = {proofs, blobs};
    for (int32_t list_index = 0; list_index < 2; list_index++) {
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

int32_t spy_ssz_object_is_valid(spy_raw_ssz_ptr opaque) {
    return opaque.p != NULL && opaque.p->valid;
}

int32_t spy_ssz_object_fork(spy_raw_ssz_ptr opaque) {
    return opaque.p->fork;
}

int32_t spy_ssz_object_preset(spy_raw_ssz_ptr opaque) {
    return opaque.p->preset;
}

int32_t spy_ssz_object_kind(spy_raw_ssz_ptr opaque) {
    return opaque.p->object_kind;
}

int32_t spy_ssz_object_schema(spy_raw_ssz_ptr opaque) {
    return opaque.p->schema_id;
}

int32_t spy_ssz_object_node_count(spy_raw_ssz_ptr opaque) {
    return opaque.p->node_count;
}

int32_t spy_ssz_object_hash_tree_root_path(
    spy_raw_ssz_ptr opaque, int32_t first, int32_t second, int32_t depth,
    spy_BytesObject *output) {
    spy_ssz_object$SszObject *obj = opaque.p;
    int32_t node = obj->root_node;
    if (depth > 0) {
        spy_ssz_object$SszNode current = obj->nodes.p[node];
        if (first < 0 || first >= current.child_count) return 0;
        node = obj->edges.p[current.first_edge + first];
    }
    if (depth > 1) {
        spy_ssz_object$SszNode current = obj->nodes.p[node];
        if (second < 0 || second >= current.child_count) return 0;
        node = obj->edges.p[current.first_edge + second];
    }
    return spy_ssz_fast_node_hash_tree_root(opaque, node, output);
}

int32_t spy_ssz_object_block_header(
    spy_raw_ssz_ptr opaque, spy_BytesObject *output) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj == NULL || output->length < 112) return 0;

    int32_t block = obj->root_node;
    if (obj->object_kind == SPY_SSZ_OBJECT_BEACON_BLOCK_CONTENTS)
        block = spy_ssz_child(obj, block, 0);
    else if (obj->object_kind != SPY_SSZ_OBJECT_BLINDED_BEACON_BLOCK)
        return 0;

    spy_ssz_object$SszNode block_node = obj->nodes.p[block];
    if (block_node.child_count != 5) return 0;
    int32_t slot = spy_ssz_child(obj, block, 0);
    int32_t proposer = spy_ssz_child(obj, block, 1);
    int32_t parent = spy_ssz_child(obj, block, 2);
    int32_t state = spy_ssz_child(obj, block, 3);
    int32_t body = spy_ssz_child(obj, block, 4);
    spy_ssz_object$SszNode slot_node = obj->nodes.p[slot];
    spy_ssz_object$SszNode proposer_node = obj->nodes.p[proposer];
    spy_ssz_object$SszNode parent_node = obj->nodes.p[parent];
    spy_ssz_object$SszNode state_node = obj->nodes.p[state];
    if (slot_node.data_length < 8 || proposer_node.data_length < 8 ||
        parent_node.data_length != 32 || state_node.data_length != 32)
        return 0;

    memcpy(output->data.p, obj->arena.p + slot_node.data_offset, 8);
    memcpy(output->data.p + 8, obj->arena.p + proposer_node.data_offset, 8);
    memcpy(output->data.p + 16, obj->arena.p + parent_node.data_offset, 32);
    memcpy(output->data.p + 48, obj->arena.p + state_node.data_offset, 32);
    spy_BytesObject body_root = {
        .length = 32,
        .hash = 0,
        .data = {.p = output->data.p + 80},
    };
    return spy_ssz_fast_node_hash_tree_root(opaque, body, &body_root);
}

void spy_ssz_object_destroy(spy_raw_ssz_ptr opaque) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj == NULL) return;
    free(obj->nodes.p);
    free(obj->edges.p);
    free(obj->arena.p);
    free(obj->work.p);
    free(obj->zeros.p);
    free(obj->state.p);
    free(obj->schedule.p);
    free(obj->root.p);
    free(obj->node_roots.p);
    free(obj->node_root_valid.p);
    free(obj);
}
