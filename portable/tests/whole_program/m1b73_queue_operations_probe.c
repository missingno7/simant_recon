#include "../../whole_program/platform/m1b73_events.h"
#include "../../whole_program/platform/m1b73_queue_source.h"

#include <stdint.h>
#include <string.h>

struct Timer g_5FF2 = {{0, 0, 0, 0}, 0, 0, 0, 0, 0, 0};
uint16_t g_9120;
int16_t g_9122;
int16_t g_9124;

static uint8_t keyboard_flags = 0x24;
static uint32_t bios_ticks = 0x12345678;

int portable_input_time_host_current_modifiers(uint8_t *modifiers)
{
    if (modifiers == NULL)
        return 0;
    *modifiers = keyboard_flags;
    return 1;
}

uint32_t f_1F58_0006(void) { return bios_ticks; }
PortableInputTimeStatus portable_input_time_host_refresh_clock(
    PortableInputTimeHost *binding)
{ (void)binding; return PORTABLE_INPUT_TIME_OK; }
int portable_input_time_host_poll_event(PortableInputTimeHost *binding,
                                        HostEvent *event)
{ (void)binding; (void)event; return 0; }
int portable_input_time_host_get_input_state(PortableInputTimeHost *binding,
                                             HostInputState *state)
{ (void)binding; (void)state; return 0; }
uint32_t sim_timing_tick_count(const SimTimingClock *clock)
{ (void)clock; return 0; }
void sim_timing_set_tick_count_enabled(SimTimingClock *clock, int enabled)
{ (void)clock; (void)enabled; }

static void put_word(uint8_t *record, uint8_t offset, uint16_t word)
{
    record[offset] = (uint8_t)word;
    record[offset + 1u] = (uint8_t)(word >> 8);
}

static int test_rect_output(void)
{
    PortableM1B73Queue *queue = portable_m1b73_queue_slot(0);
    PortableM1B73Rect output;
    uint8_t *record = queue->records[0];
    memset(record, 0, PORTABLE_M1B73_QUEUE_RECORD_BYTES);
    queue->count = 1;
    put_word(record, 0, 0xfffe);
    put_word(record, 2, 0x0011);
    put_word(record, 4, 0x1234);
    put_word(record, 6, 0x8001);
    put_word(record, 12, 0xabcd);
    output = (PortableM1B73Rect){ 1, 2, 3, 4 };
    if (f_1B73_0C42((int16_t)0xabcd, queue, &output) != 1 ||
        (uint16_t)output.left != 0xfffe || output.top != 0x0011 ||
        output.right != 0x1234 || (uint16_t)output.bottom != 0x8001)
        return 1;
    output = (PortableM1B73Rect){ 5, 6, 7, 8 };
    if (f_1B73_0C42((int16_t)0x1111, queue, &output) != 0 ||
        output.left != 5 || output.top != 6 ||
        output.right != 7 || output.bottom != 8)
        return 2;
    queue->count = 0;
    return 0;
}

static int test_typed_event_words(void)
{
    SimTimingClock clock;
    PortableInputTimeHost input_host;
    PortableM1B73Events events;
    PortableM1B73Event records[PORTABLE_M1B73_EVENT_SLOTS];
    PortableM1B73Event output;
    int16_t capacity = PORTABLE_M1B73_EVENT_SLOTS;
    int16_t count = 0, write_index = 0, read_index = 0;
    uint8_t shift_state = 0;

    memset(&clock, 0, sizeof(clock));
    memset(&input_host, 0, sizeof(input_host));
    memset(records, 0, sizeof(records));
    input_host.bound = 1;
    records[0].what = (int16_t)0x6677;
    portable_m1b73_events_init(&events, &input_host, &clock, &capacity,
        &count, &write_index, &read_index, &shift_state, records,
        PORTABLE_M1B73_EVENT_SLOTS);
    if (!portable_m1b73_events_bind(&events))
        return 3;

    f_1B73_030F((int16_t)0x3344, (int16_t)0x1122,
                (int16_t)0x0102, (int16_t)0x1357, (int16_t)0x2468);
    if (count != 1 || f_1B73_032E(&output) != 0 ||
        output.what != (int16_t)0x6677 ||
        (uint16_t)output.message != 0x0024 ||
        (uint16_t)output.x4 != 0x5678 ||
        (uint16_t)(((uint16_t)output.modHi << 8) | output.modLo) != 0x0102 ||
        output.h != 0x1357 || output.v != 0x2468 ||
        output.code != 0x3344 || output.xE != 0x1122)
        goto fail;

    f_1B73_030F((int16_t)0xfe01, 0, 0, 0, 0);
    if (count != 1 || f_1B73_032E(&output) != 0 ||
        output.code != (int16_t)0xfe01 || output.v != 0)
        goto fail;
    portable_m1b73_events_unbind(&events);
    return 0;
fail:
    portable_m1b73_events_unbind(&events);
    return 4;
}

int main(void)
{
    int result = test_rect_output();
    if (result != 0)
        return result;
    result = test_typed_event_words();
    return result;
}
