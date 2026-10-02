#ifndef SIMANT_PORTABLE_TEST_SCENARIO_FLOW_FIXTURE_H
#define SIMANT_PORTABLE_TEST_SCENARIO_FLOW_FIXTURE_H

#include <stddef.h>
#include <stdint.h>

typedef struct PortableScenarioTraceRow {
    uint16_t kind;
    uint16_t reserved;
    uint32_t value;
} PortableScenarioTraceRow;

enum {
    SCENARIO_TRACE_OPEN = 1,
    SCENARIO_TRACE_FLUSH,
    SCENARIO_TRACE_EVENT,
    SCENARIO_TRACE_TICK,
    SCENARIO_TRACE_KEY_AVAILABLE,
    SCENARIO_TRACE_KEY_READ,
    SCENARIO_TRACE_CLOSE,
    SCENARIO_TRACE_MESSAGE,
    SCENARIO_TRACE_NO_EVENT = 0xffff
};

int portable_scenario_flow_fixture_run(
    const uint16_t *events, size_t event_count,
    const uint32_t *ticks, size_t tick_count,
    const uint16_t *keys, size_t key_count,
    unsigned poll_limit,
    PortableScenarioTraceRow *trace, size_t trace_capacity,
    size_t *trace_count, uint16_t *result_code);

#endif
