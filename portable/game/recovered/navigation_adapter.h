#ifndef SIMANT_GAME_RECOVERED_NAVIGATION_ADAPTER_H
#define SIMANT_GAME_RECOVERED_NAVIGATION_ADAPTER_H

#include <stdint.h>

typedef enum SimRecoveredNavigationEventKind {
    SIM_NAV_INVALIDATE_MAP = 1,
    SIM_NAV_SET_EDIT_MODE,
    SIM_NAV_CENTER_VIEW,
    SIM_NAV_UPDATE_EDIT,
    SIM_NAV_SET_MAP_TITLE,
    SIM_NAV_CLIP_SET_WINDOW,
    SIM_NAV_SELECT_OBJECT,
    SIM_NAV_SELECT_WINDOW,
    SIM_NAV_UNSELECT_GROUP,
    SIM_NAV_CLIP_OFF,
    SIM_NAV_REFRESH_YARD
} SimRecoveredNavigationEventKind;

typedef struct SimRecoveredNavigationEvent {
    SimRecoveredNavigationEventKind kind;
    int16_t a;
    int16_t b;
    int16_t c;
    int16_t d;
} SimRecoveredNavigationEvent;

typedef int (*SimRecoveredNavigationEffect)(
    void *context, const SimRecoveredNavigationEvent *event);

#define SIM_RECOVERED_NAVIGATION_EVENT_CAPACITY 64

typedef struct SimRecoveredNavigationBinding {
    SimRecoveredNavigationEvent events[SIM_RECOVERED_NAVIGATION_EVENT_CAPACITY];
    uint16_t event_count;
    int failed;
    SimRecoveredNavigationEffect event_sink;
    void *event_context;
} SimRecoveredNavigationBinding;

/* Zero-initialize the binding before first use, then optionally set
 * event_sink/event_context. Bind around a recovered navigation call while
 * RecoveredState is active.
 * Events are captured for diagnostics and synchronously delivered to event_sink
 * when configured. A nonzero sink result accepts the event; rejection marks
 * the binding failed so its caller can fail the current tick. */
void sim_recovered_navigation_bind(SimRecoveredNavigationBinding *binding);
void sim_recovered_navigation_unbind(SimRecoveredNavigationBinding *binding);

/* Source-compatible root:015B entries used by recovered callers. */
void CenterAnt(void);
void GotoMyAnt(void);
void SetMapPlane(int16_t plane);
void SetMapPlaneLocation(int16_t plane, int16_t x, int16_t y);
void GotoMapPoint(int16_t plane, int16_t x, int16_t y);

#endif
