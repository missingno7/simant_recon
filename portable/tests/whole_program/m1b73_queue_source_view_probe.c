#include "../../whole_program/platform/m1b73_queue_source.h"

#include <stdint.h>

struct Timer g_5FF2 = {{0, 0, 0, 0}, 0, 0, 0, 0, 0, 0};

int main(void)
{
    uint8_t slot;
    for (slot = 0; slot < PORTABLE_M1B73_QUEUE_COUNT; ++slot) {
        if (portable_m1b73_queue_slot(slot) !=
            &portable_m1b73_queue_set.queues[slot])
            return 1;
    }
    if (portable_m1b73_queue_slot(0xff) != 0)
        return 2;
    g_9120 = 0xbeef;
    if (portable_m1b73_g9120_low_byte() != 0xef)
        return 3;
    if (portable_m1b73_queue_set.queues[0].records !=
            portable_m1b73_queue_set.queue0_records ||
        portable_m1b73_queue_set.queues[1].records !=
            portable_m1b73_queue_set.queue1_records ||
        portable_m1b73_queue_set.queues[2].records !=
            portable_m1b73_queue_set.queue2_records ||
        portable_m1b73_queue_set.queues[3].records !=
            portable_m1b73_queue_set.queue3_records)
        return 4;
    return 0;
}
