#include <stdlib.h>

#include "json_parser.h"
#include "schema_deneb.h"
#include "schema_deneb_ssz.h"
#include "schema_electra.h"
#include "schema_electra_encode.h"
#include "schema_electra_ssz.h"
#include "schema_gloas.h"
#include "schema_gloas_ssz.h"
#include "ssz_object.h"
#include "ssz_reader.h"

typedef spy_unsafe$raw_ptr__json_parser$JsonDocument spy_raw_json_ptr;
typedef spy_unsafe$raw_ptr__ssz_reader$SszDocument spy_raw_ssz_document_ptr;
typedef spy_unsafe$raw_ptr__ssz_object$NativeSszObject spy_raw_ssz_ptr;

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

spy_raw_ssz_ptr spy_schema_electra_decode_ssz_owned(spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_electra_ssz$decode_electra_signed_block_ssz(source);
    spy_ssz_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_owned(spy_BytesObject *source) {
    spy_schema_deneb$DenebDecodeResult result =
        spy_schema_electra$decode_fulu_signed_block(source);
    spy_json_document_destroy(result.temporary);
    return result.object;
}

spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_owned(spy_BytesObject *source) {
    spy_schema_deneb_ssz$DenebSszDecodeResult result =
        spy_schema_electra_ssz$decode_fulu_signed_block_ssz(source);
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

#define spy_ssz_object_hash_tree_root spy_ssz_object$object_hash_tree_root
#define spy_schema_electra_ssz_size \
    spy_schema_electra_encode$electra_ssz_size
#define spy_schema_electra_encode_ssz \
    spy_schema_electra_encode$electra_encode_ssz
#define spy_schema_electra_json_size \
    spy_schema_electra_encode$electra_json_size
#define spy_schema_electra_encode_json \
    spy_schema_electra_encode$electra_encode_json

int32_t spy_ssz_object_is_valid(spy_raw_ssz_ptr opaque) {
    return opaque.p != NULL && opaque.p->valid;
}

int32_t spy_ssz_object_fork(spy_raw_ssz_ptr opaque) {
    return opaque.p->fork;
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

void spy_ssz_object_destroy(spy_raw_ssz_ptr opaque) {
    spy_ssz_object$NativeSszObject *obj = opaque.p;
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
