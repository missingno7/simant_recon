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
 * its own VGA plane set and an unoccluded clip list, and each save-under box
 * (GSaveRect .. f_1CE2_056C) its own popup planes; game algorithms, window
 * records, the stack, hit testing and draw hooks stay canonical. Windows not
 * hosted keep sharing the card's planes, so with nothing hosted every access
 * is the single-screen path. */

enum { SIM_HOSTING_SLOTS = 45 };

typedef struct SimHostedWindowView {
    int16_t id;            /* logical window ID (slot << 8) */
    int open;              /* in the canonical window stack */
    int top;               /* g_5702[0] */
    int16_t left, top_y, right, bottom;   /* logical screen rect (exclusive) */
    int16_t drag_left, drag_top, drag_right, drag_bottom; /* object 1: title strip */
    uint16_t flags;        /* record +0x1C: 4 close box, 8 resizable, 0x40 modal */
    int16_t margin;        /* chrome inset */
    int anchored;          /* placed from its record on every open (Win16) */
    char title[64];
    const SimVgaPlanes *planes;
} SimHostedWindowView;

typedef struct SimHostedPopupView {
    int16_t left, top, right, bottom;     /* logical screen rect */
    const SimVgaPlanes *planes;
} SimHostedPopupView;

/* Hosts `ids` (logical window IDs) on separate plane sets of `vga`. */
int sim_window_hosting_enable(SimVga *vga, const int16_t *ids, unsigned count);
int sim_window_hosting_enabled(void);
/* Bumped whenever the stack or a hosted window's rect or title changes. */
unsigned sim_window_hosting_generation(void);
int sim_window_hosting_view(unsigned index, SimHostedWindowView *view);
unsigned sim_window_hosting_count(void);
/* Open save-under popups, bottom first; the serial changes on open/close. */
unsigned sim_window_hosting_popups(SimHostedPopupView *views, unsigned capacity);
unsigned sim_window_hosting_popup_serial(void);
/* The map window's indicator of the edit view (mapCursorRect XOR outline):
 * when owned, its XOR is left to the presentation, which draws the indicator
 * while the canonical cursor is shown. */
void sim_window_hosting_own_map_cursor(int owned);
int sim_window_hosting_map_cursor_shown(void);
/* Logical stack queries for input routing (point is logical screen space). */
int16_t sim_window_hosting_owner_at(int16_t x, int16_t y);  /* topmost window or 0x8000 */
int16_t sim_window_hosting_top(void);
int sim_window_hosting_is_hosted(int16_t id);

/* Presentation's handler for the game's event pump (f_218D_02D5 -> the
 * empty f_1B28_0069 stub), where Win16 dispatched window messages. Only the
 * pump may call the actions below; they run the canonical window code. */
void sim_window_hosting_set_pump(void (*pump)(void));
int sim_window_hosting_close(int16_t id);                   /* WM_CLOSE */
int sim_window_hosting_raise(int16_t id);                   /* WM_MOUSEACTIVATE */
int sim_window_hosting_resize(int16_t id, int width, int height); /* WM_SIZE */

#endif
