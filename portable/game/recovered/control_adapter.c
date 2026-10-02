#include "control_adapter.h"
#include "recovered_state.h"

#include <string.h>

_Static_assert(sizeof(SimSetupTriangle) == 6, "source control triple is three words");

#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
typedef struct ControlProviderFrame {
    const SimControlEventProvider *provider;
    SimSetupControls *controls;
    SimSetupControlKind kind;
} ControlProviderFrame;

static void write_control_fields(ControlProviderFrame *frame)
{
    const SimSetupControls *controls = frame->controls;
    if (frame->kind == SIM_SETUP_MODE_CONTROL) {
        ModeAuto = controls->mode_auto;
        memcpy(modeLevels, &controls->mode_level, sizeof modeLevels);
        memcpy(fd_3D57_0810, controls->mode_levels, sizeof fd_3D57_0810);
        fd_50F6_0358.x = controls->mode_point.x;
        fd_50F6_0358.y = controls->mode_point.y;
    } else {
        CasteAuto = controls->caste_auto;
        memcpy(casteLevels, &controls->caste_level, sizeof casteLevels);
        memcpy(fd_3D57_07F2, controls->caste_levels, sizeof fd_3D57_07F2);
        memcpy(IdealCaste, controls->ideal_caste, sizeof controls->ideal_caste);
        fd_50F6_022E.x = controls->caste_point.x;
        fd_50F6_022E.y = controls->caste_point.y;
    }
}

/* A synchronous host callback may inspect active source state. Publish the
 * model's writes at every original service boundary, not just on return. */
#define FRAME() ControlProviderFrame *f = context; write_control_fields(f)
static int clip_set(void *context, uint16_t id)
{ FRAME(); return f->provider->clip_set_window(f->provider->context, id); }
static int clip_off(void *context)
{ FRAME(); return f->provider->clip_off(f->provider->context); }
static int help(void *context, uint16_t id)
{ FRAME(); return f->provider->help(f->provider->context, id); }
static int group(void *context, uint16_t id, uint8_t g, int visible)
{ FRAME(); return f->provider->set_group_visible(f->provider->context, id, g, visible); }
static int select_object(void *context, uint16_t id)
{ FRAME(); return f->provider->select_object(f->provider->context, id); }
static int get_rect(void *context, uint16_t id, SimSetupRect *rect)
{ FRAME(); return f->provider->get_object_rect(f->provider->context, id, rect); }
static int draw(void *context, SimSetupControlKind kind, uint16_t flags,
                const SimSetupControls *controls, int16_t percent)
{ FRAME(); return f->provider->draw_control(f->provider->context, kind, flags, controls, percent); }
static int poll_pointer(void *context, SimSetupPoint *point)
{ FRAME(); return f->provider->pointer_poll(f->provider->context, point); }
static int still_down(void *context, int *down)
{ FRAME(); return f->provider->still_down(f->provider->context, down); }
#undef FRAME
#endif

SimControlEventStatus sim_recovered_source_control_event(
    SimSetupControls *controls, SimControlEventPrivateState *private_state,
    SimSetupControlKind kind, const SimControlEventMessage *message,
    const SimControlEventProvider *provider)
{
#ifdef SIMANT_ENABLE_CONTROL_INIT_NEXT4
    SimControlEventStatus status;
    ControlProviderFrame frame;
    SimControlEventProvider wrapped;
    if (controls == NULL || private_state == NULL || message == NULL ||
        provider == NULL || (kind != SIM_SETUP_MODE_CONTROL &&
                             kind != SIM_SETUP_CASTE_CONTROL))
        return SIM_CONTROL_EVENT_BAD_ARGUMENT;
    private_state->triangle_width = triWidth;
    private_state->triangle_height = triHeight;
    private_state->triangle_width_left = triWidthL;
    frame = (ControlProviderFrame){provider, controls, kind};
    wrapped = (SimControlEventProvider){
        provider->clip_set_window ? clip_set : NULL,
        provider->clip_off ? clip_off : NULL,
        provider->help ? help : NULL,
        provider->set_group_visible ? group : NULL,
        provider->select_object ? select_object : NULL,
        provider->get_object_rect ? get_rect : NULL,
        provider->draw_control ? draw : NULL,
        provider->pointer_poll ? poll_pointer : NULL,
        provider->still_down ? still_down : NULL,
        &frame, provider->max_drag_samples};
    status = sim_control_process_event(controls, private_state, kind, message,
                                       &wrapped);
    /* Preserve source partial writes on an ordinary provider failure. The
     * engine may subsequently fault at that named boundary. Neither branch
     * initializes defaults, shared geometry, flags, resources, or RNG. */
    write_control_fields(&frame);
    return status;
#else
    (void)controls; (void)private_state; (void)kind; (void)message; (void)provider;
    return SIM_CONTROL_EVENT_INVALID_SOURCE_STATE;
#endif
}
