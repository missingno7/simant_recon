#ifndef SIMANT_SDL3_MODERN_GAME_VIEW_H
#define SIMANT_SDL3_MODERN_GAME_VIEW_H

#include <SDL3/SDL.h>
#include "portable/platform/host.h"
#include "portable/whole_program/modern/world_view.h"
#include "../graphics_vga.h"

/* Modern Game Window map area (--windows): a world-space renderer over the
 * read-only world view, at any size and zoom, with its own camera.
 *
 * Ownership: the camera here is presentation state; MapPnt stays the game's.
 * Game-originated MapPnt changes move the modern camera by the same amount
 * (a plane change re-centres it on the edit view). User pans and zooms
 * re-centre the canonical edit view on the modern camera through the game's
 * own scroll (f_0250_0D10) in the event pump, so the overview, edge scrolling,
 * saved games and every other MapPnt reader see one camera. The canonical
 * edit view keeps drawing at game cadence (its draw path consumes the RNG);
 * rendering here never runs game code that writes state. */

/* Draw the map area `area` (client pixels) of the Game Window. `planes` and
 * `left`/`top` locate the hosted canonical edit view (logical screen origin
 * of the planes' window client), used only for not-yet-modern overlays. */
int modern_game_view_render(SDL_Renderer *renderer, const SDL_FRect *area, int scale,
                            const HostPalette *palette, const SimVgaPlanes *planes);
/* Linear filtering of zoomed world pixels instead of nearest (pixel-exact). */
void modern_game_view_set_smooth(int smooth);
void modern_game_view_shutdown(void);

/* Modern -> canonical camera requests; runs in the game's event pump. */
void modern_game_view_pump(void);

/* Input. View coordinates are map-area pixels. */
/* Logical screen point the game sees for a view point; 1 when it lies inside
 * the canonical edit view (a click there reaches the same world tile). */
int modern_game_view_to_logical(float vx, float vy, float *lx, float *ly);
/* Keep a logical point inside the edit view's tile rectangle. */
void modern_game_view_clamp_logical(float *lx, float *ly);
/* Inverse for logical points in the edit view's tile rectangle. */
int modern_game_view_to_view(float lx, float ly, float *vx, float *vy);
/* 1 when the view point shows a world tile. */
int modern_game_view_in_world(float vx, float vy);
void modern_game_view_wheel(float vx, float vy, float steps);
void modern_game_view_pan(int phase, float vx, float vy);   /* 1 begin, 0 move, -1 end */
/* A button held in the map area: the canonical edit view keeps that point. */
void modern_game_view_hold(int held, float vx, float vy);
void modern_game_view_hold_move(float vx, float vy);
/* Ask the canonical edit view to include a view point before a click is
 * delivered; settled once the pump has scrolled (or nothing was needed). */
void modern_game_view_request_include(float vx, float vy);
int modern_game_view_include_settled(void);

/* The overview indicator: the modern visible area in the map window's
 * logical coordinates, clipped to the overview's world thumbnail. */
int modern_game_view_overview(ModernRect *indicator);

#endif
