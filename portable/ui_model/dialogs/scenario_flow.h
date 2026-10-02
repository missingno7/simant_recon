#ifndef SIMANT_PORTABLE_UI_MODEL_DIALOGS_SCENARIO_FLOW_H
#define SIMANT_PORTABLE_UI_MODEL_DIALOGS_SCENARIO_FLOW_H

#include <stdint.h>

enum {
    PORTABLE_SCENARIO_WINDOW = 0x0200,
    PORTABLE_SCENARIO_CANCEL_CODE = 0x0205,
    PORTABLE_SCENARIO_WAIT_TICKS = 5400
};

typedef struct PortableScenarioEvent {
    uint16_t code;
} PortableScenarioEvent;

typedef struct PortableScenarioHost {
    void *context;
    void (*open_window)(void *context, uint16_t window_id);
    void (*flush_events)(void *context);
    int (*get_event)(void *context, PortableScenarioEvent *event);
    uint32_t (*tick_count)(void *context);
    int (*keyboard_has_key)(void *context);
    uint16_t (*keyboard_read_key)(void *context);
    void (*close_window)(void *context, uint16_t window_id);
    void (*scenario_message)(void *context, uint16_t code);
} PortableScenarioHost;

typedef enum PortableScenarioPollResult {
    PORTABLE_SCENARIO_RUNNING = 0,
    PORTABLE_SCENARIO_SELECTED,
    PORTABLE_SCENARIO_ABORTED
} PortableScenarioPollResult;

typedef struct PortableScenarioFlow {
    PortableScenarioHost host;
    uint16_t result_code;
    uint8_t active;
} PortableScenarioFlow;

/* This is the source DoScenario modal boundary. The caller supplies real host
 * window, input, BIOS-clock and physical-key callbacks; no selection is
 * fabricated when the host has no event. */
int portable_scenario_flow_begin(PortableScenarioFlow *flow,
                                 const PortableScenarioHost *host);
PortableScenarioPollResult portable_scenario_flow_poll(
    PortableScenarioFlow *flow);

#endif
