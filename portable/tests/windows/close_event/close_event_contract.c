#include "close_event_contract.h"

#include <string.h>

SimantCloseEventPlan simant_close_event_plan(uint16_t front_window,
                                             uint16_t event_code)
{
    SimantCloseEventPlan plan;
    memset(&plan, 0, sizeof(plan));
    plan.route = SIMANT_CLOSE_EVENT_IGNORE;
    plan.window_id = 0x8000;
    if (front_window == 0x8000) {
        plan.route = SIMANT_CLOSE_EVENT_FORWARD_WITHOUT_FRONT;
        plan.event_remains_pending = 1;
        return plan;
    }
    plan.window_id = front_window;
    if (event_code == 0xf083) {
        plan.route = SIMANT_CLOSE_EVENT_CLOSE_FRONT;
        plan.flush_queue = 1;
        return plan;
    }
    if ((event_code & 0x8000) == 0 && (event_code & 0xff00) == front_window) {
        plan.route = SIMANT_CLOSE_EVENT_DISPATCH_OBJECT;
        plan.event_remains_pending = 1;
        plan.enters_object_click_history = 1;
        plan.object_index = (uint8_t)event_code;
    }
    return plan;
}

int simant_object_click_history(SimantClickHistory *history,
                                SimantClickEvent *current,
                                uint32_t now)
{
    if (history == NULL || current == NULL) return 0;
    if (history->previous.code == current->code && now - 10u < history->tick &&
        ((history->previous.modifiers ^ current->modifiers) & 0x0a00u) == 0) {
        current->modifiers &= (uint16_t)~0x0a00u;
        if (history->previous.modifiers & 0x0800u)
            current->modifiers |= 0x4000u;
        if (history->previous.modifiers & 0x0200u)
            current->modifiers |= 0x2000u;
        history->tick = 0xffffffffu;
        return 1;
    }
    history->tick = now;
    history->previous = *current;
    return 0;
}
