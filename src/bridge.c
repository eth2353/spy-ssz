#include <stdlib.h>

#include "json_parser.h"
#include "metadata.h"
#include "schema_deneb.h"
#include "schema_deneb_ssz.h"
#include "schema_electra.h"
#include "schema_electra_encode.h"
#include "schema_electra_ssz.h"
#include "schema_gloas.h"
#include "schema_gloas_ssz.h"
#include "schema_signing.h"
#include "schema_block_containers.h"
#include "schema_block_containers_encode.h"
#include "schema_block_containers_ssz.h"
#include "ssz_object.h"
#include "ssz_reader.h"

typedef spy_unsafe$raw_ptr__json_parser$JsonDocument spy_raw_json_ptr;
typedef spy_unsafe$raw_ptr__ssz_reader$SszDocument spy_raw_ssz_document_ptr;
typedef spy_unsafe$raw_ptr__ssz_object$SszObject spy_raw_ssz_ptr;

static void spy_json_document_destroy(spy_raw_json_ptr opaque) {
    spy_json_parser$JsonDocument *document = opaque.p;
    if (document == NULL) return;
    free(document->json.p);
    free(document->tokens.p);
    free(document);
}

static void spy_ssz_document_destroy(spy_raw_ssz_document_ptr opaque) {
    spy_ssz_reader$SszDocument *document = opaque.p;
    if (document == NULL) return;
    free(document->data.p);
    free(document);
}

spy_raw_ssz_ptr spy_schema_deneb_decode_owned(spy_BytesObject *source) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_deneb$decode_deneb_signed_block(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_deneb_decode_ssz_owned(spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_deneb_ssz$decode_deneb_signed_block_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_owned(
    spy_BytesObject *source) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_deneb$decode_deneb_attestation(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_ssz_owned(
    spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_deneb_ssz$decode_deneb_attestation_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_owned(spy_BytesObject *source) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_electra$decode_electra_signed_block(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_electra$decode_electra_signed_block_preset(source, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_ssz_owned(spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_electra_ssz$decode_electra_signed_block_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_electra_decode_ssz_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_electra_ssz$decode_electra_signed_block_ssz_preset(
            source, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_owned(spy_BytesObject *source) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_electra$decode_fulu_signed_block(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_electra$decode_fulu_signed_block_preset(source, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_owned(spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_electra_ssz$decode_fulu_signed_block_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_preset_owned(
    spy_BytesObject *source, int32_t preset) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_electra_ssz$decode_fulu_signed_block_ssz_preset(
            source, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_owned(
    spy_BytesObject *source) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_gloas$decode_gloas_attestation(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_ssz_owned(
    spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_gloas_ssz$decode_gloas_attestation_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_signing_decode_json_owned(
    spy_BytesObject *source, int32_t kind, int32_t schema, int32_t preset) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_signing$decode_signing_json(source, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_signing_decode_ssz_owned(
    spy_BytesObject *source, int32_t kind, int32_t schema, int32_t preset) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_signing$decode_signing_ssz(source, kind, schema, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_containers_decode_json_owned(
    spy_BytesObject *source, int32_t kind, int32_t preset) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_block_containers$decode_block_container_json(source, kind, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_block_containers_decode_ssz_owned(
    spy_BytesObject *source, int32_t kind, int32_t preset) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_block_containers_ssz$decode_block_container_ssz(source, kind, preset);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

#define spy_ssz_object_hash_tree_root spy_ssz_object$object_hash_tree_root
#define spy_schema_electra_ssz_size \
    spy_schema_electra_encode$electra_ssz_size
#define spy_schema_electra_encode_ssz \
    spy_schema_electra_encode$electra_encode_ssz
#define spy_schema_electra_json_size \
    spy_schema_electra_encode$electra_json_size
#define spy_schema_electra_encode_json \
    spy_schema_electra_encode$electra_encode_json
#define spy_schema_signing_ssz_size spy_schema_signing$signing_ssz_size
#define spy_schema_signing_encode_ssz spy_schema_signing$signing_encode_ssz
#define spy_schema_signing_json_size spy_schema_signing$signing_json_size
#define spy_schema_signing_encode_json spy_schema_signing$signing_encode_json
#define spy_schema_block_containers_json_size spy_schema_block_containers_encode$block_container_json_size
#define spy_schema_block_containers_encode_json spy_schema_block_containers_encode$block_container_encode_json

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
    if (obj->object_kind != spy_metadata$OBJECT_SIGNED_BEACON_BLOCK_CONTENTS)
        return spy_schema_block_containers_encode$block_container_ssz_size(opaque);
    int32_t contents = obj->root_node;
    int32_t signed_block = spy_ssz_child(obj, contents, 0);
    int32_t proofs = spy_ssz_child(obj, contents, 1);
    int32_t blobs = spy_ssz_child(obj, contents, 2);
    int32_t saved_root = obj->root_node;
    obj->root_node = signed_block;
    int32_t block_size = spy_schema_electra_encode$electra_ssz_size(opaque);
    obj->root_node = saved_root;
    return 12 + block_size + spy_ssz_fixed_list_size(obj, proofs)
        + spy_ssz_fixed_list_size(obj, blobs);
}

int32_t spy_schema_block_containers_encode_ssz(spy_raw_ssz_ptr opaque,
                                   spy_BytesObject *output) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj->object_kind != spy_metadata$OBJECT_SIGNED_BEACON_BLOCK_CONTENTS)
        return spy_schema_block_containers_encode$block_container_encode_ssz(opaque, output);
    int32_t contents = obj->root_node;
    int32_t signed_block = spy_ssz_child(obj, contents, 0);
    int32_t proofs = spy_ssz_child(obj, contents, 1);
    int32_t blobs = spy_ssz_child(obj, contents, 2);
    int32_t proof_size = spy_ssz_fixed_list_size(obj, proofs);
    int32_t saved_root = obj->root_node;
    obj->root_node = signed_block;
    int32_t block_size = spy_schema_electra_encode$electra_ssz_size(opaque);
    uint32_t offsets[3] = {12, 12 + block_size,
                           12 + block_size + proof_size};
    memcpy(output->data.p, offsets, sizeof(offsets));
    spy_BytesObject block_output = {
        .length = output->length - 12,
        .hash = 0,
        .data = {.p = output->data.p + 12},
    };
    spy_schema_electra_encode$electra_encode_ssz(opaque, &block_output);
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
    return spy_ssz_object$object_node_hash_tree_root(opaque, node, output);
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
    free(obj);
}
