#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_CURSOR_HOOKS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_CURSOR_HOOKS_H

#ifdef __cplusplus
extern "C" {
#endif

/* Shared source-cursor service bridge used by S00 capture and cached-tile
 * drawing. The application binds these to the active m1B73 mouse runtime. */
typedef struct SimGraphicsCursorHooks {
    void *context;
    int (*hide)(void *context);             /* source f_1B73_0196 */
    int (*update)(void *context);           /* source f_1B73_00D9 */
    int (*redraw_if_shown)(void *context);  /* source f_1B73_04BB */
} SimGraphicsCursorHooks;

typedef enum SimGraphicsCursorHooksStatus {
    SIM_GRAPHICS_CURSOR_HOOKS_OK = 0,
    SIM_GRAPHICS_CURSOR_HOOKS_NOT_BOUND,
    SIM_GRAPHICS_CURSOR_HOOKS_BAD_ARGUMENT,
    SIM_GRAPHICS_CURSOR_HOOKS_FAILED
} SimGraphicsCursorHooksStatus;

SimGraphicsCursorHooksStatus sim_graphics_cursor_hooks_bind(
    const SimGraphicsCursorHooks *hooks);
void sim_graphics_cursor_hooks_unbind(void);
SimGraphicsCursorHooksStatus sim_graphics_cursor_hooks_status(void);
int sim_graphics_cursor_hooks_is_bound(void);
int sim_graphics_cursor_hooks_hide(void);
int sim_graphics_cursor_hooks_update(void);
int sim_graphics_cursor_hooks_redraw_if_shown(void);

#ifdef __cplusplus
}
#endif
#endif
