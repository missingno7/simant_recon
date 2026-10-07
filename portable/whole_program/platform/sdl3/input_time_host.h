#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_SDL3_INPUT_TIME_HOST_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_SDL3_INPUT_TIME_HOST_H

#include "../input_time.h"
#include "../../../platform/host.h"
#include "../pit_clock.h"

#include <stdint.h>

enum {
    PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY = 512,
    /* Observed canonical BIOS BDA80/82 = 001E/003E: sixteen words, with
     * one empty ring slot. Matches the pinned DOS BIOS input boundary. */
    PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY = 16,
    PORTABLE_INPUT_TIME_HOST_NUMLOCK_MASK = 0x20
};

typedef struct PortableSdlMonotonicClockRefresh
    PortableSdlMonotonicClockRefresh;

struct PortableSdlMonotonicClockRefresh {
    uint64_t last_ns;
    SimTimingClock *game_clock;
    SimTimingClock *bios_clock;
    uint8_t initialized;
};

typedef struct PortableInputTimeHost {
    PortableInputTime input_time;
    Host *host;                    /* borrowed; must outlive this binding */
    SimTimingClock *clock;          /* borrowed private game TickCount clock */
    SimTimingClock *bios_clock;     /* borrowed BDA clock; always enabled */
    HostEvent events[PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY];
    uint16_t key_words[PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY];
    uint16_t event_head, event_count;
    uint16_t key_head, key_count;
    uint8_t bios_keyboard_flags;    /* adapter-owned logical BDA flags */
    uint8_t bios_keyboard_flags_hi; /* BDA 40:18 depressed/left modifier bits */
    uint8_t suppress_bios_key;      /* IRQ09 carry-clear: flush after BIOS */
    uint8_t ingesting;
    uint8_t refreshing;
    uint8_t refresh_initialized;
    uint64_t last_refresh_ns;
    int (*interrupts_enabled)(void);
    uint8_t host_closed;
    uint8_t bound;
    uint8_t dual_clock_binding;
    int (*clock_refresh)(void *context, SimTimingClock *clock);
    void *clock_refresh_context;
    /* Optional observer for each newly ingested Host event. The event stays
     * in the retained FIFO; observation must not poll SDL. */
    int (*event_observer)(void *context, const HostEvent *event);
    void *event_observer_context;
    PortableSdlMonotonicClockRefresh monotonic_refresh;
} PortableInputTimeHost;

/* The host and clock are borrowed. The application remains the sole owner of
 * clock advancement and must not advance this clock a second time here. */
PortableInputTimeStatus portable_input_time_host_init(
    PortableInputTimeHost *binding, Host *host, SimTimingClock *clock);
/* Production binding: game and BIOS clocks have matching PIT cadence but
 * distinct tick counters. A single monotonic elapsed-time refresh advances
 * both, with BIOS counting enabled regardless of the private game flag. */
PortableInputTimeStatus portable_input_time_host_init_clocks(
    PortableInputTimeHost *binding, Host *host, SimTimingClock *game_clock,
    SimTimingClock *bios_clock);
PortableInputTimeStatus portable_input_time_host_bind(
    PortableInputTimeHost *binding);
void portable_input_time_host_shutdown(PortableInputTimeHost *binding);
/* Optional: source TickCount reads invoke this refresh before reading the
 * borrowed clock. Unset it when another application owner advances the clock. */
PortableInputTimeStatus portable_input_time_host_set_clock_refresh(
    PortableInputTimeHost *binding,
    int (*refresh)(void *context, SimTimingClock *clock), void *context);
PortableInputTimeStatus portable_input_time_host_set_event_observer(
    PortableInputTimeHost *binding,
    int (*observe)(void *context, const HostEvent *event), void *context);
PortableInputTimeStatus portable_input_time_host_refresh_clock(
    PortableInputTimeHost *binding);
/* Borrow the platform's existing CLI/STI flag. NULL permits delivery (the
 * default for isolated host-service controls). No new IF owner is introduced. */
void portable_input_time_host_set_interrupt_guard(
    PortableInputTimeHost *binding, int (*enabled)(void));
int portable_input_time_host_refresh_from_sdl_monotonic(
    void *context, SimTimingClock *clock);
void portable_sdl_monotonic_clock_refresh_init(
    PortableSdlMonotonicClockRefresh *refresh);
void portable_sdl_monotonic_clock_refresh_init_clocks(
    PortableSdlMonotonicClockRefresh *refresh,
    SimTimingClock *game_clock, SimTimingClock *bios_clock);

/* Host events are retained in source order, even when a BIOS key poll caused
 * the SDL queue to be drained. Return 1 for an event, 0 if empty, -1 on error. */
int portable_input_time_host_poll_event(PortableInputTimeHost *binding,
                                        HostEvent *event);
int portable_input_time_host_get_input_state(PortableInputTimeHost *binding,
                                             HostInputState *state);
int portable_input_time_host_dos_modifiers(PortableInputTimeHost *binding,
                                           uint8_t *modifiers);
int portable_input_time_host_current_modifiers(uint8_t *modifiers);

uint8_t portable_input_time_host_keyboard_flags(
    const PortableInputTimeHost *binding);
void portable_input_time_host_set_keyboard_flags(
    PortableInputTimeHost *binding, uint8_t flags);

uint8_t dos_keyboard_modifiers(void);

#endif
