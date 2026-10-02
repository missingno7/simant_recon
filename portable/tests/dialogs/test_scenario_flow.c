#include "scenario_flow_fixture.h"

#include <assert.h>
#include <stdio.h>

static uint16_t run(const uint16_t *events, size_t event_count,
                    const uint32_t *ticks, size_t tick_count,
                    const uint16_t *keys, size_t key_count,
                    PortableScenarioTraceRow *trace, size_t *trace_count)
{
    uint16_t result = 0;
    assert(portable_scenario_flow_fixture_run(events, event_count, ticks,
        tick_count, keys, key_count, 12, trace, 256, trace_count, &result) == 0);
    return result;
}

int main(void)
{
    static const uint32_t stable_ticks[] = {100, 100, 100, 100, 100, 100,
                                             100, 100, 100, 100, 100, 100};
    static const uint32_t timeout_ticks[] = {100, 100, 5500};
    static const uint16_t accepted[] = {0x0207};
    static const uint16_t ignored_then_selected[] = {0x8202, 0x02ff};
    static const uint16_t ignored[] = {0x0102};
    static const uint16_t escape[] = {0x001b};
    PortableScenarioTraceRow trace[256];
    size_t count;
    uint16_t result;

    result = run(accepted, 1, NULL, 0, escape, 1, trace, &count);
    assert(result == 0x0207 && count == 5);
    assert(trace[0].kind == SCENARIO_TRACE_OPEN && trace[0].value == 0x0200);
    assert(trace[1].kind == SCENARIO_TRACE_FLUSH);
    assert(trace[2].kind == SCENARIO_TRACE_EVENT && trace[2].reserved == 1 &&
           trace[2].value == 0x0207);
    assert(trace[3].kind == SCENARIO_TRACE_CLOSE && trace[3].value == 0x0200);
    assert(trace[4].kind == SCENARIO_TRACE_MESSAGE && trace[4].value == 0x0207);

    result = run(ignored_then_selected, 2, stable_ticks, 6, NULL, 0,
                 trace, &count);
    assert(result == 0x02ff);
    assert(trace[count - 2].kind == SCENARIO_TRACE_CLOSE &&
           trace[count - 1].kind == SCENARIO_TRACE_MESSAGE);

    result = run(ignored, 1, timeout_ticks, 3, NULL, 0, trace, &count);
    assert(result == 0x0205);
    assert(trace[count - 1].kind == SCENARIO_TRACE_CLOSE);
    assert(trace[count - 1].value == 0x0200);

    result = run(NULL, 0, stable_ticks, 6, escape, 1, trace, &count);
    assert(result == 0x0205);
    assert(trace[count - 2].kind == SCENARIO_TRACE_KEY_READ &&
           trace[count - 2].value == 0x001b);
    assert(trace[count - 1].kind == SCENARIO_TRACE_CLOSE);

    /* A real event code 0x0205 takes the accepted-event path before the abort
     * helper, so it closes and emits the scenario message. */
    result = run((const uint16_t[]){0x0205}, 1, timeout_ticks, 3,
                 escape, 1, trace, &count);
    assert(result == 0x0205);
    assert(trace[count - 1].kind == SCENARIO_TRACE_MESSAGE);

    puts("scenario selector source-flow fixtures passed: accepted 0x200..0x2ff, "
         "ignored high-byte partitions, ESC abort, 5400-tick abort, "
         "0x205 accepted-event priority, 0x207 pass-through");
    return 0;
}
