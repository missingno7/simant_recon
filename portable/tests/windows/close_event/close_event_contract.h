#ifndef SIMANT_CLOSE_EVENT_CONTRACT_H
#define SIMANT_CLOSE_EVENT_CONTRACT_H

#include <stdint.h>

typedef enum SimantCloseEventRoute {
    SIMANT_CLOSE_EVENT_IGNORE = 0,
    SIMANT_CLOSE_EVENT_CLOSE_FRONT,
    SIMANT_CLOSE_EVENT_DISPATCH_OBJECT,
    SIMANT_CLOSE_EVENT_FORWARD_WITHOUT_FRONT
} SimantCloseEventRoute;

typedef struct SimantCloseEventPlan {
    SimantCloseEventRoute route;
    uint16_t window_id;
    uint8_t flush_queue;
    uint8_t event_remains_pending;
    uint8_t enters_object_click_history;
    uint8_t object_index;
} SimantCloseEventPlan;

/* Test/research contract for source f_218D_02D5 after its Event was dequeued. */
SimantCloseEventPlan simant_close_event_plan(uint16_t front_window,
                                             uint16_t event_code);

typedef struct SimantClickEvent {
    uint16_t what, message, tick_low, modifiers;
    uint16_t h, v, code, xE;
} SimantClickEvent;

typedef struct SimantClickHistory {
    uint32_t tick;
    SimantClickEvent previous;
} SimantClickHistory;

/* Test/research contract for the bookkeeping tail of f_218D_000C. */
int simant_object_click_history(SimantClickHistory *history,
                                SimantClickEvent *current,
                                uint32_t now);

#endif
