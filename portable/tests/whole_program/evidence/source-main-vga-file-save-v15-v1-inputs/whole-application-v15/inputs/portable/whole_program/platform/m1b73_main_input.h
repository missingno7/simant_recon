#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MAIN_INPUT_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MAIN_INPUT_H

#include "m1b73_events.h"
#include "m1b73_timer_view.h"

/* Bind the original root:m1FD2 event queue owner and m1B73 private state to
 * the shared host input/timing provider. The queue records are a separately
 * owned native span, not a cast of DOS DS:91B0. */
int portable_m1b73_bind_source_main_input(
    PortableM1B73Events *events,
    PortableInputTimeHost *input_host,
    SimTimingClock *clock,
    uint8_t *source_shift_state,
    PortableM1B73Event *native_records,
    uint16_t native_record_slots);
void portable_m1b73_unbind_source_main_input(
    PortableM1B73Events *events);

/* Logical source queries backed by the same retained SDL input provider.
 * Scan codes must be in the original 0..127 key-state table domain. */
int16_t f_1B73_0A30(uint16_t scan_code);
int16_t f_1B73_0EEE(void);

#endif
