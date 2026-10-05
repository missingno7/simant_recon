#include "m1b73_queue_source.h"

#include <stdlib.h>
#include <string.h>

PortableM1B73Queue *portable_m1b73_queue_slot(uint8_t source_slot)
{
    if (source_slot >= PORTABLE_M1B73_QUEUE_COUNT)
        return 0;
    return &portable_m1b73_queue_set.queues[source_slot];
}

static int16_t read_record_word(const uint8_t *record, uint8_t offset)
{
    uint16_t bits = (uint16_t)((uint16_t)record[offset] |
                               ((uint16_t)record[offset + 1u] << 8));
    int16_t value;
    /* The recovered target is little-endian. memcpy avoids implementation-
     * defined unsigned-to-signed conversion for values above INT16_MAX. */
    memcpy(&value, &bits, sizeof(value));
    return value;
}

int16_t f_1B73_0C42(int16_t id, PortableM1B73Queue *slot,
                    PortableM1B73Rect *out_rect)
{
    uint16_t i;

    if (slot == NULL || out_rect == NULL || slot->records == NULL ||
        (*slot->capacity) == 0 || (*slot->capacity) > slot->allocated_record_count ||
        (*slot->count) > (*slot->capacity))
        abort();

    for (i = 0; i < (*slot->count); ++i) {
        const uint8_t *record = slot->records[i];
        if (read_record_word(record, 12) == id) {
            PortableM1B73Rect result;
            result.left = read_record_word(record, 0);
            result.top = read_record_word(record, 2);
            result.right = read_record_word(record, 4);
            result.bottom = read_record_word(record, 6);
            *out_rect = result;
            return 1;
        }
    }
    return 0;
}
