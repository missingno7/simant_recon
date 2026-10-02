#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_GAME_VIEW_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_GAME_VIEW_H

#include "registry.h"
#include "../../game/render/map.h"

/* The source game uses window 0 / object 4 as the Edit map viewport. */
enum {
    PORTABLE_GAME_VIEW_WINDOW_ID = 0,
    PORTABLE_GAME_VIEW_OBJECT_INDEX = 4,
    PORTABLE_GAME_VIEW_CELL_SIZE = 16
};

typedef enum PortableGameViewStatus {
    PORTABLE_GAME_VIEW_OK = 0,
    PORTABLE_GAME_VIEW_BAD_ARGUMENT,
    PORTABLE_GAME_VIEW_WINDOW_NOT_READY,
    PORTABLE_GAME_VIEW_UNSUPPORTED_GEOMETRY,
    PORTABLE_GAME_VIEW_UNSUPPORTED_MAP_STATE,
    PORTABLE_GAME_VIEW_MAP_RENDER_FAILED
} PortableGameViewStatus;

/* Values in this record correspond to live source globals consumed by
 * f_0250_1018 and LoadTiles. They stay explicit because no host UI state is
 * synthesized here. Use ega_profile 0 or 8, and pheromone_mode -1..4. */
typedef struct PortableGameViewState {
    int16_t ega_profile;
    int16_t pheromone_mode;
    int16_t animation_base; /* fd_50F6_049A */
    int16_t queen_frame;    /* fd_50F6_0496 */
    int16_t young_frame;    /* fd_50F6_0502 */
    int16_t caste_frame;    /* fd_50F6_04C2 */
} PortableGameViewState;

typedef struct PortableGameView {
    PortableWindowRect viewport;
    SimMapView map;
} PortableGameView;

typedef struct PortableGameViewRenderResult {
    size_t cells_drawn;
    size_t cells_with_life;
} PortableGameViewRenderResult;

/* Resolve the initial default-game view from the actual, already loaded and recalculated window-0 object-4
 * geometry. CenterEdit(MeLocX,MeLocY) semantics are applied using the
 * generated world's current player location, then f_0250_0F2C's plane bounds
 * clamp the camera. Call for the startup view; later user camera movement must
 * retain the live camera origin instead of invoking this recenter operation. */
PortableGameViewStatus portable_game_view_resolve(
    const PortableWindowRegistry *registry,
    const SimGameWorld *world,
    const PortableGameViewState *state,
    PortableGameView *view);

/* Draws map cells only, clipped to the source viewport and caller's current
 * framebuffer clip. Window frame and UI objects remain the native window
 * renderer's responsibility; unsupported object paths must remain errors. */
PortableGameViewStatus portable_game_view_render(
    const SimGameWorld *world,
    const PortableGameView *view,
    const PortableTileSet *tileset,
    PortableFramebuffer *framebuffer,
    PortableGameViewRenderResult *result);

const char *portable_game_view_status_string(PortableGameViewStatus status);

#endif
