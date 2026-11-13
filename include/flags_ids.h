/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_FLAGS_IDS_H
#define SIMANT_FLAGS_IDS_H

/* Visibility bit read/written by win_SetObjVisibleState. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_VISIBLE 0x1

/* Closes when another window is raised or the desktop is clicked, unless dismissal is inhibited. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_AUTO_DISMISS 0x1

/* Selectable hit-region registration bit. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_SELECTABLE 0x2

/* Title-object events call win_track_move when this bit is set. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_TITLE_DRAG 0x2

/* Selected state read/written by win_SetObjSelectedStateI. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_SELECTED 0x4

/* Registers and draws the window close bitmap/control. Evidence: src/window/object_attributes.c:484
 * (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open); src/window/object_geometry.c:361
 * (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_CLOSE_CONTROL 0x4

/* Click feedback toggles selection persistently instead of flashing it. Evidence:
 * src/window/object_attributes.c:228 (win_SetObjSelectedStateI); src/window/events.c:35
 * (win_dispatch_object_event); src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218
 * (win_DrawObjectI). */
#define OBJ_FLAG_TOGGLE_SELECT 0x8

/* Registers and draws the window resize bitmap/control. Evidence: src/window/object_attributes.c:484
 * (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open); src/window/object_geometry.c:361
 * (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_RESIZE_CONTROL 0x8

/* Registers a proximity region and permits hover highlighting. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_PROXIMITY 0x10

/* Selecting this object first clears its group selection. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_EXCLUSIVE_GROUP 0x20

/* win_Recalc replaces size using win_AutoSize. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_AUTO_SIZE 0x40

/* Desktop-click dispatch tests this bit before closing an auto-dismiss window. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_INHIBIT_AUTO_DISMISS 0x40

/* Current zoom state, tested by win_is_zoomed. Evidence: src/window/object_attributes.c:484
 * (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open); src/window/object_geometry.c:361
 * (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_ZOOMED 0x80

/* Window has a zoom control; win_toggle_zoom rejects windows without it. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_ZOOM_CONTROL 0x100

/* Bits 7 and 8 are shifted into the gr_JustifyStrInRect alignment argument. Evidence:
 * src/window/object_attributes.c:228 (win_SetObjSelectedStateI); src/window/events.c:35
 * (win_dispatch_object_event); src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218
 * (win_DrawObjectI). */
#define OBJ_FLAG_JUSTIFY_MASK 0x180

/* win_DrawObjectI pushes object rectangle clipping while rendering. Evidence:
 * src/window/object_attributes.c:228 (win_SetObjSelectedStateI); src/window/events.c:35
 * (win_dispatch_object_event); src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218
 * (win_DrawObjectI). */
#define OBJ_FLAG_CLIP_CONTENT 0x200

/* Set on open/swap-in and cleared on close/swap-out. Evidence: src/window/object_attributes.c:484
 * (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open); src/window/object_geometry.c:361
 * (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_OPEN 0x200

/* Suppresses selected exclusive-group deselection in click dispatch; list clicks also test it. Evidence:
 * src/window/object_attributes.c:228 (win_SetObjSelectedStateI); src/window/events.c:35
 * (win_dispatch_object_event); src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218
 * (win_DrawObjectI). */
#define OBJ_FLAG_STICKY_SELECTION 0x400

/* Registers/draws the lower-window control with EVENT_WINDOW_LOWER. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_LOWER_CONTROL 0x400

/* Enables selection feedback in win_dispatch_object_event. Evidence: src/window/object_attributes.c:228
 * (win_SetObjSelectedStateI); src/window/events.c:35 (win_dispatch_object_event);
 * src/window/object_geometry.c:305 (win_Recalc); src/window/drawing.c:218 (win_DrawObjectI). */
#define OBJ_FLAG_CLICK_FEEDBACK 0x800

/* Closed resources with this bit release nested handles and become discardable at final unlock. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_DISCARD_CLOSED 0x800

/* Click-class bits compared between successive events when recognizing repeated clicks. Evidence:
 * src/window/events.c:35 (win_dispatch_object_event). */
#define EVENT_MOD_CLICK_MASK 0xa00

/* Open temporarily adjusts object-zero origin into screen bounds; close restores it. Evidence:
 * src/window/object_attributes.c:484 (win_IsWinOpen); src/window/lifecycle.c:207 (win_Open);
 * src/window/object_geometry.c:361 (win_set_frame_hit_rects); src/window/locking.c:117 (win_UnlockWin). */
#define WIN_FLAG_KEEP_ON_SCREEN 0x1000

/* Bits synthesized for successive clicks on the same object within ten ticks. Evidence:
 * src/window/events.c:35 (win_dispatch_object_event). */
#define EVENT_MOD_DOUBLE_CLICK_MASK 0x6000

#endif
