#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "bridge_internal.h"

/* Private traversal state. Sizing uses the same preorder walk as copying, with
 * null output buffers. Python holds its owner lock across both calls. */
typedef struct {
    spy_ssz_object$SszObject *object;
    spy_projection_node *nodes;
    uint8_t *data;
    int32_t node_capacity;
    int32_t data_capacity;
    int32_t node_count;
    int32_t data_length;
} spy_projection_copy;

static int spy_projection_visit(spy_projection_copy *copy, int32_t index) {
    spy_ssz_object$SszObject *obj = copy->object;
    if (index < 0 || index >= obj->node_count) return 0;
    spy_ssz_object$SszNode node = obj->nodes.p[index];
    int bits = node.kind == SPY_KIND_BITLIST ||
               node.kind == SPY_KIND_PROGRESSIVE_BITLIST;
    int32_t length = bits ? node.data_length / 8 + 1 : node.data_length;
    int32_t stored = bits ? node.data_length / 8 + (node.data_length % 8 != 0) : length;
    if (length < 0 || length > INT32_MAX - copy->data_length ||
        copy->node_count == INT32_MAX || node.data_offset < 0 ||
        node.data_offset > obj->arena_cursor ||
        stored > obj->arena_cursor - node.data_offset) return 0;
    int32_t end = copy->data_length + length;
    if (copy->nodes != NULL) {
        if (copy->node_count >= copy->node_capacity || end > copy->data_capacity)
            return 0;
        spy_projection_node *record = &copy->nodes[copy->node_count];
        record->kind = node.kind;
        record->data_length = length;
        record->child_count = node.child_count;
        record->element_width = node.active_length;
        if (stored > 0)
            memcpy(copy->data + copy->data_length, obj->arena.p + node.data_offset, stored);
        if (bits) {
            if (node.data_length % 8 == 0) copy->data[end - 1] = 0;
            copy->data[end - 1] |= 1 << (node.data_length % 8);
        }
    }
    copy->node_count++;
    copy->data_length = end;
    for (int32_t child = 0; child < node.child_count; child++) {
        if (!spy_projection_visit(copy, obj->edges.p[node.first_edge + child]))
            return 0;
    }
    return 1;
}

static int32_t spy_projection_field(spy_ssz_object$SszObject *obj, int32_t field) {
    if (obj == NULL || obj->root_node < 0 || obj->root_node >= obj->node_count)
        return -1;
    spy_ssz_object$SszNode root = obj->nodes.p[obj->root_node];
    if (field < 0 || field >= root.child_count) return -1;
    return obj->edges.p[root.first_edge + field];
}

int32_t spy_ssz_object_projection_size(
    spy_raw_ssz_ptr opaque, int32_t field, int32_t *sizes) {
    int32_t node = spy_projection_field(opaque.p, field);
    if (node < 0 || sizes == NULL) return 0;
    spy_projection_copy copy = {.object = opaque.p};
    if (!spy_projection_visit(&copy, node)) return 0;
    sizes[0] = copy.node_count;
    sizes[1] = copy.data_length;
    return 1;
}

int32_t spy_ssz_object_projection_copy(
    spy_raw_ssz_ptr opaque, int32_t field, spy_projection_node *nodes,
    int32_t node_count, spy_BytesObject *output) {
    int32_t node = spy_projection_field(opaque.p, field);
    if (node < 0 || nodes == NULL || node_count < 1 || output == NULL ||
        output->length > INT32_MAX)
        return 0;
    spy_projection_copy copy = {
        .object = opaque.p, .nodes = nodes, .data = output->data.p,
        .node_capacity = node_count, .data_capacity = output->length
    };
    if (!spy_projection_visit(&copy, node)) return 0;
    return copy.node_count == node_count && copy.data_length == output->length;
}
