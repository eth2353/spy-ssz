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
#include "gloas_payload_envelope.h"
#include "gloas_payload_envelope_encode.h"
#include "gloas_payload_envelope_ssz.h"
#include "gloas_signing.h"
#include "ssz_object.h"
#include "ssz_reader.h"
#include "decode_status.h"
#include "bridge_internal.h"
#include "merkle.c"

typedef spy_unsafe$raw_ptr__json_parser$JsonDocument spy_raw_json_ptr;
typedef spy_unsafe$raw_ptr__ssz_reader$SszDocument spy_raw_ssz_document_ptr;

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

spy_raw_ssz_ptr spy_schema_gloas_payload_envelope_decode_json_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_json_lowering$JsonDecodeResult result =
        spy_gloas_payload_envelope$decode_gloas_payload_envelope_json(
            source, fork, kind, schema, preset);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_gloas_payload_envelope_decode_ssz_owned(
    spy_BytesObject *source, int32_t fork, int32_t kind, int32_t schema,
    int32_t preset) {
    spy_ssz_lowering$SszDecodeResult result =
        spy_gloas_payload_envelope_ssz$decode_gloas_payload_envelope_ssz(
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
#define spy_schema_gloas_payload_envelope_ssz_size spy_gloas_payload_envelope_encode$gloas_payload_envelope_ssz_size
#define spy_schema_gloas_payload_envelope_encode_ssz spy_gloas_payload_envelope_encode$gloas_payload_envelope_encode_ssz
#define spy_schema_gloas_payload_envelope_json_size spy_gloas_payload_envelope_encode$gloas_payload_envelope_json_size
#define spy_schema_gloas_payload_envelope_encode_json spy_gloas_payload_envelope_encode$gloas_payload_envelope_encode_json
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

void spy_ssz_object_destroy(spy_raw_ssz_ptr opaque) {
    spy_ssz_object$SszObject *obj = opaque.p;
    if (obj == NULL) return;
    free(obj->nodes.p);
    free(obj->edges.p);
    free(obj->arena.p);
    free(obj->work.p);
    free(obj->zeros.p);
    free(obj->root.p);
    free(obj->node_roots.p);
    free(obj->node_root_valid.p);
    free(obj);
}
