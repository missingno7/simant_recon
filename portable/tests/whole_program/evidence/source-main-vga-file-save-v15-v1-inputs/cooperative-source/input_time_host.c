#include "input_time_host.h"

#include <stdlib.h>
#include <stddef.h>
#include <string.h>

static PortableInputTimeHost *active_host_binding;

static int push_event(PortableInputTimeHost *binding, const HostEvent *event)
{
    uint16_t tail;
    if (binding->event_count >= PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY)
        return 0;
    tail = (uint16_t)((binding->event_head + binding->event_count) %
                      PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY);
    binding->events[tail] = *event;
    ++binding->event_count;
    return 1;
}

static int push_key(PortableInputTimeHost *binding, uint16_t key)
{
    uint16_t tail;
    if (binding->key_count >= PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY)
        return 0;
    tail = (uint16_t)((binding->key_head + binding->key_count) %
                      PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY);
    binding->key_words[tail] = key;
    ++binding->key_count;
    return 1;
}

static int pop_key(PortableInputTimeHost *binding, uint16_t *key)
{
    if (binding->key_count == 0)
        return 0;
    *key = binding->key_words[binding->key_head];
    binding->key_head = (uint16_t)((binding->key_head + 1u) %
                                   PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY);
    --binding->key_count;
    return 1;
}

/* Poll each SDL event exactly once, preserving its order for the logical
 * event adapter while separately queuing keyboard transitions for BIOS APIs. */
static int ingest_host_events(PortableInputTimeHost *binding)
{
    HostEvent event;
    int polled;
    do {
        polled = host_poll_event(binding->host, &event);
        if (polled < 0) {
            binding->host_closed = 1;
            return -1;
        }
        if (polled == 0)
            return 1;
        event.tick = sim_timing_tick_count(binding->clock);
        if (!push_event(binding, &event)) {
            binding->host_closed = 1;
            return -1;
        }
        if (binding->event_observer != NULL &&
            !binding->event_observer(binding->event_observer_context,
                                     &event)) {
            binding->host_closed = 1;
            return -1;
        }
        if (event.kind == HOST_EVENT_QUIT)
            binding->host_closed = 1;
        if (event.kind == HOST_EVENT_KEY_DOWN &&
            !push_key(binding, event.key)) {
            binding->host_closed = 1;
            return -1;
        }
    } while (1);
}

static int host_ticks(void *context, uint32_t *ticks)
{
    PortableInputTimeHost *binding = (PortableInputTimeHost *)context;
    if (binding == NULL || binding->bios_clock == NULL || ticks == NULL)
        return 0;
    if (portable_input_time_host_refresh_clock(binding) !=
        PORTABLE_INPUT_TIME_OK)
        return 0;
    *ticks = sim_timing_tick_count(binding->bios_clock);
    return 1;
}

static int host_key_available(void *context, uint16_t *key)
{
    PortableInputTimeHost *binding = (PortableInputTimeHost *)context;
    if (binding == NULL || key == NULL)
        return -1;
    /* BIOS polling is also the yield boundary for source modal loops. Refresh
     * through the application owner first: it advances the monotonic clocks,
     * drains/replays host input, dispatches retained events, and presents as
     * appropriate. Its refresh guard makes the nested key-availability check
     * below nonrecursive; the SDL queue is still ingested only once. */
    if (portable_input_time_host_refresh_clock(binding) !=
        PORTABLE_INPUT_TIME_OK)
        return -1;
    if (ingest_host_events(binding) < 0)
        return -1;
    if (binding->key_count == 0)
        return 0;
    *key = binding->key_words[binding->key_head];
    return 1;
}

static int host_read_key_blocking(void *context, uint16_t *key)
{
    PortableInputTimeHost *binding = (PortableInputTimeHost *)context;
    if (binding == NULL || key == NULL)
        return -1;
    for (;;) {
        /* Blocking DOS reads must yield too. In particular, the original menu
         * selector waits here while the outer source loop is suspended. */
        if (portable_input_time_host_refresh_clock(binding) !=
            PORTABLE_INPUT_TIME_OK)
            return -1;
        if (ingest_host_events(binding) < 0)
            return -1;
        if (pop_key(binding, key))
            return 1;
        if (binding->host_closed)
            return -1;
        host_wait_ms(1);
    }
}

static int clear_logical_numlock(void *context)
{
    PortableInputTimeHost *binding = (PortableInputTimeHost *)context;
    if (binding == NULL)
        return 0;
    binding->bios_keyboard_flags = (uint8_t)(binding->bios_keyboard_flags &
        (uint8_t)~PORTABLE_INPUT_TIME_HOST_NUMLOCK_MASK);
    return 1;
}

static PortableInputTimeStatus input_time_host_init_common(
    PortableInputTimeHost *binding, Host *host, SimTimingClock *game_clock,
    SimTimingClock *bios_clock, int dual_clock_binding)
{
    PortableInputTimeServices services;
    if (binding == NULL || host == NULL || game_clock == NULL ||
        bios_clock == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    memset(binding, 0, sizeof(*binding));
    memset(&services, 0, sizeof(services));
    services.context = binding;
    services.read_logical_bios_ticks = host_ticks;
    services.key_available = host_key_available;
    services.read_key_blocking = host_read_key_blocking;
    services.clear_numlock_state = clear_logical_numlock;
    /* DOS IVT/atexit vector services are deliberately unprovided. */
    binding->host = host;
    binding->clock = game_clock;
    binding->bios_clock = bios_clock;
    binding->dual_clock_binding = (uint8_t)(dual_clock_binding != 0);
    portable_input_time_init(&binding->input_time, &services);
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_host_init(
    PortableInputTimeHost *binding, Host *host, SimTimingClock *clock)
{
    return input_time_host_init_common(binding, host, clock, clock, 0);
}

static int same_pit_cadence(const SimTimingClock *a,
                            const SimTimingClock *b)
{
    return a != NULL && b != NULL &&
        a->pit_input_numerator == b->pit_input_numerator &&
        a->pit_input_denominator == b->pit_input_denominator &&
        a->pit_divisor_counts == b->pit_divisor_counts &&
        a->interrupts_per_tick == b->interrupts_per_tick;
}

PortableInputTimeStatus portable_input_time_host_init_clocks(
    PortableInputTimeHost *binding, Host *host, SimTimingClock *game_clock,
    SimTimingClock *bios_clock)
{
    PortableInputTimeStatus status;
    if (game_clock == NULL || bios_clock == NULL || game_clock == bios_clock ||
        !same_pit_cadence(game_clock, bios_clock))
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    status = input_time_host_init_common(binding, host, game_clock, bios_clock, 1);
    if (status != PORTABLE_INPUT_TIME_OK)
        return status;
    sim_timing_set_tick_count_enabled(bios_clock, 1);
    portable_sdl_monotonic_clock_refresh_init_clocks(
        &binding->monotonic_refresh, game_clock, bios_clock);
    binding->clock_refresh = portable_input_time_host_refresh_from_sdl_monotonic;
    binding->clock_refresh_context = &binding->monotonic_refresh;
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_host_bind(
    PortableInputTimeHost *binding)
{
    PortableInputTimeStatus status;
    if (binding == NULL || binding->host == NULL || binding->clock == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (binding->dual_clock_binding) {
        if (binding->bios_clock == NULL || binding->bios_clock == binding->clock ||
            !same_pit_cadence(binding->clock, binding->bios_clock))
            return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
        sim_timing_set_tick_count_enabled(binding->bios_clock, 1);
    }
    if (binding->bound)
        return PORTABLE_INPUT_TIME_INVALID_LIFETIME;
    status = portable_input_time_bind(&binding->input_time);
    if (status == PORTABLE_INPUT_TIME_OK) {
        binding->bound = 1;
        active_host_binding = binding;
    }
    return status;
}

void portable_input_time_host_shutdown(PortableInputTimeHost *binding)
{
    if (binding == NULL)
        return;
    if (binding->bound) {
        if (active_host_binding == binding)
            active_host_binding = NULL;
        portable_input_time_unbind(&binding->input_time);
        binding->bound = 0;
    }
}

PortableInputTimeStatus portable_input_time_host_set_clock_refresh(
    PortableInputTimeHost *binding,
    int (*refresh)(void *context, SimTimingClock *clock), void *context)
{
    if (binding == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (binding->bound)
        return PORTABLE_INPUT_TIME_INVALID_LIFETIME;
    binding->clock_refresh = refresh;
    binding->clock_refresh_context = context;
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_host_set_event_observer(
    PortableInputTimeHost *binding,
    int (*observe)(void *context, const HostEvent *event), void *context)
{
    if (binding == NULL || binding->bound)
        return binding == NULL ? PORTABLE_INPUT_TIME_BAD_ARGUMENT :
            PORTABLE_INPUT_TIME_INVALID_LIFETIME;
    binding->event_observer = observe;
    binding->event_observer_context = context;
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_host_refresh_clock(
    PortableInputTimeHost *binding)
{
    if (binding == NULL || binding->clock == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (binding->clock_refresh == NULL)
        return PORTABLE_INPUT_TIME_OK;
    return binding->clock_refresh(binding->clock_refresh_context,
                                  binding->clock) == 1
        ? PORTABLE_INPUT_TIME_OK : PORTABLE_INPUT_TIME_PROVIDER_FAILED;
}

int portable_input_time_host_refresh_from_sdl_monotonic(
    void *context, SimTimingClock *clock)
{
    PortableSdlMonotonicClockRefresh *refresh =
        (PortableSdlMonotonicClockRefresh *)context;
    uint64_t now_ns;
    if (refresh == NULL || clock == NULL || !refresh->initialized)
        return 0;
    SimTimingClock next_game, next_bios;
    now_ns = host_time_ns();
    if (now_ns < refresh->last_ns)
        return 0;
    if (refresh->game_clock != NULL || refresh->bios_clock != NULL) {
        if (refresh->game_clock == NULL || refresh->bios_clock == NULL ||
            refresh->game_clock != clock || refresh->bios_clock == clock ||
            !same_pit_cadence(refresh->game_clock, refresh->bios_clock))
            return 0;
        next_game = *refresh->game_clock;
        next_bios = *refresh->bios_clock;
        next_bios.tick_count_enabled = 1;
        if (sim_timing_advance_nanoseconds(&next_game,
                    now_ns - refresh->last_ns) != SIM_TIMING_OK ||
            sim_timing_advance_nanoseconds(&next_bios,
                    now_ns - refresh->last_ns) != SIM_TIMING_OK)
            return 0;
        *refresh->game_clock = next_game;
        *refresh->bios_clock = next_bios;
    } else if (sim_timing_advance_nanoseconds(clock,
                    now_ns - refresh->last_ns) != SIM_TIMING_OK) {
        return 0;
    }
    refresh->last_ns = now_ns;
    return 1;
}

void portable_sdl_monotonic_clock_refresh_init(
    PortableSdlMonotonicClockRefresh *refresh)
{
    if (refresh == NULL)
        return;
    refresh->last_ns = host_time_ns();
    refresh->game_clock = NULL;
    refresh->bios_clock = NULL;
    refresh->initialized = 1;
}

void portable_sdl_monotonic_clock_refresh_init_clocks(
    PortableSdlMonotonicClockRefresh *refresh,
    SimTimingClock *game_clock, SimTimingClock *bios_clock)
{
    if (refresh == NULL)
        return;
    refresh->last_ns = host_time_ns();
    refresh->game_clock = game_clock;
    refresh->bios_clock = bios_clock;
    refresh->initialized = game_clock != NULL && bios_clock != NULL &&
                           game_clock != bios_clock;
}

int portable_input_time_host_poll_event(PortableInputTimeHost *binding,
                                        HostEvent *event)
{
    if (binding == NULL || event == NULL)
        return -1;
    if (binding->event_count == 0 && ingest_host_events(binding) < 0)
        return -1;
    if (binding->event_count == 0)
        return 0;
    *event = binding->events[binding->event_head];
    binding->event_head = (uint16_t)((binding->event_head + 1u) %
                                     PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY);
    --binding->event_count;
    return 1;
}

int portable_input_time_host_get_input_state(PortableInputTimeHost *binding,
                                             HostInputState *state)
{
    return binding != NULL && binding->host != NULL && state != NULL
        ? host_get_input_state(binding->host, state) : 0;
}

int portable_input_time_host_is_scan_down(PortableInputTimeHost *binding,
                                          uint8_t scan, int *down)
{
    return binding != NULL && binding->host != NULL
        ? host_is_dos_scan_down(binding->host, scan, down) : 0;
}

int portable_input_time_host_dos_modifiers(PortableInputTimeHost *binding,
                                           uint8_t *modifiers)
{
    if (binding == NULL || binding != active_host_binding)
        return 0;
    return portable_input_time_host_current_modifiers(modifiers);
}

uint8_t dos_keyboard_modifiers(void)
{
    PortableInputTimeHost *binding = active_host_binding;
    uint8_t modifiers;
    if (binding == NULL || !portable_input_time_host_current_modifiers(&modifiers))
        abort();
    return modifiers;
}

int portable_input_time_host_current_modifiers(uint8_t *modifiers)
{
    PortableInputTimeHost *binding = active_host_binding;
    HostInputState state;
    if (binding == NULL || binding->host == NULL || modifiers == NULL ||
        !host_get_input_state(binding->host, &state))
        return 0;
    binding->bios_keyboard_flags = (uint8_t)(
        (binding->bios_keyboard_flags & (uint8_t)~UINT8_C(0x0f)) |
        (state.dos_modifiers & UINT8_C(0x0f)));
    *modifiers = binding->bios_keyboard_flags;
    return 1;
}

uint8_t portable_input_time_host_keyboard_flags(
    const PortableInputTimeHost *binding)
{
    return binding == NULL ? 0 : binding->bios_keyboard_flags;
}

void portable_input_time_host_set_keyboard_flags(
    PortableInputTimeHost *binding, uint8_t flags)
{
    if (binding != NULL)
        binding->bios_keyboard_flags = flags;
}

