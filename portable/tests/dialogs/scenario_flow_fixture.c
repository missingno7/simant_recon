#include "scenario_flow_fixture.h"
#include "../../ui_model/dialogs/scenario_flow.h"

#include <string.h>

typedef struct Fixture {
    const uint16_t *events;
    size_t event_count, event_index;
    const uint32_t *ticks;
    size_t tick_count, tick_index;
    const uint16_t *keys;
    size_t key_count, key_index;
    PortableScenarioTraceRow *trace;
    size_t trace_capacity, trace_count;
    int overflow;
} Fixture;

static void record(Fixture *fixture, uint16_t kind, uint32_t value)
{
    if (fixture->trace_count >= fixture->trace_capacity) {
        fixture->overflow = 1;
        return;
    }
    fixture->trace[fixture->trace_count++] =
        (PortableScenarioTraceRow){kind, 0, value};
}

static void record_event(Fixture *fixture, int present, uint16_t code)
{
    if (fixture->trace_count >= fixture->trace_capacity) {
        fixture->overflow = 1;
        return;
    }
    fixture->trace[fixture->trace_count++] = (PortableScenarioTraceRow){
        SCENARIO_TRACE_EVENT, (uint16_t)(present != 0), present ? code : 0};
}

static void open_window(void *context, uint16_t window)
{ record((Fixture *)context, SCENARIO_TRACE_OPEN, window); }

static void flush_events(void *context)
{ record((Fixture *)context, SCENARIO_TRACE_FLUSH, 0); }

static int get_event(void *context, PortableScenarioEvent *event)
{
    Fixture *fixture = (Fixture *)context;
    if (fixture->event_index >= fixture->event_count) {
        record_event(fixture, 0, 0);
        return 0;
    }
    event->code = fixture->events[fixture->event_index++];
    record_event(fixture, 1, event->code);
    return 1;
}

static uint32_t fixture_tick_count(void *context)
{
    Fixture *fixture = (Fixture *)context;
    uint32_t value;
    if (fixture->tick_count == 0)
        value = 0;
    else {
        size_t index = fixture->tick_index < fixture->tick_count
            ? fixture->tick_index : fixture->tick_count - 1;
        value = fixture->ticks[index];
        ++fixture->tick_index;
    }
    record(fixture, SCENARIO_TRACE_TICK, value);
    return value;
}

static int keyboard_has_key(void *context)
{
    Fixture *fixture = (Fixture *)context;
    int available = fixture->key_index < fixture->key_count;
    record(fixture, SCENARIO_TRACE_KEY_AVAILABLE, (uint32_t)available);
    return available;
}

static uint16_t keyboard_read_key(void *context)
{
    Fixture *fixture = (Fixture *)context;
    uint16_t value = fixture->key_index < fixture->key_count
        ? fixture->keys[fixture->key_index++] : 0;
    record(fixture, SCENARIO_TRACE_KEY_READ, value);
    return value;
}

static void close_window(void *context, uint16_t window)
{ record((Fixture *)context, SCENARIO_TRACE_CLOSE, window); }

static void scenario_message(void *context, uint16_t code)
{ record((Fixture *)context, SCENARIO_TRACE_MESSAGE, code); }

int portable_scenario_flow_fixture_run(
    const uint16_t *events, size_t event_count,
    const uint32_t *ticks, size_t tick_count,
    const uint16_t *keys, size_t key_count,
    unsigned poll_limit,
    PortableScenarioTraceRow *trace, size_t trace_capacity,
    size_t *trace_count, uint16_t *result_code)
{
    Fixture fixture;
    PortableScenarioHost host;
    PortableScenarioFlow flow;
    unsigned poll;
    if ((events == NULL && event_count != 0) ||
        (ticks == NULL && tick_count != 0) ||
        (keys == NULL && key_count != 0) || trace == NULL ||
        trace_count == NULL || result_code == NULL)
        return -1;
    memset(&fixture, 0, sizeof(fixture));
    fixture.events = events; fixture.event_count = event_count;
    fixture.ticks = ticks; fixture.tick_count = tick_count;
    fixture.keys = keys; fixture.key_count = key_count;
    fixture.trace = trace; fixture.trace_capacity = trace_capacity;
    host = (PortableScenarioHost){&fixture, open_window, flush_events,
        get_event, fixture_tick_count, keyboard_has_key, keyboard_read_key,
        close_window, scenario_message};
    if (!portable_scenario_flow_begin(&flow, &host))
        return -2;
    for (poll = 0; poll < poll_limit; ++poll) {
        PortableScenarioPollResult status = portable_scenario_flow_poll(&flow);
        if (status != PORTABLE_SCENARIO_RUNNING) {
            *trace_count = fixture.trace_count;
            *result_code = flow.result_code;
            return fixture.overflow ? -3 : 0;
        }
    }
    *trace_count = fixture.trace_count;
    *result_code = flow.result_code;
    return fixture.overflow ? -3 : -4;
}
