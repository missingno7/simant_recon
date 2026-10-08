#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_WINDOW_HOSTING_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_WINDOW_HOSTING_H

#include "graphics_vga.h"
#include <stdint.h>

/* Native multi-window presentation boundary (DOS window-system clipping).
 *
 * DOS SimAnt composites every logical window into one VGA screen: m1E57
 * computes each window's visible region from the stack g_5702 and
 * clip_SetWin selects it before the window draws. Win16 SimAnt replaces that
 * DOS window system with native windows (its clip_SetWin is empty; each
 * window draws through its own DC). Here a hosted logical window instead gets
 * its own VGA plane set and an unoccluded clip list; game algorithms, window
 * records, the stack, hit testing and draw hooks stay canonical. Windows not
 * hosted keep sharing the card's planes, so with nothing hosted every access
 * is the single-screen path. */

enum { SIM_HOSTING_SLOTS = 45 };

typedef struct SimHostedWindowView {
    int16_t id;            /* logical window ID (slot << 8) */
    int open;              /* in the canonical window stack */
    int top;               /* g_5702[0] */
    int16_t left, top_y, right, bottom;   /* logical screen rect (exclusive) */
    int16_t drag_left, drag_top, drag_right, drag_bottom; /* object 1: drag bar */
    const SimVgaPlanes *planes;
} SimHostedWindowView;

/* Hosts `ids` (logical window IDs) on separate plane sets of `vga`. */
int sim_window_hosting_enable(SimVga *vga, const int16_t *ids, unsigned count);
int sim_window_hosting_enabled(void);
/* Bumped whenever the stack or a hosted window's rect changes. */
unsigned sim_window_hosting_generation(void);
int sim_window_hosting_view(unsigned index, SimHostedWindowView *view);
unsigned sim_window_hosting_count(void);
/* Logical stack queries for input routing (point is logical screen space). */
int16_t sim_window_hosting_owner_at(int16_t x, int16_t y);  /* topmost window or 0x8000 */
int sim_window_hosting_is_hosted(int16_t id);
/* A logical point inside `id` that no window above it covers; 0 if none. */
int sim_window_hosting_visible_point(int16_t id, int16_t *x, int16_t *y);
/* Software cursor draw scope: 1 show, 2 hide, 0 leave. The cursor is drawn
 * on the surface of the native window under the mouse and hidden there. */
void sim_window_hosting_cursor_scope(int mode);
/* Presentation reports the hosted window under the mouse (0x8000: root). */
void sim_window_hosting_set_pointer_window(int16_t id);

#endif
