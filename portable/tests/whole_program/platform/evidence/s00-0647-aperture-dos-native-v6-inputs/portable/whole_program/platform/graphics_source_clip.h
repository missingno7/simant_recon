#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_SOURCE_CLIP_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_SOURCE_CLIP_H

#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/window_source_rects.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Canonical native owners for DOS DGROUP 55B3:5A9C and the far pointer at
 * 55B3:5AAC. g_5AAE is the pointer's segment word, not another global. */
/* Original 5A9C..5AAB is a full-screen rectangle followed by a sentinel
 * rectangle. Source clip_Off and clip_SubExclude walk it as a list. */
extern struct Rect sim_source_screen_clip_list[2];
#define g_5A9C (sim_source_screen_clip_list[0])
extern struct Rect *g_5AAC;
extern int16_t fd_55B3_3DE6;
extern int16_t fd_55B3_3DE8;

/* The DOS resident default before a video mode is selected is deliberately
 * retained as 0,0,349,639. f_205F_0004 later writes right/bottom to the chosen
 * logical dimensions. This binds the live graphics owner but does not invent
 * or install a clipping list. */
SimGraphicsStatus sim_graphics_source_clip_bind(SimGraphicsDriver *graphics);
void sim_graphics_source_clip_unbind(void);
SimGraphicsDriver *sim_graphics_source_clip_owner(void);
int sim_graphics_source_clip_active(void);
struct Rect *const *sim_graphics_source_clip_slot(void);

#ifdef __cplusplus
}
#endif
#endif
