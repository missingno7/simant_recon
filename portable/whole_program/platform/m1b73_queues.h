#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUES_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUES_H

#include <stdint.h>
#include <stddef.h>

enum {
    PORTABLE_M1B73_QUEUE_RECORD_BYTES = 18,
    PORTABLE_M1B73_QUEUE_COUNT = 4,
    PORTABLE_M1B73_QUEUE_HOTBOX_DISPATCH_COUNT = 3
};

typedef enum PortableM1B73QueueStatus {
    PORTABLE_M1B73_QUEUE_OK = 0,
    PORTABLE_M1B73_QUEUE_BAD_ARGUMENT,
    PORTABLE_M1B73_QUEUE_BAD_COUNT,
    PORTABLE_M1B73_QUEUE_PROVIDER_MISSING,
    PORTABLE_M1B73_QUEUE_PROVIDER_FAILED
} PortableM1B73QueueStatus;

/* Queue rows retain the source's opaque 18-byte record. The first four words
 * are the inclusive hot-box rectangle and word at +16 is the event mask.
 * Callback far pointers at +8 are never cast to native function pointers. */
typedef struct PortableM1B73Queue {
    uint16_t capacity; /* word immediately before source count */
    uint16_t count;
    uint8_t (*records)[PORTABLE_M1B73_QUEUE_RECORD_BYTES];
    uint8_t allocated_record_count;
} PortableM1B73Queue;

typedef struct PortableM1B73QueueSet {
    PortableM1B73Queue queues[PORTABLE_M1B73_QUEUE_COUNT];
    uint8_t queue0_records[5][PORTABLE_M1B73_QUEUE_RECORD_BYTES];
    uint8_t queue1_records[48][PORTABLE_M1B73_QUEUE_RECORD_BYTES];
    uint8_t queue2_records[48][PORTABLE_M1B73_QUEUE_RECORD_BYTES];
    uint8_t queue3_records[10][PORTABLE_M1B73_QUEUE_RECORD_BYTES];
} PortableM1B73QueueSet;

_Static_assert(sizeof(((PortableM1B73QueueSet *)0)->queue0_records) == 90,
               "Queue0 has five 18-byte rows");
_Static_assert(sizeof(((PortableM1B73QueueSet *)0)->queue1_records) == 864 &&
               sizeof(((PortableM1B73QueueSet *)0)->queue2_records) == 864,
               "middle queues each have forty-eight 18-byte rows");
_Static_assert(sizeof(((PortableM1B73QueueSet *)0)->queue3_records) == 180,
               "cursor hot-box queue has ten 18-byte rows");

typedef struct PortableM1B73QueueEvent {
    uint16_t status;
    int16_t x;
    int16_t y;
} PortableM1B73QueueEvent;

/* Return nonzero to continue the source-order descriptor walk; zero returns
 * immediately from f_1B73_0CB3, including when later descriptors match. */
typedef int (*PortableM1B73QueueCallback)(
    void *context, uint8_t queue_index, uint8_t record_index,
    const uint8_t record[PORTABLE_M1B73_QUEUE_RECORD_BYTES],
    const PortableM1B73QueueEvent *event);

typedef struct PortableM1B73QueueServices {
    void *context;
    PortableM1B73QueueCallback dispatch_record;
} PortableM1B73QueueServices;

/* Sole native owner for the ASM far queues. Capacities/record extents are
 * source-derived from m1B73.asm; applications borrow this storage. */
extern PortableM1B73QueueSet portable_m1b73_queue_set;

int portable_m1b73_queues_bind(const PortableM1B73QueueServices *services);
void portable_m1b73_queues_unbind(void);
PortableM1B73QueueStatus portable_m1b73_queue_dispatch(void);

/* Original root m1B73 entrypoints used by S17 startup and the Timer callback. */
void f_1B73_0AA3(void);
void f_1B73_0CB3(void);

#endif
