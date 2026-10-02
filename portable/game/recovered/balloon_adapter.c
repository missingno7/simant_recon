#include "balloon_adapter.h"

#include <stddef.h>

static void load_cue(PortableBalloonState *state,
                     PortableBalloonCueKind kind)
{
    PortableBalloonCueState *cue = &state->cue[kind];
    switch (kind) {
    case PORTABLE_BALLOON_EGG:
        cue->active = fd_50F6_0EF6;
        cue->displayed.x = fd_50F6_08DE.x;
        cue->displayed.y = fd_50F6_08DE.y;
        cue->displayed_plane = fd_50F6_0AD8;
        /* RecoveredPoint is the m0894 v/h type view; its first physical word
         * is m0250 Pnt.x and its second is Pnt.y. */
        cue->pending.x = fd_50F6_0852.v;
        cue->pending.y = fd_50F6_0852.h;
        cue->pending_plane = fd_50F6_0ACA;
        break;
    case PORTABLE_BALLOON_FIGHT:
        cue->active = fd_50F6_0F06;
        cue->displayed.x = fd_50F6_09F2.x;
        cue->displayed.y = fd_50F6_09F2.y;
        cue->displayed_plane = fd_50F6_0B06;
        cue->pending.x = fd_50F6_08EC.v;
        cue->pending.y = fd_50F6_08EC.h;
        cue->pending_plane = fd_50F6_0AEA;
        break;
    case PORTABLE_BALLOON_QUEEN:
        cue->active = fd_50F6_0F10;
        cue->displayed.x = fd_50F6_0A8A.x;
        cue->displayed.y = fd_50F6_0A8A.y;
        cue->displayed_plane = fd_50F6_0C3A;
        cue->pending.x = fd_50F6_0A02.v;
        cue->pending.y = fd_50F6_0A02.h;
        cue->pending_plane = fd_50F6_0B08;
        break;
    case PORTABLE_BALLOON_REST:
        cue->active = fd_50F6_0F2E;
        cue->displayed.x = fd_50F6_0AB2.x;
        cue->displayed.y = fd_50F6_0AB2.y;
        cue->displayed_plane = fd_50F6_0D9A;
        cue->pending.x = fd_50F6_0AA2.v;
        cue->pending.y = fd_50F6_0AA2.h;
        cue->pending_plane = fd_50F6_0D68;
        break;
    case PORTABLE_BALLOON_CUE_COUNT:
        break;
    }
}

static void store_cue(const PortableBalloonState *state,
                      PortableBalloonCueKind kind)
{
    const PortableBalloonCueState *cue = &state->cue[kind];
    switch (kind) {
    case PORTABLE_BALLOON_EGG:
        fd_50F6_0EF6 = cue->active;
        fd_50F6_08DE.x = cue->displayed.x;
        fd_50F6_08DE.y = cue->displayed.y;
        fd_50F6_0AD8 = cue->displayed_plane;
        fd_50F6_0852.v = cue->pending.x;
        fd_50F6_0852.h = cue->pending.y;
        fd_50F6_0ACA = cue->pending_plane;
        break;
    case PORTABLE_BALLOON_FIGHT:
        fd_50F6_0F06 = cue->active;
        fd_50F6_09F2.x = cue->displayed.x;
        fd_50F6_09F2.y = cue->displayed.y;
        fd_50F6_0B06 = cue->displayed_plane;
        fd_50F6_08EC.v = cue->pending.x;
        fd_50F6_08EC.h = cue->pending.y;
        fd_50F6_0AEA = cue->pending_plane;
        break;
    case PORTABLE_BALLOON_QUEEN:
        fd_50F6_0F10 = cue->active;
        fd_50F6_0A8A.x = cue->displayed.x;
        fd_50F6_0A8A.y = cue->displayed.y;
        fd_50F6_0C3A = cue->displayed_plane;
        fd_50F6_0A02.v = cue->pending.x;
        fd_50F6_0A02.h = cue->pending.y;
        fd_50F6_0B08 = cue->pending_plane;
        break;
    case PORTABLE_BALLOON_REST:
        fd_50F6_0F2E = cue->active;
        fd_50F6_0AB2.x = cue->displayed.x;
        fd_50F6_0AB2.y = cue->displayed.y;
        fd_50F6_0D9A = cue->displayed_plane;
        fd_50F6_0AA2.v = cue->pending.x;
        fd_50F6_0AA2.h = cue->pending.y;
        fd_50F6_0D68 = cue->pending_plane;
        break;
    case PORTABLE_BALLOON_CUE_COUNT:
        break;
    }
}

static void submit(PortableBalloonCueKind kind,
                   int16_t x, int16_t y, int16_t plane)
{
    PortableBalloonState state;
    portable_balloons_init(&state);
    load_cue(&state, kind);
    (void)portable_balloon_submit(&state, kind, &(PortableBalloonViewport){
        MapPlane, fd_50F6_0508[0], fd_50F6_0508[1],
        fd_50F6_10E0, fd_50F6_10DE
    }, x, y, plane);
    store_cue(&state, kind);
}

void sim_recovered_egg_balloons(int16_t x, int16_t y, int16_t plane)
{
    submit(PORTABLE_BALLOON_EGG, x, y, plane);
}

void sim_recovered_fight_balloons(int16_t x, int16_t y, int16_t plane)
{
    submit(PORTABLE_BALLOON_FIGHT, x, y, plane);
}

void sim_recovered_queen_balloons(int16_t x, int16_t y, int16_t plane)
{
    submit(PORTABLE_BALLOON_QUEEN, x, y, plane);
}

void sim_recovered_rest_balloons(int16_t x, int16_t y, int16_t plane)
{
    submit(PORTABLE_BALLOON_REST, x, y, plane);
}

void sim_recovered_balloons_simulation_reset(int16_t simulation_mode)
{
    PortableBalloonState state;
    size_t i;
    if (simulation_mode != 1)
        return;
    portable_balloons_init(&state);
    for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i)
        load_cue(&state, (PortableBalloonCueKind)i);
    portable_balloons_simulation_reset(&state, simulation_mode);
    for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i)
        store_cue(&state, (PortableBalloonCueKind)i);
}
