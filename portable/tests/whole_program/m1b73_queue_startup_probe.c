#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../../whole_program/platform/m1b73_queues.h"
#include "../../whole_program/platform/m1b73_mouse_state.h"

/* Compile the actual startup caller with DOS width keywords mapped to the
 * portable compiler's 16-bit scalar width. Its call sequence is not copied. */
#define far
#define near
#define int short
#define Rect SourceRect
#include "../../../src/S17/m384C.c"
#undef Rect
#undef int
#undef near
#undef far

#include "../../whole_program/types/timer.h"

struct Timer g_5FF2 = {{0, 0, 0, 0x7777}, NULL, 0, 1, 2, 3, 4};

static unsigned call_log[8];
static unsigned call_count;
static int startup_ready_at_ratio_call;
struct SourceRect g_5A9C = {11, 12, 13, 14};

/* Other functions in this multi-member S17 TU are not called by the startup
 * case, but their source sections still need native link-time declarations. */
long **db_LoadObject(short object, short kind)
{
    (void)object;
    (void)kind;
    return NULL;
}

long *fd_55B3_6054;
short fd_50F6_46A8[16];
short fd_50F6_46BC[16];
short g_5FEA, g_5FEC, g_5FEE, g_5FE6, g_5FE8;
char g_3DDC, g_3DDE;

void db_UnhookObject(short object, short kind)
{
    (void)object;
    (void)kind;
}

short f_1FD2_0663(short draw)
{
    (void)draw;
    return 0;
}

void f_1B28_006A(short value)
{
    if (value != 0) call_log[call_count++] = 99;
    else call_log[call_count++] = 1;
}

void f_1B73_0046(void)
{
    call_log[call_count++] = 2;
}

void f_1B73_0235(void)
{
    call_log[call_count++] = 3;
}

void f_1B73_0218(short ratio_x, short ratio_y)
{
    call_log[call_count++] = 4;
    startup_ready_at_ratio_call =
        ratio_x == 0x10 && ratio_y == 0x10 &&
        g_5FF2.r.bottom == (int16_t)0x1f00 &&
        g_5FF2.fn == f_1B73_0CB3;
}

void f_1FD2_03EB(struct SourceRect *rect, short ticks)
{
    call_log[call_count++] = 5;
    if (rect != &g_5A9C || ticks != (short)0xff00)
        startup_ready_at_ratio_call = 0;
}

static unsigned callbacks;
static uint8_t seen_queue;
static uint8_t seen_record;
static uint16_t seen_status;
static int16_t seen_x, seen_y;
static int keep_scanning = 1;
static int mutate_after_first;

static int callback(void *context, uint8_t queue_index, uint8_t record_index,
                    const uint8_t record[18],
                    const PortableM1B73QueueEvent *event)
{
    const uint8_t expected_byte = 0x5a;
    if (context != &callbacks || record[12] != expected_byte)
        return 0;
    ++callbacks;
    seen_queue = queue_index;
    seen_record = record_index;
    seen_status = event->status;
    seen_x = event->x;
    seen_y = event->y;
    if (mutate_after_first != 0 && callbacks == 1) {
        g_9122 = 100;
        g_9124 = 120;
    }
    return keep_scanning;
}

static void put_word(uint8_t *where, uint16_t word)
{
    where[0] = (uint8_t)word;
    where[1] = (uint8_t)(word >> 8);
}

static void make_record(uint8_t *record, int16_t left, int16_t top,
                        int16_t right, int16_t bottom, uint16_t condition)
{
    memset(record, 0, 18);
    put_word(record + 0, (uint16_t)left);
    put_word(record + 2, (uint16_t)top);
    put_word(record + 4, (uint16_t)right);
    put_word(record + 6, (uint16_t)bottom);
    record[12] = 0x5a;
    put_word(record + 16, condition);
}

int main(void)
{
    PortableM1B73QueueServices services = {&callbacks, callback};
    PortableM1B73QueueSet *set = &portable_m1b73_queue_set;
    PortableM1B73QueueStatus status;

    if (set->queues[0].capacity != 4 || set->queues[0].allocated_record_count != 5 ||
        set->queues[1].capacity != 47 || set->queues[1].allocated_record_count != 48 ||
        set->queues[2].capacity != 47 || set->queues[2].allocated_record_count != 48 ||
        set->queues[3].capacity != 9 || set->queues[3].allocated_record_count != 10)
        return 1;
    g_9120 = 0xabcd;
    if (portable_m1b73_g9120_low_byte() != 0xcd)
        return 10;
    g_9120 = 0;
    set->queues[0].count = 3;
    set->queues[1].count = 6;
    set->queues[2].count = 7;
    set->queues[3].count = 8;

    o17_384C_0000();
    if (call_count != 5 || call_log[0] != 1 || call_log[1] != 2 ||
        call_log[2] != 3 || call_log[3] != 4 || call_log[4] != 5 ||
        startup_ready_at_ratio_call == 0 || set->queues[0].count != 0 ||
        set->queues[1].count != 0 || set->queues[2].count != 7 ||
        set->queues[3].count != 8 || g_5FF2.r.bottom != (int16_t)0x1f00 ||
        g_5FF2.fn != f_1B73_0CB3)
        return 2;

    /* An empty initialized queue dispatches without inventing a service. */
    if (portable_m1b73_queue_dispatch() != PORTABLE_M1B73_QUEUE_OK)
        return 3;
    if (!portable_m1b73_queues_bind(&services))
        return 4;
    g_9120 = 0x0201;
    g_9122 = 20;
    g_9124 = 30;
    make_record(set->queues[0].records[0], 20, 30, 20, 30, 0x0200);
    make_record(set->queues[0].records[1], 100, 120, 100, 120, 0x0200);
    set->queues[0].count = 2;
    keep_scanning = 1;
    mutate_after_first = 1;
    status = portable_m1b73_queue_dispatch();
    if (status != PORTABLE_M1B73_QUEUE_OK || callbacks != 2 || seen_queue != 0 ||
        seen_record != 1 || seen_status != 0x0201 || seen_x != 100 ||
        seen_y != 120 || g_9122 != 100 || g_9124 != 120)
        return 5;

    /* Descriptor mask 1Eh excludes event AH=01h; no resolver callback occurs. */
    callbacks = 0;
    mutate_after_first = 0;
    g_9120 = 0x0101;
    make_record(set->queues[2].records[0], 0, 0, 100, 100, 0xffff);
    set->queues[2].count = 1;
    if (portable_m1b73_queue_dispatch() != PORTABLE_M1B73_QUEUE_OK || callbacks != 0)
        return 6;

    /* AX=0 from a source callback ends the current queue scan but the caller
     * then advances to the next descriptor. */
    callbacks = 0;
    g_9120 = 0x0201;
    g_9122 = 20;
    g_9124 = 30;
    make_record(set->queues[0].records[0], 20, 30, 20, 30, 0x0200);
    make_record(set->queues[0].records[1], 20, 30, 20, 30, 0x0200);
    make_record(set->queues[1].records[0], 20, 30, 20, 30, 0x0200);
    set->queues[0].count = 2;
    set->queues[1].count = 1;
    set->queues[2].count = 0;
    keep_scanning = 0;
    status = portable_m1b73_queue_dispatch();
    if (status != PORTABLE_M1B73_QUEUE_OK ||
        callbacks != 2 || seen_queue != 1 || seen_record != 0) {
        fprintf(stderr, "callback-boundary status=%d calls=%u queue=%u row=%u counts=%u/%u/%u\n",
                (int)status, callbacks, seen_queue, seen_record,
                set->queues[0].count, set->queues[1].count, set->queues[2].count);
        return 7;
    }

    /* A matched opaque DOS callback pointer must fail when no native resolver
     * is bound; the implementation never calls it as a host address. */
    portable_m1b73_queues_unbind();
    g_9120 = 0x0201;
    set->queues[0].count = 1;
    make_record(set->queues[0].records[0], 20, 30, 20, 30, 0x0200);
    if (portable_m1b73_queue_dispatch() != PORTABLE_M1B73_QUEUE_PROVIDER_MISSING)
        return 8;
    set->queues[0].count = (uint16_t)(set->queues[0].capacity + 1u);
    if (portable_m1b73_queue_dispatch() != PORTABLE_M1B73_QUEUE_BAD_COUNT)
        return 9;

    puts("PASS: source o17_384C_0000 startup reaches f0AA3 and native m1B73 queue callback contract");
    return 0;
}
