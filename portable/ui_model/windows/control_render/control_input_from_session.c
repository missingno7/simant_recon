#include "control_input_from_session.h"

#include <string.h>

SimControlSessionInputStatus sim_control_render_binding_from_session(
    SimSession *session,
    const PortableWindowRenderer *active_renderer,
    SimSetupControlKind kind,
    uint16_t draw_flags,
    const SimControlRecoveredVisualState *recovered,
    const SimControlActiveAnimation *animation,
    SimControlAnimationBitmapResolver resolve_animation_bitmap,
    SimControlRenderBinding *binding)
{
    static const uint8_t mode_colors[3] = {40, 43, 39};
    static const uint8_t caste_colors[3] = {36, 38, 34};
    PortableWindowRegistrySlot *slot;
    SimSessionControlVisual *visual;
    int16_t window_id;
    uint16_t source_window;
    unsigned control_index;

    if (session == NULL || active_renderer == NULL || recovered == NULL ||
        binding == NULL || (kind != SIM_SETUP_MODE_CONTROL &&
                            kind != SIM_SETUP_CASTE_CONTROL) ||
        session->window_registry == NULL || session->window_database == NULL ||
        active_renderer->database != session->window_database ||
        session->window_registry->database != session->window_database ||
        active_renderer->framebuffer == NULL || active_renderer->colors == NULL)
        return SIM_CONTROL_SESSION_INPUT_BAD_ARGUMENT;
    control_index = (unsigned)kind;
    visual = &session->controls[control_index];
    if (!visual->active || !session->setup_controls.source_data_initialized)
        return SIM_CONTROL_SESSION_INPUT_INACTIVE_CONTROL;
    {
        const SimSetupRect *rect = kind == SIM_SETUP_MODE_CONTROL
                                       ? &session->setup_controls.mode_rect
                                       : &session->setup_controls.caste_rect;
        const SimSetupPoint *point = kind == SIM_SETUP_MODE_CONTROL
                                         ? &session->setup_controls.mode_point
                                         : &session->setup_controls.caste_point;
        if (visual->rectangle.left != rect->left ||
            visual->rectangle.top != rect->top ||
            visual->rectangle.right != rect->right ||
            visual->rectangle.bottom != rect->bottom ||
            visual->point.x != point->x || visual->point.y != point->y)
            return SIM_CONTROL_SESSION_INPUT_INACTIVE_CONTROL;
    }
    if ((visual->animation_resource == NULL) != (animation == NULL) ||
        (animation != NULL &&
         (animation->resource == NULL ||
          animation->resource != visual->animation_resource ||
          resolve_animation_bitmap == NULL)))
        return SIM_CONTROL_SESSION_INPUT_ANIMATION_MISMATCH;

    source_window = kind == SIM_SETUP_MODE_CONTROL ? 0x1200u : 0x1300u;
    window_id = (int16_t)(source_window >> 8);
    if (portable_window_registry_load(session->window_registry, window_id) !=
        PORTABLE_WINDOW_REGISTRY_OK)
        return SIM_CONTROL_SESSION_INPUT_WINDOW_NOT_CURRENT;
    slot = &session->window_registry->slots[window_id];
    if (!slot->recalculated || slot->window.resource_id != window_id ||
        slot->window.count <= 12)
        return SIM_CONTROL_SESSION_INPUT_WINDOW_NOT_CURRENT;

    memset(binding, 0, sizeof(*binding));
    binding->input.controls = &session->setup_controls;
    binding->input.window_id = source_window;
    binding->input.flags = draw_flags;
    binding->input.screen_width = active_renderer->screen_width;
    binding->input.percent = kind == SIM_SETUP_MODE_CONTROL
                                ? recovered->mode_percent
                                : recovered->caste_percent;
    if (kind == SIM_SETUP_MODE_CONTROL) {
        /* DrawControlLevels sums fd_50F6_0B12[2] + [1] + [0] as a DOS long. */
        binding->input.total = (int32_t)recovered->mode_population[2] +
                               (int32_t)recovered->mode_population[1] +
                               (int32_t)recovered->mode_population[0];
        memcpy(binding->input.colors, mode_colors, sizeof(mode_colors));
    } else {
        /* fd_50F6_0AEC maps to world.population_black; this draw uses [0]. */
        binding->input.total = session->world.population_black[0];
        memcpy(binding->input.colors, caste_colors, sizeof(caste_colors));
    }
    binding->input.draw_rect = (SimSetupRect){
        slot->window.objects[12].rect.left,
        slot->window.objects[12].rect.top,
        slot->window.objects[12].rect.right,
        slot->window.objects[12].rect.bottom};
    if (animation != NULL) {
        binding->input.animation_set_live = 1;
        binding->input.animation_set_handle = animation->animation_set_handle;
        binding->input.animation_object_id = animation->animation_object_id;
        binding->raster.active_animation_state =
            (void *)session->controls[control_index].animation_resource;
        binding->raster.resolve_animation_bitmap = resolve_animation_bitmap;
    }
    binding->raster.active_registry = session->window_registry;
    binding->raster.active_renderer = active_renderer;
    /* g_3DE2 is graphics-driver state, outside SimSession. For an existing
     * source driver the caller must override this default from its live owner
     * before rasterization if it has changed. The source DATA initializer is 0. */
    binding->raster.text_background = 0;
    return SIM_CONTROL_SESSION_INPUT_OK;
}
