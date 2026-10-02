#include "../../game/recovered/navigation_adapter.h"
#include "recovered_state.h"

#include <assert.h>
#include <stdlib.h>

static int sound_calls;
static int16_t sound_args[3];

typedef struct SinkCapture {
    int calls;
    int accept;
    SimRecoveredNavigationEventKind last_kind;
    int16_t last_x;
    int16_t last_y;
    int16_t view_x_at_call;
    int16_t view_y_at_call;
} SinkCapture;

static int navigation_sink(void *context,
                           const SimRecoveredNavigationEvent *event)
{
    SinkCapture *capture = (SinkCapture *)context;
    ++capture->calls;
    capture->last_kind = event->kind;
    capture->last_x = event->b;
    capture->last_y = event->c;
    capture->view_x_at_call = fd_50F6_0508[0];
    capture->view_y_at_call = fd_50F6_0508[1];
    return capture->accept;
}

void myBeginSound(int16_t sound, int16_t a, int16_t b)
{
    ++sound_calls;
    sound_args[0] = sound;
    sound_args[1] = a;
    sound_args[2] = b;
}

static void begin(RecoveredState *state, RecoveredBindingFrame *frame)
{
    recovered_state_init(state);
    (void)frame;
}

int main(void)
{
    RecoveredState *state = (RecoveredState *)malloc(sizeof(*state));
    RecoveredBindingFrame frame;
    SimRecoveredNavigationBinding binding = { 0 };
    SinkCapture capture = { 0 };
    assert(state != NULL);

    begin(state, &frame);
    state->MapPlane = 1;
    state->MePlane = 1;
    state->MeLocX = 45;
    state->MeLocY = 30;
    state->fd_50F6_0EAC = 2;
    state->fd_50F6_1074 = 0;
    state->fd_50F6_0AA6 = 7;
    state->fd_50F6_0508[0] = 0;
    state->fd_50F6_0508[1] = 0;
    state->fd_50F6_10E0 = 20;
    state->fd_50F6_10DE = 12;
    capture.accept = 1;
    binding.event_sink = navigation_sink;
    binding.event_context = &capture;
    recovered_bind_begin(&frame, state);
    sim_recovered_navigation_bind(&binding);
    GotoMyAnt();
    sim_recovered_navigation_unbind(&binding);
    recovered_bind_end(&frame, state);
    assert(state->fd_50F6_1074 == 1);
    assert(state->fd_50F6_0AA6 == 0);
    assert(state->fd_50F6_0508[0] == 35);
    /* f_0250_0D10's integer 16.16 fraction leaves the minor axis one tile
     * short in this non-integral slope case (the source rounding is retained). */
    assert(state->fd_50F6_0508[1] == 23);
    assert(binding.event_count == 1);
    assert(binding.events[0].kind == SIM_NAV_CENTER_VIEW);
    assert(capture.calls == 1);
    assert(capture.last_kind == SIM_NAV_CENTER_VIEW);
    assert(capture.last_x == 45 && capture.last_y == 30);
    assert(capture.view_x_at_call == 35 && capture.view_y_at_call == 23);
    assert(binding.failed == 0);

    begin(state, &frame);
    state->MapPlane = 2;
    state->MePlane = 2;
    state->MeLocX = 50;
    state->MeLocY = 30;
    state->fd_50F6_0EAC = 3;
    state->fd_50F6_1074 = 0;
    sound_calls = 0;
    recovered_bind_begin(&frame, state);
    sim_recovered_navigation_bind(&binding);
    GotoMyAnt();
    sim_recovered_navigation_unbind(&binding);
    recovered_bind_end(&frame, state);
    assert(state->fd_50F6_1074 == 1);
    assert(sound_calls == 1);
    assert(sound_args[0] == 1 && sound_args[1] == 0 && sound_args[2] == 0x7e);
    assert(binding.event_count == 0);

    begin(state, &frame);
    state->MapPlane = 1;
    state->MePlane = 1;
    state->MeLocX = 45;
    state->MeLocY = 30;
    state->fd_50F6_0EAC = 2;
    state->fd_50F6_0508[0] = 0;
    state->fd_50F6_0508[1] = 0;
    state->fd_50F6_10E0 = 20;
    state->fd_50F6_10DE = 12;
    capture = (SinkCapture){ 0 };
    capture.accept = 0;
    binding.event_sink = navigation_sink;
    binding.event_context = &capture;
    recovered_bind_begin(&frame, state);
    sim_recovered_navigation_bind(&binding);
    GotoMyAnt();
    assert(binding.failed == 1);
    assert(binding.event_count == 1);
    assert(capture.calls == 1);
    sim_recovered_navigation_unbind(&binding);
    recovered_bind_end(&frame, state);

    free(state);
    return 0;
}
