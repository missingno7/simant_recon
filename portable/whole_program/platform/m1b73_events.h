#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_EVENTS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_EVENTS_H

#include "sdl3/input_time_host.h"

#include <stdint.h>

enum {
    PORTABLE_M1B73_EVENT_SLOTS = 7,
    PORTABLE_M1B73_EVENT_MAX_COUNT = 6
};

/* Eight consecutive 16-bit source Event words (16-byte DOS record). */
typedef struct PortableM1B73Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    uint8_t modLo;
    uint8_t modHi;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
} PortableM1B73Event;

typedef struct PortableM1B73Events {
    PortableInputTimeHost *input_host; /* borrowed shared event-queue owner */
    SimTimingClock *clock;             /* same application clock as TickCount */
    int16_t *source_capacity;            /* borrowed typed alias of g_5FF0 */
    int16_t *source_count;               /* g_5FF2.r.left */
    int16_t *source_write_index;         /* g_5FF2.r.top */
    int16_t *source_read_index;          /* g_5FF2.r.right */
    uint8_t *source_shift_state;          /* m1B73 code-segment shift_state */
    PortableM1B73Event *source_records; /* borrowed DS:[g_5FFE] record span */
    uint16_t source_record_slots;
    uint8_t bound;
} PortableM1B73Events;

void portable_m1b73_events_init(PortableM1B73Events *events,
                                PortableInputTimeHost *input_host,
                                SimTimingClock *clock,
                                int16_t *source_capacity,
                                int16_t *source_count,
                                int16_t *source_write_index,
                                int16_t *source_read_index,
                                uint8_t *source_shift_state,
                                PortableM1B73Event *source_records,
                                uint16_t source_record_slots);
int portable_m1b73_events_bind(PortableM1B73Events *events);
void portable_m1b73_events_unbind(PortableM1B73Events *events);

/* Source f_1B73_036E register effects. The event's `what` word is untouched.
 * Fields receive BDA keyboard flags, BDA BIOS ticks, and AX/CX/DX/ES:BX;
 * source shift_state bit 7 is ORed into message bit 0 and can be cleared by
 * AX.AH bits 1 or 3. Returns 1 when enqueued, 0 when full. */
int portable_m1b73_event_enqueue_registers(PortableM1B73Events *events,
                                           uint16_t ax, uint16_t cx,
                                           uint16_t dx, uint16_t bx,
                                           uint16_t es);
uint16_t portable_m1b73_event_count(const PortableM1B73Events *events);
int16_t portable_m1b73_event_dequeue(PortableM1B73Events *events,
                                     PortableM1B73Event *event);

/* One-consumer host access. This polls the retained SDL queue owned by
 * PortableInputTimeHost and never reads SDL directly. */
int portable_m1b73_poll_host_event(PortableM1B73Events *events,
                                   HostEvent *event);
int portable_m1b73_poll_mouse(PortableM1B73Events *events,
                              HostInputState *state);

/* Original root m1B73 public entrypoints in the native whole-program lane. */
uint32_t TickCount(void);
int16_t f_1B73_032A(void);
int16_t f_1B73_032E(void *event_record);
void f_1B73_0511(void);
void f_1B73_0518(void);

#endif
