#ifndef SIMANT_PORTABLE_SDL3_LIVE_GAME_H
#define SIMANT_PORTABLE_SDL3_LIVE_GAME_H

#include "../host.h"
#include "../../render/palette.h"
#include "../../game/resources/fonts.h"
#include "../../game/session.h"
#include "../../ui_model/windows/render.h"
#include "../../ui_model/windows/titles.h"

#include <stdint.h>

typedef struct PortableLiveGame PortableLiveGame;

/* The recovered simulation owns substantial binding state, so creation
 * returns an opaque heap-owned adapter. All supplied game/resource/render
 * objects are borrowed and must outlive it. The recovered-core build is
 * selected explicitly with SIMANT_ENABLE_RECOVERED_CORE. */
PortableLiveGame *portable_live_game_create(
    SimSession *session,
    PortableWindowRegistry *registry,
    PortableWindowRenderer *renderer,
    PortableFontSet *fonts,
    const PortableWindowTitlesStringSet *titles,
    PortableWindowTitleProjection *title_projection,
    Host *host,
    const HostPalette *host_palette,
    const PortablePalette *palette);

/* Advance source BIOS time and execute one outer source-loop scheduling pass.
 * This is called independently of host_present; synchronous source UI effects
 * render immediately, while ordinary invalidations render after the tick. */
int portable_live_game_update(PortableLiveGame *game, uint64_t now_ns);

/* Feed one physical SDL host event into the explicitly supported source input
 * projection. Unsupported gameplay events fail with a diagnostic. */
int portable_live_game_event(PortableLiveGame *game, const HostEvent *event);

void portable_live_game_destroy(PortableLiveGame *game);
const char *portable_live_game_error(const PortableLiveGame *game);
int portable_live_game_quit_requested(const PortableLiveGame *game);
uint64_t portable_live_game_completed_ticks(const PortableLiveGame *game);
int portable_live_game_needs_present(const PortableLiveGame *game);
void portable_live_game_mark_presented(PortableLiveGame *game);

#endif
