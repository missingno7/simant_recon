#include "balloons.h"

#include <limits.h>
#include <string.h>

static int16_t signed_i16(uint16_t bits)
{
    if (bits <= (uint16_t)INT16_MAX)
        return (int16_t)bits;
    return (int16_t)(-1 - (int16_t)(UINT16_MAX - bits));
}

static int16_t add_i16(int16_t left, int16_t right)
{
    return signed_i16((uint16_t)((uint16_t)left + (uint16_t)right));
}

void portable_balloons_init(PortableBalloonState *state)
{
    if (state != NULL)
        memset(state, 0, sizeof(*state));
}

int portable_balloon_is_visible(const PortableBalloonViewport *viewport,
                                int16_t plane, int16_t x, int16_t y)
{
    int16_t right, bottom, y_minus_three;
    if (viewport == NULL || plane != viewport->plane)
        return 0;
    right = add_i16(viewport->left, viewport->columns);
    bottom = add_i16(viewport->top, viewport->rows);
    y_minus_three = add_i16(y, -3);
    if (x < viewport->left || x >= right)
        return 0;
    if (y_minus_three < viewport->top || y >= bottom)
        return 0;
    return 1;
}

PortableBalloonStatus portable_balloon_submit(
    PortableBalloonState *state, PortableBalloonCueKind kind,
    const PortableBalloonViewport *viewport,
    int16_t x, int16_t y, int16_t plane)
{
    PortableBalloonCueState *cue;
    if (state == NULL || kind < 0 || kind >= PORTABLE_BALLOON_CUE_COUNT ||
        viewport == NULL)
        return PORTABLE_BALLOON_BAD_ARGUMENT;
    cue = &state->cue[kind];
    if (cue->active != 0)
        return PORTABLE_BALLOON_OK;
    if (!portable_balloon_is_visible(viewport, plane, x, y))
        return PORTABLE_BALLOON_OK;
    if (cue->displayed.x == x && cue->displayed.y == y &&
        cue->displayed_plane == plane) {
        ++cue->active;
        return PORTABLE_BALLOON_OK;
    }
    cue->pending.x = x;
    cue->pending.y = y;
    cue->pending_plane = plane;
    return PORTABLE_BALLOON_OK;
}

void portable_balloons_simulation_reset(PortableBalloonState *state,
                                        int16_t simulation_mode)
{
    size_t i;
    if (state == NULL || simulation_mode != 1)
        return;
    for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i) {
        state->cue[i].active = 0;
        state->cue[i].pending.x = -1;
        state->cue[i].pending.y = -1;
    }
}

PortableBalloonStatus portable_balloons_prepare_frame(
    PortableBalloonState *state, int enabled, int16_t sprite_state,
    PortableBalloonFrameResult *result)
{
    static const PortableBalloonCueKind source_order[] = {
        PORTABLE_BALLOON_FIGHT,
        PORTABLE_BALLOON_EGG,
        PORTABLE_BALLOON_QUEEN,
        PORTABLE_BALLOON_REST
    };
    PortableBalloonFrameResult updated = {0};
    size_t i;
    if (state == NULL || result == NULL)
        return PORTABLE_BALLOON_BAD_ARGUMENT;
    *result = updated;
    if (!enabled || sprite_state != -1)
        return PORTABLE_BALLOON_OK;
    for (i = 0; i < sizeof(source_order) / sizeof(source_order[0]); ++i) {
        PortableBalloonCueKind kind = source_order[i];
        PortableBalloonCueState *cue = &state->cue[kind];
        if (cue->active == 0 && cue->pending.x >= 0 && cue->pending.y >= 0) {
            cue->displayed = cue->pending;
            cue->displayed_plane = cue->pending_plane;
            ++cue->active;
            updated.activation_order[updated.activated_count++] = kind;
            updated.activated_mask |= (uint8_t)(1u << kind);
        }
    }
    *result = updated;
    return PORTABLE_BALLOON_OK;
}
