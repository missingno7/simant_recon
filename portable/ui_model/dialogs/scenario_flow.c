#include "scenario_flow.h"

#include <string.h>

static int waited_enough(PortableScenarioFlow *flow, uint32_t *start)
{
    uint32_t now = flow->host.tick_count(flow->host.context);
    uint32_t deadline;
    uint32_t after;
    int expired = (int32_t)now < (int32_t)*start;
    if (!expired) {
        after = flow->host.tick_count(flow->host.context);
        deadline = *start + (uint32_t)PORTABLE_SCENARIO_WAIT_TICKS;
        expired = (int32_t)deadline <= (int32_t)after;
    }
    if (expired) {
        /* WaitedEnough refreshes the caller's timestamp for either expiry
         * condition, including a signed-backwards TickCount sample. */
        *start = flow->host.tick_count(flow->host.context);
        return 1;
    }
    return 0;
}

static int dialog_abort(PortableScenarioFlow *flow, uint32_t *start)
{
    if (waited_enough(flow, start))
        return 1;
    if (flow->host.keyboard_has_key(flow->host.context) &&
        flow->host.keyboard_read_key(flow->host.context) == 0x1b)
        return 1;
    return 0;
}

static int valid_host(const PortableScenarioHost *host)
{
    return host != NULL && host->open_window != NULL &&
           host->flush_events != NULL && host->get_event != NULL &&
           host->tick_count != NULL && host->keyboard_has_key != NULL &&
           host->keyboard_read_key != NULL && host->close_window != NULL &&
           host->scenario_message != NULL;
}

int portable_scenario_flow_begin(PortableScenarioFlow *flow,
                                 const PortableScenarioHost *host)
{
    if (flow == NULL || !valid_host(host))
        return 0;
    memset(flow, 0, sizeof(*flow));
    flow->host = *host;
    flow->active = 1;
    flow->host.open_window(flow->host.context, PORTABLE_SCENARIO_WINDOW);
    flow->host.flush_events(flow->host.context);
    return 1;
}

PortableScenarioPollResult portable_scenario_flow_poll(
    PortableScenarioFlow *flow)
{
    PortableScenarioEvent event;
    uint32_t start;
    if (flow == NULL || !flow->active)
        return PORTABLE_SCENARIO_ABORTED;
    if (flow->host.get_event(flow->host.context, &event) &&
        (event.code >> 8) == 2) {
        flow->host.close_window(flow->host.context, PORTABLE_SCENARIO_WINDOW);
        flow->host.scenario_message(flow->host.context, event.code);
        flow->result_code = event.code;
        flow->active = 0;
        return PORTABLE_SCENARIO_SELECTED;
    }

    /* f_00F8_032A is DialogClearWait, called after each non-scenario event.
     * It resets the 5400-tick baseline every poll, exactly as the DOS source. */
    start = flow->host.tick_count(flow->host.context);
    if (dialog_abort(flow, &start)) {
        flow->host.close_window(flow->host.context, PORTABLE_SCENARIO_WINDOW);
        flow->result_code = PORTABLE_SCENARIO_CANCEL_CODE;
        flow->active = 0;
        return PORTABLE_SCENARIO_ABORTED;
    }
    return PORTABLE_SCENARIO_RUNNING;
}
