#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_ZOOM_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_ZOOM_H

#include "window.h"

#include <stddef.h>
#include <stdint.h>

/* Runtime Win fields used by S26 o26_39C7_0000; resource bytes stay immutable. */
enum {
    PORTABLE_WINDOW_ZOOMED = 0x0080,
    PORTABLE_WINDOW_ZOOM_ENABLED = 0x0100,
    PORTABLE_WINDOW_ZOOM_SOURCE_FLAG_1000 = 0x1000
};

typedef enum PortableWindowZoomHostRepaintPolicy {
    PORTABLE_WINDOW_ZOOM_HOST_REPAINT_FULL_Z_ORDER = 1
} PortableWindowZoomHostRepaintPolicy;

typedef struct PortableWindowZoomState {
    PortableWindowRect window_rect; /* runtime Win.rect */
    PortableWindowRect frame_rect;  /* Raw Obj x/y/width/height words, not edges. */
    PortableWindowRect zoom_rect;   /* runtime Win.zoomRect */
    uint16_t flags;
    int16_t min_width, min_height;
    int16_t grid_x, grid_y;
    uint8_t has_zoom_rect;
} PortableWindowZoomState;

typedef struct PortableWindowZoomBounds {
    int16_t desktop_top; /* fd_50F6_393C.bottom */
    int16_t screen_right; /* g_3DB2 */
    int16_t screen_bottom; /* g_3DB4 */
} PortableWindowZoomBounds;

/* The DOS caller's local `r.right`/`r.bottom` are not initialized before the
   first mode-0 constraint call. Supply the observed stack residue explicitly. */
typedef struct PortableWindowZoomResidue {
    int16_t first_rect_right;
    int16_t first_rect_bottom;
    PortableWindowRect saved_rect; /* Local saved rect used by clip restore. */
    PortableWindowRect unzoom_obj_rect; /* win_GetObjRect result after recalc. */
} PortableWindowZoomResidue;

typedef enum PortableWindowZoomStatus {
    PORTABLE_WINDOW_ZOOM_OK = 0,
    PORTABLE_WINDOW_ZOOM_BAD_ARGUMENT,
    PORTABLE_WINDOW_ZOOM_DISABLED,
    PORTABLE_WINDOW_ZOOM_NO_PROGRESS,
    PORTABLE_WINDOW_ZOOM_ITERATION_LIMIT
} PortableWindowZoomStatus;

/* Initialize the unzoomed state from a decoded kind-0 resource and its live
   runtime flags. The caller supplies the current Win.rect, since it may have
   been recalculated after resource loading. Object zero's raw x/y/width/height
   are read from the decoded source offsets. */
PortableWindowZoomStatus portable_window_zoom_state_from_resource(
    PortableWindowZoomState *state,
    const PortableWindowResource *resource,
    PortableWindowRect runtime_window_rect,
    uint16_t runtime_flags);

typedef enum PortableWindowZoomStepKind {
    PORTABLE_ZOOM_LOCK,
    PORTABLE_ZOOM_RECALCULATE,
    PORTABLE_ZOOM_REBUILD_CLIPS,
    PORTABLE_ZOOM_WINDOW_CALLBACK,
    PORTABLE_ZOOM_CLIP_SET,
    PORTABLE_ZOOM_CLIP_RESTORE,
    PORTABLE_ZOOM_CLIP_PUSH,
    PORTABLE_ZOOM_RESET_CLIP,
    PORTABLE_ZOOM_CLIP_POP,
    PORTABLE_ZOOM_CLIP_EXCLUDE,
    PORTABLE_ZOOM_OBJECT_RECT_QUERY,
    PORTABLE_ZOOM_CLIP_INTERSECT,
    PORTABLE_ZOOM_DRAW_WINDOW,
    PORTABLE_ZOOM_BORDER_08EA,
    PORTABLE_ZOOM_BORDER_0831,
    PORTABLE_ZOOM_UNLOCK
} PortableWindowZoomStepKind;

typedef struct PortableWindowZoomStep {
    PortableWindowZoomStepKind kind;
    int16_t window_id;
    PortableWindowRect rect;
} PortableWindowZoomStep;

/* Implements S26 o26_39C7_022F, including signed DOS-int geometry arithmetic. */
PortableWindowZoomStatus portable_window_zoom_constrain(
    const PortableWindowZoomState *state, const PortableWindowZoomBounds *bounds,
    int mode, PortableWindowRect *rect, size_t iteration_limit);

/* Toggle geometry and emit the source-ordered logical redraw/effect trace.
   open_windows is the DOS g_5702 order, terminated by 0x8000. */
PortableWindowZoomStatus portable_window_zoom_toggle(
    PortableWindowZoomState *state, const PortableWindowZoomBounds *bounds,
    const PortableWindowZoomResidue *residue,
    int16_t window_id, const int16_t *open_windows, size_t open_window_capacity,
    const PortableWindowRect *open_object_rects,
    PortableWindowZoomStep *steps, size_t step_capacity, size_t *step_count,
    size_t iteration_limit);

/* SDL host repaint boundary: after a successful geometry transition, redraw
   all open windows in current z-order (or repaint the full logical surface).
   Use PORTABLE_WINDOW_ZOOM_HOST_REPAINT_FULL_Z_ORDER. This intentionally does
   not emulate DOS clip-list history. In particular, it must not synthesize
   the original function's uninitialized `saved` Rect. */

#endif
