#ifndef SIMANT_UI_CONTROL_RENDER_H
#define SIMANT_UI_CONTROL_RENDER_H

#include <stddef.h>
#include <stdint.h>
#include "../../../game/simulation/setup.h"

typedef enum SimControlRenderStatus {
    SIM_CONTROL_RENDER_OK = 0,
    SIM_CONTROL_RENDER_INVALID_ARGUMENT = 1,
    SIM_CONTROL_RENDER_CAPACITY = 2
} SimControlRenderStatus;

typedef enum SimControlRenderOp {
    SIM_CONTROL_CLIP_WINDOW,
    SIM_CONTROL_SET_FONT,
    SIM_CONTROL_TEXT_VALUE,
    SIM_CONTROL_DRAW_TEXT_OBJECT,
    SIM_CONTROL_FILL_RECT,
    SIM_CONTROL_SET_PATTERN,
    SIM_CONTROL_OUTLINE_RECT,
    SIM_CONTROL_CREATE_ANIM_SET,
    SIM_CONTROL_ADD_BITMAP,
    SIM_CONTROL_MOVE_BITMAP,
    SIM_CONTROL_RENDER_ANIM_SET
} SimControlRenderOp;

typedef struct SimControlRenderCommand {
    SimControlRenderOp op;
    uint16_t window_id;
    uint16_t object_id;
    uint16_t bitmap_id;
    uint16_t flags;
    int32_t value;
    SimSetupRect rect;
    int16_t x;
    int16_t y;
    int16_t width;
    int16_t font_id;
    uint16_t fore;
    uint16_t back;
    uint16_t pattern;
    uint16_t priority;
} SimControlRenderCommand;

typedef struct SimControlRenderInput {
    const SimSetupControls *controls;
    uint16_t window_id; /* Source IDs: 0x1200 mode, 0x1300 caste. */
    uint16_t flags; /* Source win_Draw{Mode,Caste}Window flags. */
    uint16_t screen_width; /* Source g_3DB2. */
    int16_t percent; /* Source g_1B62/g_1B64. */
    int32_t total; /* Mode: sum of 0B12[0..2]; caste: 0AEC. */
    SimSetupRect draw_rect; /* win_GetObjRect(window + 12) bar/text band. */
    uint8_t colors[3]; /* Source g_1B4A/g_1B46, in component order. */
    uint8_t animation_set_live;
    uint16_t animation_set_handle;
    uint16_t animation_object_id;
} SimControlRenderInput;

typedef struct SimControlRenderPlan {
    SimControlRenderCommand commands[32];
    size_t count;
} SimControlRenderPlan;

/* Source-mapped command plan for the initial DrawModeWindow/DrawCasteWindow
 * paths. Bitmap 0x578 is a resource key to resolve in the active session
 * provider; this plan owns no animation/resource handles and does not raster
 * the source graphics backend. */
SimControlRenderStatus sim_control_render_plan(
    const SimControlRenderInput *input, SimControlRenderPlan *plan);

#endif
