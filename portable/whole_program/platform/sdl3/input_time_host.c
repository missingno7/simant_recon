#include "input_time_host.h"
#include "host_modes.h"

#include <stdlib.h>
#include <stddef.h>
#include <string.h>

static PortableInputTimeHost *active_host_binding;

static int delivery_enabled(const PortableInputTimeHost *binding)
{
    return binding->interrupts_enabled == NULL || binding->interrupts_enabled();
}

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

/* US BIOS set-1 relation: normal, Shift, Ctrl, Alt. Zero means no word,
 * while e.g. 0300 is a valid Ctrl+2 NUL. Provenance and independently measured
 * INT16 controls: portable/tests/acceptance/key_bios_{probe.py,us.json}.
 * DOSBox-X 2026.08.31 bios_keyboard.cpp scan_to_scanascii (IBM/Bochs table).
 * Keep the physical scan in HostEvent: BIOS scan words may be different. */
static const uint16_t us_bios_words[0x59][4] = {
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 00 */
    { 0x011b, 0x011b, 0x011b, 0x01f0 }, /* 01 */
    { 0x0231, 0x0221, 0x0000, 0x7800 }, /* 02 */
    { 0x0332, 0x0340, 0x0300, 0x7900 }, /* 03 */
    { 0x0433, 0x0423, 0x0000, 0x7a00 }, /* 04 */
    { 0x0534, 0x0524, 0x0000, 0x7b00 }, /* 05 */
    { 0x0635, 0x0625, 0x0000, 0x7c00 }, /* 06 */
    { 0x0736, 0x075e, 0x071e, 0x7d00 }, /* 07 */
    { 0x0837, 0x0826, 0x0000, 0x7e00 }, /* 08 */
    { 0x0938, 0x092a, 0x0000, 0x7f00 }, /* 09 */
    { 0x0a39, 0x0a28, 0x0000, 0x8000 }, /* 0a */
    { 0x0b30, 0x0b29, 0x0000, 0x8100 }, /* 0b */
    { 0x0c2d, 0x0c5f, 0x0c1f, 0x8200 }, /* 0c */
    { 0x0d3d, 0x0d2b, 0x0000, 0x8300 }, /* 0d */
    { 0x0e08, 0x0e08, 0x0e7f, 0x0ef0 }, /* 0e */
    { 0x0f09, 0x0f00, 0x9400, 0x0000 }, /* 0f */
    { 0x1071, 0x1051, 0x1011, 0x1000 }, /* 10 */
    { 0x1177, 0x1157, 0x1117, 0x1100 }, /* 11 */
    { 0x1265, 0x1245, 0x1205, 0x1200 }, /* 12 */
    { 0x1372, 0x1352, 0x1312, 0x1300 }, /* 13 */
    { 0x1474, 0x1454, 0x1414, 0x1400 }, /* 14 */
    { 0x1579, 0x1559, 0x1519, 0x1500 }, /* 15 */
    { 0x1675, 0x1655, 0x1615, 0x1600 }, /* 16 */
    { 0x1769, 0x1749, 0x1709, 0x1700 }, /* 17 */
    { 0x186f, 0x184f, 0x180f, 0x1800 }, /* 18 */
    { 0x1970, 0x1950, 0x1910, 0x1900 }, /* 19 */
    { 0x1a5b, 0x1a7b, 0x1a1b, 0x1af0 }, /* 1a */
    { 0x1b5d, 0x1b7d, 0x1b1d, 0x1bf0 }, /* 1b */
    { 0x1c0d, 0x1c0d, 0x1c0a, 0x0000 }, /* 1c */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 1d */
    { 0x1e61, 0x1e41, 0x1e01, 0x1e00 }, /* 1e */
    { 0x1f73, 0x1f53, 0x1f13, 0x1f00 }, /* 1f */
    { 0x2064, 0x2044, 0x2004, 0x2000 }, /* 20 */
    { 0x2166, 0x2146, 0x2106, 0x2100 }, /* 21 */
    { 0x2267, 0x2247, 0x2207, 0x2200 }, /* 22 */
    { 0x2368, 0x2348, 0x2308, 0x2300 }, /* 23 */
    { 0x246a, 0x244a, 0x240a, 0x2400 }, /* 24 */
    { 0x256b, 0x254b, 0x250b, 0x2500 }, /* 25 */
    { 0x266c, 0x264c, 0x260c, 0x2600 }, /* 26 */
    { 0x273b, 0x273a, 0x0000, 0x27f0 }, /* 27 */
    { 0x2827, 0x2822, 0x0000, 0x28f0 }, /* 28 */
    { 0x2960, 0x297e, 0x0000, 0x29f0 }, /* 29 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 2a */
    { 0x2b5c, 0x2b7c, 0x2b1c, 0x2bf0 }, /* 2b */
    { 0x2c7a, 0x2c5a, 0x2c1a, 0x2c00 }, /* 2c */
    { 0x2d78, 0x2d58, 0x2d18, 0x2d00 }, /* 2d */
    { 0x2e63, 0x2e43, 0x2e03, 0x2e00 }, /* 2e */
    { 0x2f76, 0x2f56, 0x2f16, 0x2f00 }, /* 2f */
    { 0x3062, 0x3042, 0x3002, 0x3000 }, /* 30 */
    { 0x316e, 0x314e, 0x310e, 0x3100 }, /* 31 */
    { 0x326d, 0x324d, 0x320d, 0x3200 }, /* 32 */
    { 0x332c, 0x333c, 0x0000, 0x33f0 }, /* 33 */
    { 0x342e, 0x343e, 0x0000, 0x34f0 }, /* 34 */
    { 0x352f, 0x353f, 0x0000, 0x35f0 }, /* 35 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 36 */
    { 0x372a, 0x372a, 0x9600, 0x37f0 }, /* 37 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 38 */
    { 0x3920, 0x3920, 0x3920, 0x3920 }, /* 39 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 3a */
    { 0x3b00, 0x5400, 0x5e00, 0x6800 }, /* 3b */
    { 0x3c00, 0x5500, 0x5f00, 0x6900 }, /* 3c */
    { 0x3d00, 0x5600, 0x6000, 0x6a00 }, /* 3d */
    { 0x3e00, 0x5700, 0x6100, 0x6b00 }, /* 3e */
    { 0x3f00, 0x5800, 0x6200, 0x6c00 }, /* 3f */
    { 0x4000, 0x5900, 0x6300, 0x6d00 }, /* 40 */
    { 0x4100, 0x5a00, 0x6400, 0x6e00 }, /* 41 */
    { 0x4200, 0x5b00, 0x6500, 0x6f00 }, /* 42 */
    { 0x4300, 0x5c00, 0x6600, 0x7000 }, /* 43 */
    { 0x4400, 0x5d00, 0x6700, 0x7100 }, /* 44 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 45 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 46 */
    { 0x4700, 0x4737, 0x7700, 0x0007 }, /* 47 */
    { 0x4800, 0x4838, 0x8d00, 0x0008 }, /* 48 */
    { 0x4900, 0x4939, 0x8400, 0x0009 }, /* 49 */
    { 0x4a2d, 0x4a2d, 0x8e00, 0x4af0 }, /* 4a */
    { 0x4b00, 0x4b34, 0x7300, 0x0004 }, /* 4b */
    { 0x4cf0, 0x4c35, 0x8f00, 0x0005 }, /* 4c */
    { 0x4d00, 0x4d36, 0x7400, 0x0006 }, /* 4d */
    { 0x4e2b, 0x4e2b, 0x9000, 0x4ef0 }, /* 4e */
    { 0x4f00, 0x4f31, 0x7500, 0x0001 }, /* 4f */
    { 0x5000, 0x5032, 0x9100, 0x0002 }, /* 50 */
    { 0x5100, 0x5133, 0x7600, 0x0003 }, /* 51 */
    { 0x5200, 0x5230, 0x9200, 0x0000 }, /* 52 */
    { 0x5300, 0x532e, 0x9300, 0x0000 }, /* 53 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 54 */
    { 0x0000, 0x0000, 0x0000, 0x0000 }, /* 55 */
    { 0x565c, 0x567c, 0x0000, 0x0000 }, /* 56 */
    { 0x8500, 0x8700, 0x8900, 0x8b00 }, /* 57 */
    { 0x8600, 0x8800, 0x8a00, 0x8c00 }, /* 58 */
};

static uint8_t alt_token;

static uint16_t bios_key_word(const HostEvent *event, uint8_t flags)
{
    uint8_t scan = (uint8_t)(event->key >> 8);
    unsigned column = flags & 8 ? 3 : flags & 4 ? 2 : flags & 3 ? 1 : 0;
    uint16_t word;
    if (scan >= 0x59) return 0;
    if (scan >= 0x47 && scan <= 0x53) {
        if (event->extended) {
            if (flags & 8) return (uint16_t)(us_bios_words[scan][0] + 0x5000);
            return us_bios_words[scan][flags & 4 ? 2 : 0];
        }
        if (flags & 8) {
            if (scan != 0x4a && scan != 0x4e) {
                alt_token = (uint8_t)(alt_token * 10 + us_bios_words[scan][3]);
                return 0;
            }
        } else if (!(flags & 4)) {
            column = ((flags & 0x20) != 0) != ((flags & 3) != 0);
        }
    }
    word = us_bios_words[scan][column];
    if (flags & 0x40) {
        if ((flags & 3) && (word & 255) >= 'A' && (word & 255) <= 'Z')
            word = us_bios_words[scan][0];
        else if (!(flags & 3) && (word & 255) >= 'a' && (word & 255) <= 'z')
            word = us_bios_words[scan][1];
    }
    if (event->extended && scan == 0x1c) {
        if (flags & 8) return 0xa600;
    } else if (event->extended && scan == 0x35) {
        if (flags & 8) return 0xa400;
        if (flags & 4) return 0x9500;
        return 0x352f;
    }
    return word;
}

static int push_key(PortableInputTimeHost *binding, uint16_t key)
{
    uint16_t tail;
    /* A full BIOS ring drops this key; IRQ scan state/event effects already
     * occurred. It must not turn input into a host-provider failure. */
    if (binding->key_count >= PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY - 1u)
        return 1;
    tail = (uint16_t)((binding->key_head + binding->key_count) %
                      PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY);
    binding->key_words[tail] = key;
    ++binding->key_count;
    return 1;
}

static int peek_key(PortableInputTimeHost *binding, uint16_t *key)
{
    while (binding->key_count != 0) {
        uint16_t word = binding->key_words[binding->key_head];
        if ((word >> 8) <= 0x84 && !((word >> 8) && (word & 255) == 0xf0))
            break;
        binding->key_head = (uint16_t)((binding->key_head + 1u) %
                                       PORTABLE_INPUT_TIME_HOST_KEY_CAPACITY);
        --binding->key_count;
    }
    if (binding->key_count == 0)
        return 0;
    *key = binding->key_words[binding->key_head];
    return 1;
}

static int pop_key(PortableInputTimeHost *binding, uint16_t *key)
{
    if (!peek_key(binding, key)) return 0;
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
    if (binding->ingesting || !delivery_enabled(binding))
        return 1;
    binding->ingesting = 1;
    do {
        /* Apply backpressure before removing another SDL event. The consumer
         * can drain a full retained FIFO and resume without losing an IRQ or
         * failing on a large ordinary SDL batch. */
        if (binding->event_count == PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY) {
            binding->ingesting = 0;
            return 1;
        }
        polled = host_poll_event(binding->host, &event);
        if (polled < 0) {
            binding->host_closed = 1;
            binding->ingesting = 0;
            return -1;
        }
        if (polled == 0) {
            binding->ingesting = 0;
            return 1;
        }
        event.tick = sim_timing_tick_count(binding->clock);
        if (!push_event(binding, &event)) {
            binding->host_closed = 1;
            binding->ingesting = 0;
            return -1;
        }
        binding->suppress_bios_key = 0;
        if (binding->event_observer != NULL &&
            !binding->event_observer(binding->event_observer_context,
                                     &event)) {
            binding->host_closed = 1;
            binding->ingesting = 0;
            return -1;
        }
        if (event.kind == HOST_EVENT_QUIT)
            binding->host_closed = 1;
        if (event.kind == HOST_EVENT_KEY_DOWN || event.kind == HOST_EVENT_KEY_UP) {
            uint8_t scan = (uint8_t)(event.key >> 8);
            uint8_t lock = scan == 0x3a ? 0x40 : scan == 0x45 ? 0x20 :
                           scan == 0x46 ? 0x10 : scan == 0x52 ? 0x80 : 0;
            /* The hook samples the BDA before the old BIOS IRQ updates it. */
            binding->bios_keyboard_flags = (uint8_t)(
                (binding->bios_keyboard_flags & 0xf0) | (event.modifiers & 0x0f));
            if (lock != 0) {
                if (event.kind == HOST_EVENT_KEY_DOWN &&
                    !(binding->bios_keyboard_flags_hi & lock))
                    binding->bios_keyboard_flags ^= lock;
                if (event.kind == HOST_EVENT_KEY_DOWN)
                    binding->bios_keyboard_flags_hi |= lock;
                else
                    binding->bios_keyboard_flags_hi &= (uint8_t)~lock;
            }
            if ((scan == 0x1d || scan == 0x38) && !event.extended) {
                uint8_t bit = scan == 0x1d ? 1 : 2;
                if (event.kind == HOST_EVENT_KEY_DOWN)
                    binding->bios_keyboard_flags_hi |= bit;
                else
                    binding->bios_keyboard_flags_hi &= (uint8_t)~bit;
            }
            /* The source scan hook has run above. Only the old BIOS handler
             * translates and queues a word; unsupported Ctrl combinations
             * still retain their physical down/up event and scan effects. */
            if (event.kind == HOST_EVENT_KEY_DOWN) {
                uint16_t word = bios_key_word(&event, binding->bios_keyboard_flags);
                if (word != 0) push_key(binding, word);
            } else if (scan == 0x38 && !(event.modifiers & 8)) {
                if (alt_token != 0) push_key(binding, alt_token);
                alt_token = 0;
            }
            if (binding->suppress_bios_key) {
                binding->key_head = 0;
                binding->key_count = 0;
            }
        }
    } while (1);
}

/* Deliver the host queue through the ordinary IRQ adapter without an idle hook.
 * Clock-tape admission uses this boundary; production refresh remains unchanged. */
int portable_input_time_host_interrupt(void)
{
    PortableInputTimeHost *binding = active_host_binding;
    int result, full;
    if (!binding) return -1;
    do {
        result = ingest_host_events(binding);
        full = binding->event_count == PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY;
        /* This entry is tape admission's counterpart of application.c's
         * drain_host_observations: the ordinary observer already dispatched
         * every event. Release only the retained host copies, with no idle,
         * clock, presentation, BIOS-key or canonical event-queue operation. */
        binding->event_head = (uint16_t)((binding->event_head + binding->event_count) %
                                       PORTABLE_INPUT_TIME_HOST_EVENT_CAPACITY);
        binding->event_count = 0;
    } while (result > 0 && full && !binding->ingesting && delivery_enabled(binding));
    return result;
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
    return peek_key(binding, key);
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
    alt_token = 0;
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
    /* The pinned DOSBox-X BIOS starts with BDA NumLock set (40:17 bit 5). */
    binding->bios_keyboard_flags = PORTABLE_INPUT_TIME_HOST_NUMLOCK_MASK;
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
    uint64_t now;
    int refreshed;
    if (binding == NULL || binding->clock == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    /* DOS IRQ input/time can change while a source modal/tracking loop runs.
     * Every platform query yields here. Never enter a callback recursively or
     * deliver host interrupts while the existing source IF flag is clear. */
    if (binding->ingesting || !delivery_enabled(binding))
        return PORTABLE_INPUT_TIME_OK;
    if (portable_test_before_poll) portable_test_before_poll();
    /* The application callback polls retained events after advancing clocks
     * and injecting due replays. Nested services may drain those events within
     * this refresh, but never enter the clock/idle callback a second time. */
    if (binding->refreshing)
        return ingest_host_events(binding) < 0 ? PORTABLE_INPUT_TIME_PROVIDER_FAILED :
                                                PORTABLE_INPUT_TIME_OK;
    /* Captured service inputs replace host time and interrupt scheduling.
     * Their adapter admits IRQ transitions directly; do not advance a second
     * host timeline or run an application idle callback inside a sampled read. */
    if (portable_test_refresh_mode && portable_test_refresh_mode()==1)
        return PORTABLE_INPUT_TIME_OK;
    now = host_time_ns();
    /* Cap real-time refresh work at 1 kHz. Virtual mode instead consumes one
     * configured quantum at each eligible outer refresh, never SDL wall time. */
    if (!host_virtual_clock_enabled() && binding->refresh_initialized &&
        now >= binding->last_refresh_ns &&
        now - binding->last_refresh_ns < UINT64_C(1000000))
        return PORTABLE_INPUT_TIME_OK;
    binding->refreshing = 1;
    binding->last_refresh_ns = now;
    binding->refresh_initialized = 1;
    refreshed = binding->clock_refresh == NULL ||
        binding->clock_refresh(binding->clock_refresh_context, binding->clock) == 1;
    if (refreshed && ingest_host_events(binding) < 0)
        refreshed = 0;
    binding->refreshing = 0;
    return refreshed ? PORTABLE_INPUT_TIME_OK : PORTABLE_INPUT_TIME_PROVIDER_FAILED;
}

void portable_input_time_host_set_interrupt_guard(
    PortableInputTimeHost *binding, int (*enabled)(void))
{
    if (binding != NULL) binding->interrupts_enabled = enabled;
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
    if (portable_input_time_host_refresh_clock(binding) != PORTABLE_INPUT_TIME_OK)
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
    if (binding != NULL &&
        portable_input_time_host_refresh_clock(binding) != PORTABLE_INPUT_TIME_OK)
        return 0;
    return binding != NULL && binding->host != NULL && state != NULL
        ? host_get_input_state(binding->host, state) : 0;
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
    if (binding == NULL || portable_input_time_host_refresh_clock(binding) !=
            PORTABLE_INPUT_TIME_OK || !portable_input_time_host_current_modifiers(&modifiers))
        abort();
    return modifiers;
}

int portable_input_time_host_current_modifiers(uint8_t *modifiers)
{
    PortableInputTimeHost *binding = active_host_binding;
    if (binding == NULL || binding->host == NULL || modifiers == NULL)
        return 0;
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
