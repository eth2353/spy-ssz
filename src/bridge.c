#include <limits.h>
#include <stdlib.h>
#include <string.h>

#include "json_parser.h"
#include "metadata.h"
#include "metadata_constants.h"
#include "json_lowering.h"
#include "ssz_lowering.h"
#include "electra_block.h"
#include "electra_block_encode.h"
#include "electra_block_ssz.h"
#include "electra_signing.h"
#include "electra_block_containers.h"
#include "electra_block_containers_encode.h"
#include "electra_block_containers_ssz.h"
#include "gloas_block.h"
#include "gloas_block_encode.h"
#include "gloas_block_ssz.h"
#include "gloas_signing.h"
#include "ssz_object.h"
#include "ssz_reader.h"
#include "decode_status.h"
#include "merkle.c"

typedef spy_unsafe$raw_ptr__json_parser$JsonDocument spy_raw_json_ptr;
typedef spy_unsafe$raw_ptr__ssz_reader$SszDocument spy_raw_ssz_document_ptr;
typedef spy_ssz_object$SszObject spy_ssz_object_handle;
typedef spy_unsafe$raw_ptr__ssz_object$SszObject spy_raw_ssz_ptr;

enum {
    SPY_SSZ_OFFSET_SIZE = 4,
    SPY_SSZ_UINT64_SIZE = 8,
    SPY_SSZ_ROOT_SIZE = 32,
    SPY_SIGNED_BLOCK_CONTENTS_FIELD_COUNT = 3,
    SPY_SIGNED_BLOCK_CONTENTS_FIXED_SIZE =
        SPY_SIGNED_BLOCK_CONTENTS_FIELD_COUNT * SPY_SSZ_OFFSET_SIZE,
    SPY_SIGNED_BLOCK_CONTENTS_LIST_COUNT = 2,
    SPY_BEACON_BLOCK_FIELD_COUNT = 5,
    SPY_BEACON_BLOCK_HEADER_SIZE =
        2 * SPY_SSZ_UINT64_SIZE + 3 * SPY_SSZ_ROOT_SIZE,
};

typedef enum {
    SPY_SIGNED_BLOCK_CONTENTS_BLOCK = 0,
    SPY_SIGNED_BLOCK_CONTENTS_PROOFS = 1,
    SPY_SIGNED_BLOCK_CONTENTS_BLOBS = 2,
} spy_signed_block_contents_field;

typedef enum {
    SPY_BEACON_BLOCK_SLOT = 0,
    SPY_BEACON_BLOCK_PROPOSER = 1,
    SPY_BEACON_BLOCK_PARENT_ROOT = 2,
    SPY_BEACON_BLOCK_STATE_ROOT = 3,
    SPY_BEACON_BLOCK_BODY = 4,
} spy_beacon_block_field;

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

spy_raw_ssz_ptr spy_schema_block_decode_json_owned(
    spy_BytesObject *source, int32_t fork, int32_t schema, int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_block$decode_signed_block(source, fork, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_decode_ssz_owned(
    spy_BytesObject *source, int32_t fork, int32_t schema, int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_block_ssz$decode_signed_block_ssz(
            source, fork, schema, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_signing_decode_json_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_signing$decode_signing_json(
            source, fork, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_signing_decode_ssz_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_signing$decode_signing_ssz(
            source, fork, kind, schema, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_signing_decode_json_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_gloas_signing$decode_gloas_signing_json(
            source, fork, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_signing_decode_ssz_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_gloas_signing$decode_gloas_signing_ssz(
            source, fork, kind, schema, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_block_decode_json_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_gloas_block$decode_gloas_block_json(
            source, fork, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_block_decode_ssz_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_gloas_block_ssz$decode_gloas_block_ssz(
            source, fork, kind, schema, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_containers_decode_json_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_electra_block_containers$decode_block_container_json(
            source, fork, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_containers_decode_ssz_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_electra_block_containers_ssz$decode_block_container_ssz(
            source, fork, kind, schema, preset);
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
#define spy_schema_gloas_ssz_size spy_gloas_block_encode$gloas_ssz_size
#define spy_schema_gloas_encode_ssz spy_gloas_block_encode$gloas_encode_ssz
#define spy_schema_gloas_json_size spy_gloas_block_encode$gloas_json_size
#define spy_schema_gloas_encode_json spy_gloas_block_encode$gloas_encode_json
#define spy_schema_block_containers_json_size spy_electra_block_containers_encode$block_container_json_size
#define spy_schema_block_containers_encode_json spy_electra_block_containers_encode$block_container_encode_json
#define spy_ssz_object_clone_and_sign_block spy_ssz_object$clone_and_sign_block
#define spy_ssz_object_compose_signing spy_electra_signing$compose_signing_object

typedef int32_t (*spy_json_sizer)(spy_raw_ssz_ptr object);
typedef int32_t (*spy_json_encoder)(spy_raw_ssz_ptr object,
                                    spy_BytesObject *output);

static int32_t spy_json_array_size(spy_raw_ssz_ptr *objects, int32_t count,
                                   spy_json_sizer sizer) {
    if (objects == NULL || count <= 0) return -1;
    int64_t total = (int64_t)count + 1;
    for (int32_t i = 0; i < count; i++) {
        if (objects[i].p == NULL) return -1;
        int32_t size = sizer(objects[i]);
        if (size < 0 || total > INT32_MAX - size) return -1;
        total += size;
    }
    return (int32_t)total;
}

static int32_t spy_json_array_encode(spy_raw_ssz_ptr *objects, int32_t count,
                                     spy_BytesObject *output,
                                     spy_json_encoder encoder) {
    if (objects == NULL || count <= 0 || output == NULL ||
        output->data.p == NULL || output->length < 2)
        return -1;
    int32_t position = 0;
    output->data.p[position++] = '[';
    for (int32_t i = 0; i < count; i++) {
        if (objects[i].p == NULL) return -1;
        if (i > 0) {
            if ((size_t)position >= output->length) return -1;
            output->data.p[position++] = ',';
        }
        spy_BytesObject item_output = {
            .length = output->length - (size_t)position,
            .hash = 0,
            .data = {.p = output->data.p + position},
        };
        int32_t written = encoder(objects[i], &item_output);
        if (written < 0 || (size_t)written > item_output.length) return -1;
        position += written;
    }
    if ((size_t)position >= output->length) return -1;
    output->data.p[position++] = ']';
    return position;
}

int32_t spy_schema_signing_json_array_size(spy_raw_ssz_ptr *objects,
                                           int32_t count) {
    return spy_json_array_size(objects, count, spy_schema_signing_json_size);
}

int32_t spy_schema_signing_encode_json_array(spy_raw_ssz_ptr *objects,
                                             int32_t count,
                                             spy_BytesObject *output) {
    return spy_json_array_encode(objects, count, output,
                                 spy_schema_signing_encode_json);
}

int32_t spy_schema_block_containers_json_array_size(
        spy_raw_ssz_ptr *objects, int32_t count) {
    return spy_json_array_size(objects, count,
                               spy_schema_block_containers_json_size);
}

int32_t spy_schema_block_containers_encode_json_array(
        spy_raw_ssz_ptr *objects, int32_t count, spy_BytesObject *output) {
    return spy_json_array_encode(objects, count, output,
                                 spy_schema_block_containers_encode_json);
}

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
    int32_t signed_block = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_BLOCK);
    int32_t proofs = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_PROOFS);
    int32_t blobs = spy_ssz_child(
        obj, contents, SPY_SIGNED_BLOCK_CONTENTS_BLOBS);
    int32_t saved_root = obj->root_node;
    obj->root_node = signed_block;
    int32_t block_size = spy_electra_block_encode$electra_ssz_size(opaque);
    obj->root_node = saved_root;
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
    int32_t saved_root = obj->root_node;
    obj->root_node = signed_block;
    int32_t block_size = spy_electra_block_encode$electra_ssz_size(opaque);
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
    spy_electra_block_encode$electra_encode_ssz(opaque, &block_output);
    obj->root_node = saved_root;
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

int32_t spy_ssz_object_is_valid(spy_raw_ssz_ptr opaque) {
    return opaque.p != NULL && opaque.p->status == SPY_SSZ_DECODE_VALID;
}

spy_ssz_decode_status spy_ssz_object_decode_status(spy_raw_ssz_ptr opaque) {
    return opaque.p == NULL
        ? SPY_SSZ_DECODE_MALFORMED_INPUT
        : (spy_ssz_decode_status)opaque.p->status;
}

int32_t spy_ssz_object_error_start(spy_raw_ssz_ptr opaque) {
    return opaque.p == NULL
        ? SPY_SSZ_ERROR_POSITION_UNSET
        : opaque.p->error_start;
}

int32_t spy_ssz_object_error_end(spy_raw_ssz_ptr opaque) {
    return opaque.p == NULL
        ? SPY_SSZ_ERROR_POSITION_UNSET
        : opaque.p->error_end;
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
    if (obj == NULL || output->length < SPY_BEACON_BLOCK_HEADER_SIZE) return 0;

    int32_t block = obj->root_node;
    if (obj->object_kind == SPY_SSZ_OBJECT_BEACON_BLOCK_CONTENTS)
        block = spy_ssz_child(obj, block, SPY_SIGNED_BLOCK_CONTENTS_BLOCK);
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
