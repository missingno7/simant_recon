#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../../../ui_model/windows/control_render/control_render.h"

static void emit(const SimControlRenderPlan *plan)
{
    size_t i;
    for (i = 0; i < plan->count; ++i) {
        const SimControlRenderCommand *c = &plan->commands[i];
        printf("%u\t%u\t%u\t%u\t%u\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%u\t%u\t%u\t%u\n",
               (unsigned)c->op, c->window_id, c->object_id, c->bitmap_id,
               c->flags, (int)c->value, c->rect.left, c->rect.top,
               c->rect.right, c->rect.bottom, c->x, c->y, c->width,
               c->font_id, c->fore, c->back, c->pattern, c->priority);
    }
}

static void init_controls(SimSetupControls *c)
{
    memset(c, 0, sizeof *c);
    c->knob_width = 14;
    c->knob_height = 14;
    c->mode_level = (SimSetupTriangle){ 0x9999u, 0x3333u, 0x3333u };
    c->caste_level = (SimSetupTriangle){ 0x0000u, 0x9999u, 0x6666u };
    c->mode_rect = (SimSetupRect){ 136, 344, 247, 440 };
    c->caste_rect = (SimSetupRect){ 392, 344, 501, 440 };
    c->mode_point = (SimSetupPoint){ 191, 381 };
    c->caste_point = (SimSetupPoint){ 436, 438 };
    c->mode_width = 111;
    c->mode_height = 96;
    c->caste_width = 109;
    c->caste_height = 96;
}

int main(void)
{
    SimSetupControls controls;
    SimControlRenderInput input;
    SimControlRenderPlan plan;
    init_controls(&controls);
    memset(&input, 0, sizeof input);
    input.controls = &controls;
    input.flags = 3;
    input.screen_width = 640;
    input.percent = 1;

    input.window_id = 0x1200;
    input.draw_rect = (SimSetupRect){ 255, 314, 287, 386 };
    input.colors[0] = 40;
    input.colors[1] = 43;
    input.colors[2] = 39;
    assert(sim_control_render_plan(&input, &plan) == SIM_CONTROL_RENDER_OK);
    assert(plan.count == 24);
    assert(plan.commands[0].op == SIM_CONTROL_CLIP_WINDOW);
    assert(plan.commands[1].op == SIM_CONTROL_SET_FONT && plan.commands[1].font_id == 4);
    assert(plan.commands[2].op == SIM_CONTROL_TEXT_VALUE && plan.commands[2].object_id == 0x1209 && plan.commands[2].value == 60);
    assert(plan.commands[4].op == SIM_CONTROL_FILL_RECT && plan.commands[4].rect.left == 255 && plan.commands[4].rect.right == 261);
    assert(plan.commands[4].rect.top == 343 && plan.commands[4].rect.bottom == 386);
    assert(plan.commands[4].fore == 40);
    assert(plan.commands[20].op == SIM_CONTROL_SET_FONT && plan.commands[20].font_id == 0);
    assert(plan.commands[22].op == SIM_CONTROL_ADD_BITMAP && plan.commands[22].bitmap_id == 0x578);
    assert(plan.commands[22].x == 184 && plan.commands[22].y == 374);
    emit(&plan);

    input.window_id = 0x1300;
    input.draw_rect = (SimSetupRect){ 512, 315, 542, 388 };
    input.colors[0] = 36;
    input.colors[1] = 38;
    input.colors[2] = 34;
    assert(sim_control_render_plan(&input, &plan) == SIM_CONTROL_RENDER_OK);
    assert(plan.count == 21);
    assert(plan.commands[2].value == 0);
    assert(plan.commands[5].value == 60);
    assert(plan.commands[11].value == 40);
    assert(plan.commands[19].x == 429 && plan.commands[19].y == 431);
    emit(&plan);

    input.window_id = 0x1200;
    input.animation_set_live = 1;
    input.animation_set_handle = 0x1234;
    input.animation_object_id = 7;
    assert(sim_control_render_plan(&input, &plan) == SIM_CONTROL_RENDER_OK);
    assert(plan.count == 22);
    assert(plan.commands[0].op == SIM_CONTROL_SET_FONT);
    assert(plan.commands[20].op == SIM_CONTROL_MOVE_BITMAP);
    assert(plan.commands[20].bitmap_id == 0x8000 && plan.commands[20].object_id == 7);
    emit(&plan);

    input.flags = 1;
    assert(sim_control_render_plan(&input, &plan) == SIM_CONTROL_RENDER_OK);
    assert(plan.count == 0); /* Live anim set suppresses clip and draw flags. */
    input.animation_set_live = 0;
    assert(sim_control_render_plan(&input, &plan) == SIM_CONTROL_RENDER_OK);
    assert(plan.count == 1 && plan.commands[0].op == SIM_CONTROL_CLIP_WINDOW);

    puts("control-render source model PASS");
    return 0;
}
