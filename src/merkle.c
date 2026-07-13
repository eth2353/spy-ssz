#include <stdint.h>
#include <string.h>

#include "decode_status.h"

void spy_sha256_pair(const uint8_t *source, uint8_t *output);

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
    SPY_KIND_BASIC_LIST = 10,
    SPY_NODE_ROOT_NOT_CACHED = 0,
    SPY_NODE_ROOT_CACHED = 1,
};

typedef struct {
    spy_ssz_object$SszObject *object;
    uint8_t stack[41][32];
    uint64_t occupied;
} spy_merkle_accumulator;

static int spy_merkle_depth(uint32_t limit) {
    int depth = 0;
    uint32_t width = 1;
    while (width < limit) {
        width <<= 1U;
        depth++;
    }
    return depth;
}

static void spy_hash_pair(
    const uint8_t left[32], const uint8_t right[32], uint8_t output[32]
) {
    uint8_t pair[64];
    memcpy(pair, left, 32);
    memcpy(pair + 32, right, 32);
    spy_sha256_pair(pair, output);
}

static void spy_merkle_push(
    spy_merkle_accumulator *accumulator,
    const uint8_t root[32],
    int level
) {
    uint8_t value[32];
    memcpy(value, root, 32);
    while ((accumulator->occupied & (1ULL << level)) != 0) {
        spy_hash_pair(accumulator->stack[level], value, value);
        accumulator->occupied &= ~(1ULL << level);
        level++;
    }
    memcpy(accumulator->stack[level], value, 32);
    accumulator->occupied |= 1ULL << level;
}

static void spy_merkle_finish(
    spy_merkle_accumulator *accumulator,
    uint32_t count,
    uint32_t limit,
    uint8_t output[32]
) {
    int depth = spy_merkle_depth(limit);
    uint64_t total = 1ULL << depth;
    uint64_t position = count;

    if (count == 0) {
        memcpy(output, accumulator->object->zeros.p->data.p + depth * 32, 32);
        return;
    }
    while (position < total) {
        uint64_t remaining = total - position;
        int aligned = 0;
        int available = 0;
        uint64_t cursor = position;
        while ((cursor & 1ULL) == 0 && aligned < depth) {
            aligned++;
            cursor >>= 1U;
        }
        while ((1ULL << (available + 1)) <= remaining) available++;
        if (available < aligned) aligned = available;
        spy_merkle_push(
            accumulator,
            accumulator->object->zeros.p->data.p + aligned * 32,
            aligned
        );
        position += 1ULL << aligned;
    }
    memcpy(output, accumulator->stack[depth], 32);
}

static int spy_fast_hash_node(
    spy_ssz_object$SszObject *object, int32_t node_index, uint8_t output[32]
);

static int spy_merkle_children(
    spy_ssz_object$SszObject *object,
    spy_ssz_object$SszNode *node,
    int32_t start,
    int32_t count,
    int32_t limit,
    uint8_t output[32]
) {
    spy_merkle_accumulator accumulator = {.object = object, .occupied = 0};
    uint8_t child[32];
    for (int32_t index = 0; index < count; index++) {
        int32_t child_index = object->edges.p[node->first_edge + start + index];
        if (!spy_fast_hash_node(object, child_index, child)) return 0;
        spy_merkle_push(&accumulator, child, 0);
    }
    spy_merkle_finish(&accumulator, (uint32_t)count, (uint32_t)limit, output);
    return 1;
}

static void spy_merkle_bytes(
    spy_ssz_object$SszObject *object,
    const uint8_t *data,
    int32_t byte_length,
    int32_t start_chunk,
    int32_t count,
    int32_t limit,
    uint8_t output[32]
) {
    spy_merkle_accumulator accumulator = {.object = object, .occupied = 0};
    uint8_t chunk[32];
    for (int32_t index = 0; index < count; index++) {
        int32_t offset = (start_chunk + index) * 32;
        int32_t remaining = byte_length - offset;
        int32_t take = remaining < 32 ? remaining : 32;
        memset(chunk, 0, 32);
        if (take > 0) memcpy(chunk, data + offset, (size_t)take);
        spy_merkle_push(&accumulator, chunk, 0);
    }
    spy_merkle_finish(&accumulator, (uint32_t)count, (uint32_t)limit, output);
}

static void spy_mix_length(
    const uint8_t root[32], int32_t length, uint8_t output[32]
) {
    uint8_t pair[64] = {0};
    uint32_t value = (uint32_t)length;
    memcpy(pair, root, 32);
    pair[32] = (uint8_t)value;
    pair[33] = (uint8_t)(value >> 8U);
    pair[34] = (uint8_t)(value >> 16U);
    pair[35] = (uint8_t)(value >> 24U);
    spy_sha256_pair(pair, output);
}

static int spy_progressive_children(
    spy_ssz_object$SszObject *object,
    spy_ssz_object$SszNode *node,
    uint8_t output[32]
) {
    uint8_t groups[20][32];
    uint8_t root[32] = {0};
    int32_t group_count = 0;
    int32_t position = 0;
    int32_t group_limit = 1;
    while (position < node->child_count) {
        int32_t remaining = node->child_count - position;
        int32_t take = remaining < group_limit ? remaining : group_limit;
        if (!spy_merkle_children(
            object, node, position, take, group_limit, groups[group_count]
        )) return 0;
        group_count++;
        position += take;
        group_limit *= 4;
    }
    for (int32_t index = group_count - 1; index >= 0; index--) {
        spy_hash_pair(groups[index], root, root);
    }
    memcpy(output, root, 32);
    return 1;
}

static void spy_progressive_bytes(
    spy_ssz_object$SszObject *object,
    const uint8_t *data,
    int32_t byte_length,
    int32_t chunk_count,
    uint8_t output[32]
) {
    uint8_t groups[20][32];
    uint8_t root[32] = {0};
    int32_t group_count = 0;
    int32_t position = 0;
    int32_t group_limit = 1;
    while (position < chunk_count) {
        int32_t remaining = chunk_count - position;
        int32_t take = remaining < group_limit ? remaining : group_limit;
        spy_merkle_bytes(
            object, data, byte_length, position, take, group_limit,
            groups[group_count]
        );
        group_count++;
        position += take;
        group_limit *= 4;
    }
    for (int32_t index = group_count - 1; index >= 0; index--) {
        spy_hash_pair(groups[index], root, root);
    }
    memcpy(output, root, 32);
}

static int spy_fast_hash_node(
    spy_ssz_object$SszObject *object, int32_t node_index, uint8_t output[32]
) {
    spy_ssz_object$SszNode *node;
    const uint8_t *data;
    uint8_t root[32];
    int32_t chunks;

    if (node_index < 0 || node_index >= object->node_count) return 0;
    if (!object->node_cache_initialized) {
        uint8_t *node_roots = realloc(
            object->node_roots.p, (size_t)object->node_count * 32
        );
        if (node_roots == NULL) {
            object->status = SPY_SSZ_DECODE_MALFORMED_INPUT;
            return 0;
        }
        object->node_roots.p = node_roots;
        uint8_t *node_root_valid = realloc(
            object->node_root_valid.p, (size_t)object->node_count
        );
        if (node_root_valid == NULL) {
            object->status = SPY_SSZ_DECODE_MALFORMED_INPUT;
            return 0;
        }
        object->node_root_valid.p = node_root_valid;
        memset(object->node_root_valid.p, SPY_NODE_ROOT_NOT_CACHED,
               (size_t)object->node_count);
        object->node_cache_initialized = true;
    }
    if (object->node_root_valid.p[node_index] == SPY_NODE_ROOT_CACHED) {
        memcpy(output, object->node_roots.p + node_index * 32, 32);
        return 1;
    }
    node = object->nodes.p + node_index;
    data = object->arena.p + node->data_offset;
    switch (node->kind) {
        case SPY_KIND_UINT:
            memcpy(root, data, 32);
            break;
        case SPY_KIND_FIXED_BYTES:
            chunks = (node->data_length + 31) / 32;
            spy_merkle_bytes(
                object, data, node->data_length, 0, chunks, chunks, root
            );
            break;
        case SPY_KIND_BYTE_LIST:
            chunks = (node->data_length + 31) / 32;
            spy_merkle_bytes(
                object, data, node->data_length, 0, chunks,
                (node->limit + 31) / 32, root
            );
            spy_mix_length(root, node->data_length, root);
            break;
        case SPY_KIND_BITLIST: {
            int32_t bytes = (node->data_length + 7) / 8;
            chunks = (node->data_length + 255) / 256;
            spy_merkle_bytes(
                object, data, bytes, 0, chunks,
                (node->limit + 255) / 256, root
            );
            spy_mix_length(root, node->data_length, root);
            break;
        }
        case SPY_KIND_BASIC_LIST:
            chunks = (node->data_length + 31) / 32;
            spy_merkle_bytes(
                object, data, node->data_length, 0, chunks,
                (node->limit * node->active_length + 31) / 32, root
            );
            spy_mix_length(root, node->data_length / node->active_length, root);
            break;
        case SPY_KIND_PROGRESSIVE_BITLIST: {
            int32_t bytes = (node->data_length + 7) / 8;
            chunks = (node->data_length + 255) / 256;
            spy_progressive_bytes(object, data, bytes, chunks, root);
            spy_mix_length(root, node->data_length, root);
            break;
        }
        case SPY_KIND_CONTAINER:
            if (!spy_merkle_children(
                object, node, 0, node->child_count, node->child_count, root
            )) return 0;
            break;
        case SPY_KIND_LIST:
            if (!spy_merkle_children(
                object, node, 0, node->child_count, node->limit, root
            )) return 0;
            spy_mix_length(root, node->child_count, root);
            break;
        case SPY_KIND_PROGRESSIVE_LIST:
            if (!spy_progressive_children(object, node, root)) return 0;
            spy_mix_length(root, node->child_count, root);
            break;
        case SPY_KIND_PROGRESSIVE_CONTAINER: {
            uint8_t pair[64] = {0};
            int32_t active_bytes = (node->active_length + 7) / 8;
            if (!spy_progressive_children(object, node, root)) return 0;
            memcpy(pair, root, 32);
            memcpy(pair + 32, object->arena.p + node->active_offset,
                   (size_t)active_bytes);
            spy_sha256_pair(pair, root);
            break;
        }
        default:
            return 0;
    }
    memcpy(object->node_roots.p + node_index * 32, root, 32);
    object->node_root_valid.p[node_index] = SPY_NODE_ROOT_CACHED;
    memcpy(output, root, 32);
    return 1;
}

static int32_t spy_ssz_fast_node_hash_tree_root(
    spy_unsafe$raw_ptr__ssz_object$SszObject opaque,
    int32_t node_index,
    spy_BytesObject *output
) {
    if (opaque.p == NULL || output->length < 32) return 0;
    return spy_fast_hash_node(opaque.p, node_index, output->data.p);
}

static int32_t spy_ssz_fast_object_hash_tree_root(
    spy_unsafe$raw_ptr__ssz_object$SszObject opaque,
    spy_BytesObject *output
) {
    spy_ssz_object$SszObject *object = opaque.p;
    if (object == NULL || output->length < 32) return 0;
    if (!object->root_valid) {
        if (!spy_fast_hash_node(object, object->root_node, object->root.p->data.p))
            return 0;
        object->root_valid = true;
    }
    memcpy(output->data.p, object->root.p->data.p, 32);
    return object->status;
}
