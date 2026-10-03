#include "graphics_cursor_hooks.h"

#include <string.h>

static SimGraphicsCursorHooks s_hooks;
static int s_bound;
static SimGraphicsCursorHooksStatus s_status =
    SIM_GRAPHICS_CURSOR_HOOKS_NOT_BOUND;

SimGraphicsCursorHooksStatus sim_graphics_cursor_hooks_bind(
    const SimGraphicsCursorHooks *hooks)
{
    if (hooks == NULL || hooks->hide == NULL || hooks->update == NULL ||
        hooks->redraw_if_shown == NULL) {
        s_bound = 0;
        memset(&s_hooks, 0, sizeof(s_hooks));
        return s_status = SIM_GRAPHICS_CURSOR_HOOKS_BAD_ARGUMENT;
    }
    s_hooks = *hooks;
    s_bound = 1;
    return s_status = SIM_GRAPHICS_CURSOR_HOOKS_OK;
}

void sim_graphics_cursor_hooks_unbind(void)
{
    memset(&s_hooks, 0, sizeof(s_hooks));
    s_bound = 0;
    s_status = SIM_GRAPHICS_CURSOR_HOOKS_NOT_BOUND;
}

SimGraphicsCursorHooksStatus sim_graphics_cursor_hooks_status(void)
{
    return s_status;
}

int sim_graphics_cursor_hooks_is_bound(void)
{
    return s_bound;
}

static int call_hook(int (*callback)(void *context))
{
    if (!s_bound)
        return 0;
    if (!callback(s_hooks.context)) {
        s_status = SIM_GRAPHICS_CURSOR_HOOKS_FAILED;
        return 0;
    }
    s_status = SIM_GRAPHICS_CURSOR_HOOKS_OK;
    return 1;
}

int sim_graphics_cursor_hooks_hide(void)
{
    return call_hook(s_hooks.hide);
}

int sim_graphics_cursor_hooks_update(void)
{
    return call_hook(s_hooks.update);
}

int sim_graphics_cursor_hooks_redraw_if_shown(void)
{
    return call_hook(s_hooks.redraw_if_shown);
}
