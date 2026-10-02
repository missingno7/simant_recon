#include "../../ui_model/windows/control_events.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Context {
    SimSetupRect source_rect[2];
    SimSetupRect event_rect[2];
    SimSetupPoint samples[2];
    int sample_at;
    int kind;
    int initialized;
} Context;

static int resource_size(void *context, uint16_t id, uint16_t kind,
                        int16_t *width, int16_t *height)
{
    (void)context;
    if (id != 0x0578 || kind != 2 || width == NULL || height == NULL) return 0;
    *width = 32;
    *height = 20;
    return 1;
}

static int get_rect(void *opaque, uint16_t id, SimSetupRect *rect)
{
    Context *context = opaque;
    if (rect == NULL) return 0;
    if (id == 0x120d) *rect = context->initialized ?
        context->event_rect[0] : context->source_rect[0];
    else if (id == 0x130d) *rect = context->initialized ?
        context->event_rect[1] : context->source_rect[1];
    else return 0;
    return 1;
}

static int refresh_control(void *context, SimSetupControlKind kind,
                           const SimSetupControls *controls)
{
    Context *c = context;
    (void)kind; (void)controls;
    if (kind == SIM_SETUP_CASTE_CONTROL) c->initialized = 1;
    return 1;
}

static int clip(void *context, uint16_t window_id)
{ (void)context; return window_id == 0x1200 || window_id == 0x1300; }
static int off(void *context) { (void)context; return 1; }
static int group(void *context, uint16_t window_id, uint8_t group_id, int visible)
{ (void)context; (void)visible; return (window_id == 0x1200 || window_id == 0x1300) && group_id == 4; }
static int select_object(void *context, uint16_t object_id)
{ (void)context; return object_id == 0x1205 || object_id == 0x1305; }
static int draw(void *context, SimSetupControlKind kind, uint16_t flags,
                const SimSetupControls *controls, int16_t percent)
{ (void)context; (void)kind; (void)flags; (void)controls; (void)percent; return 1; }
static int pointer_poll(void *opaque, SimSetupPoint *point)
{
    Context *context = opaque;
    if (context->sample_at >= 2) return 0;
    *point = context->samples[context->sample_at++];
    return 1;
}
static int still_down(void *opaque, int *down)
{ Context *context = opaque; *down = context->sample_at == 1; return 1; }

static int rect_arg(char **argv, int at, SimSetupRect *rect)
{
    return sscanf(argv[at], "%hd,%hd,%hd,%hd", &rect->left, &rect->top,
                  &rect->right, &rect->bottom) == 4;
}

int main(int argc, char **argv)
{
    Context context;
    SimSetupControls controls;
    SimControlEventPrivateState private_state;
    SimSetupHooks hooks;
    SimControlEventProvider provider;
    SimControlEventMessage message;
    SimSetupPoint drag_end[2];
    int i;
    if (argc != 12) return 2;
    memset(&context, 0, sizeof(context));
    memset(&controls, 0, sizeof(controls));
    if (!rect_arg(argv,1,&context.source_rect[0]) ||
        !rect_arg(argv,2,&context.event_rect[0]) ||
        !rect_arg(argv,3,&context.source_rect[1]) ||
        !rect_arg(argv,4,&context.event_rect[1])) return 2;
    controls.mode_current = controls.caste_current = 0;
    sim_setup_controls_init_data(&controls);
    hooks = (SimSetupHooks){resource_size,get_rect,refresh_control,&context};
    if (sim_setup_init_controls(&controls,&hooks) != SIM_SETUP_OK) return 3;
    private_state = (SimControlEventPrivateState){1,1,
        (uint16_t)strtoul(argv[9],NULL,10),
        (uint16_t)strtoul(argv[10],NULL,10),
        (uint16_t)strtoul(argv[11],NULL,10)};
    drag_end[0] = (SimSetupPoint){(int16_t)strtol(argv[5],NULL,10),
                                 (int16_t)strtol(argv[6],NULL,10)};
    drag_end[1] = (SimSetupPoint){(int16_t)strtol(argv[7],NULL,10),
                                 (int16_t)strtol(argv[8],NULL,10)};
    provider = (SimControlEventProvider){clip,off,NULL,group,select_object,
        get_rect,draw,pointer_poll,still_down,&context,2};
    for (i = 0; i < 2; ++i) {
        const uint16_t base = i == 0 ? 0x1200 : 0x1300;
        const SimSetupControlKind kind = i == 0 ? SIM_SETUP_MODE_CONTROL : SIM_SETUP_CASTE_CONTROL;
        const SimSetupRect *r = &context.event_rect[i];
        /* OpenMode/ModeControlChanged and OpenCaste/CasteControlChanged each
         * run InitTriVars for that loaded control rect before its events. */
        private_state.triangle_width = (uint16_t)(r->right - r->left);
        private_state.triangle_height = (uint16_t)(r->bottom - r->top);
        private_state.triangle_width_left = (uint16_t)(private_state.triangle_width >> 1);
        /* The injected stream is motion while held, then release at the same
         * endpoint. The source loop applies the motion on its next pass. */
        context.samples[0] = drag_end[i];
        context.samples[1] = drag_end[i];
        const SimSetupPoint start = {(int16_t)((r->left+r->right)/2),
                                     (int16_t)((r->top+r->bottom)/2)};
        const int codes[5] = {base+4,base+5,base+8,base+16,base+13};
        int j;
        for (j = 0; j < 5; ++j) {
            message.code = (uint16_t)codes[j];
            message.point = start;
            context.sample_at = 0;
            if (sim_control_process_event(&controls,&private_state,kind,
                    &message,&provider) != SIM_CONTROL_EVENT_OK) return 4;
        }
    }
    printf("{\"mode_auto\":%d,\"caste_auto\":%d,"
           "\"mode_selector\":%d,\"caste_selector\":%d,"
           "\"mode_percent\":%d,\"caste_percent\":%d,"
           "\"mode_level\":[%u,%u,%u],\"caste_level\":[%u,%u,%u]}\n",
           controls.mode_auto,controls.caste_auto,controls.mode_current,
           controls.caste_current,private_state.mode_percent,private_state.caste_percent,
           controls.mode_level.frac,controls.mode_level.mid,controls.mode_level.weight,
           controls.caste_level.frac,controls.caste_level.mid,controls.caste_level.weight);
    return 0;
}
