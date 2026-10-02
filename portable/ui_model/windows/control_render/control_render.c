#include "control_render.h"

#include <string.h>

static uint16_t ega_color(uint16_t color)
{
    /* m1B4E.asm f_1B4E_000D: preserve high nibble and translate low nibble
     * through g_41C0. Frozen profile-0 g_41C0 is the identity table 0..15. */
    return (uint16_t)((color & 0xfff0u) | (color & 0x000fu));
}

static int append(SimControlRenderPlan *plan, SimControlRenderCommand value)
{
    if (plan->count >= sizeof plan->commands / sizeof plan->commands[0])
        return 0;
    plan->commands[plan->count++] = value;
    return 1;
}

static SimControlRenderCommand command(SimControlRenderOp op,
                                       uint16_t window_id)
{
    SimControlRenderCommand out;
    memset(&out, 0, sizeof out);
    out.op = op;
    out.window_id = window_id;
    return out;
}

static const SimSetupTriangle *levels_for(const SimControlRenderInput *input,
                                          SimSetupRect *rect,
                                          SimSetupPoint *point,
                                          int16_t *width,
                                          int16_t *height,
                                          uint8_t colors[3])
{
    const SimSetupControls *c = input->controls;
    if (input->window_id == 0x1200u) {
        *rect = input->draw_rect;
        *point = c->mode_point;
        *width = c->mode_width;
        *height = c->mode_height;
        memcpy(colors, input->colors, 3);
        return &c->mode_level;
    }
    *rect = input->draw_rect;
    *point = c->caste_point;
    *width = c->caste_width;
    *height = c->caste_height;
    memcpy(colors, input->colors, 3);
    return &c->caste_level;
}

static int32_t rounded_level(uint16_t level, int16_t percent, int32_t total)
{
    uint32_t n;
    if (percent)
        return (int32_t)((100u * (uint32_t)level + 0x3fffu) / 0xffffu);
    n = (uint32_t)level * (uint32_t)total + 0x3fffu;
    return (int32_t)(n / 0xffffu);
}

SimControlRenderStatus sim_control_render_plan(
    const SimControlRenderInput *input, SimControlRenderPlan *plan)
{
    const SimSetupTriangle *levels;
    SimSetupRect bounds, bar;
    SimSetupPoint point;
    int16_t width, height;
    uint8_t colors[3];
    uint16_t component[3];
    uint16_t i;
    SimControlRenderCommand out;

    if (!input || !plan || !input->controls ||
        (input->window_id != 0x1200u && input->window_id != 0x1300u))
        return SIM_CONTROL_RENDER_INVALID_ARGUMENT;
    memset(plan, 0, sizeof *plan);
    if ((input->flags & 1u) && !input->animation_set_live) {
        out = command(SIM_CONTROL_CLIP_WINDOW, input->window_id);
        if (!append(plan, out)) goto full;
    }
    if (!(input->flags & 2u)) return SIM_CONTROL_RENDER_OK;

    levels = levels_for(input, &bounds, &point, &width, &height, colors);
    component[0] = levels->frac;
    component[1] = levels->mid;
    component[2] = levels->weight;
    (void)width;
    (void)height;
    if (bounds.right < bounds.left || bounds.bottom < bounds.top ||
        input->total < 0)
        return SIM_CONTROL_RENDER_INVALID_ARGUMENT;
    width = (int16_t)((bounds.right - bounds.left) / 5);
    height = (int16_t)(bounds.bottom - bounds.top);

    out = command(SIM_CONTROL_SET_FONT, input->window_id);
    out.font_id = input->screen_width == 320u ? 0 : 4;
    if (!append(plan, out)) goto full;

    for (i = 0; i < 3; ++i) {
        out = command(SIM_CONTROL_TEXT_VALUE, input->window_id);
        out.object_id = (uint16_t)(input->window_id + 9u + i);
        out.value = rounded_level(component[i], input->percent,
                                  input->total);
        out.flags = input->percent ? 1u : 0u;
        if (!append(plan, out)) goto full;

        out = command(SIM_CONTROL_DRAW_TEXT_OBJECT, input->window_id);
        out.object_id = (uint16_t)(input->window_id + 9u + i);
        if (!append(plan, out)) goto full;

        bar.left = (int16_t)(width * (int16_t)(i * 2u) + bounds.left);
        bar.right = (int16_t)(bar.left + width);
        bar.bottom = bounds.bottom;
        bar.top = (int16_t)(((int32_t)component[i] * height) /
                            -65535L + bounds.bottom);
        if ((int32_t)bar.top + 1 < bounds.bottom) {
            out = command(SIM_CONTROL_FILL_RECT, input->window_id);
            out.rect = bar;
            out.fore = ega_color(colors[i]);
            if (!append(plan, out)) goto full;

            out = command(SIM_CONTROL_SET_PATTERN, input->window_id);
            out.fore = ega_color(15);
            out.back = ega_color(15);
            out.pattern = 0;
            if (!append(plan, out)) goto full;

            out = command(SIM_CONTROL_OUTLINE_RECT, input->window_id);
            out.rect = bar;
            out.width = 1;
            if (!append(plan, out)) goto full;
        } else {
            bar.top = bounds.bottom;
        }

        bar.bottom = bar.top;
        bar.top = (int16_t)(bounds.top - 1);
        out = command(SIM_CONTROL_FILL_RECT, input->window_id);
        out.rect = bar;
        out.fore = ega_color(0x40);
        if (!append(plan, out)) goto full;
    }

    out = command(SIM_CONTROL_SET_FONT, input->window_id);
    out.font_id = 0;
    if (!append(plan, out)) goto full;

    if (!input->animation_set_live) {
        out = command(SIM_CONTROL_CREATE_ANIM_SET, input->window_id);
        if (!append(plan, out)) goto full;
        out = command(SIM_CONTROL_ADD_BITMAP, input->window_id);
        out.bitmap_id = 0x0578u;
        out.x = (int16_t)(point.x - input->controls->knob_width / 2);
        out.y = (int16_t)(point.y - input->controls->knob_height / 2);
        out.priority = 0;
    } else {
        out = command(SIM_CONTROL_MOVE_BITMAP, input->window_id);
        out.bitmap_id = 0x8000u;
        out.object_id = input->animation_object_id;
        out.x = (int16_t)(point.x - input->controls->knob_width / 2);
        out.y = (int16_t)(point.y - input->controls->knob_height / 2);
        out.priority = 0x8000u;
    }
    if (!append(plan, out)) goto full;
    out = command(SIM_CONTROL_RENDER_ANIM_SET, input->window_id);
    out.flags = input->animation_set_handle;
    if (!append(plan, out)) goto full;
    return SIM_CONTROL_RENDER_OK;

full:
    memset(plan, 0, sizeof *plan);
    return SIM_CONTROL_RENDER_CAPACITY;
}
