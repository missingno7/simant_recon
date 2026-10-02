#include "../../ui_model/balloons/balloons.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static PortableBalloonViewport normal_view(void)
{
    PortableBalloonViewport viewport = {7, 10, 20, 40, 30};
    return viewport;
}

static void test_visibility_edges_and_word_wrap(void)
{
    PortableBalloonViewport viewport = normal_view();
    assert(portable_balloon_is_visible(&viewport, 7, 10, 23));
    assert(portable_balloon_is_visible(&viewport, 7, 49, 49));
    assert(!portable_balloon_is_visible(&viewport, 6, 10, 23));
    assert(!portable_balloon_is_visible(&viewport, 7, 9, 23));
    assert(!portable_balloon_is_visible(&viewport, 7, 50, 23));
    assert(!portable_balloon_is_visible(&viewport, 7, 10, 22));
    assert(!portable_balloon_is_visible(&viewport, 7, 10, 50));

    /* The source performs viewport-end and y-3 operations as signed DOS ints. */
    viewport.left = INT16_C(32760);
    viewport.top = INT16_C(32760);
    viewport.columns = 10;
    viewport.rows = 10;
    assert(!portable_balloon_is_visible(&viewport, 7, INT16_MIN, INT16_MIN));
    viewport.left = 10;
    assert(portable_balloon_is_visible(&viewport, 7, 10, INT16_MIN));
    assert(!portable_balloon_is_visible(&viewport, 7, 10, -32766));
}

static void test_pending_activation_reset_and_dedup(void)
{
    PortableBalloonState state;
    PortableBalloonViewport viewport = normal_view();
    PortableBalloonFrameResult frame;
    portable_balloons_init(&state);
    portable_balloons_simulation_reset(&state, 1);

    /* Pending writes overwrite while inactive; invisible requests do nothing. */
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_EGG, &viewport,
                                  15, 25, 7) == PORTABLE_BALLOON_OK);
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_EGG, &viewport,
                                  30, 30, 7) == PORTABLE_BALLOON_OK);
    assert(state.cue[PORTABLE_BALLOON_EGG].pending.x == 30);
    assert(state.cue[PORTABLE_BALLOON_EGG].pending.y == 30);
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_EGG, &viewport,
                                  50, 30, 7) == PORTABLE_BALLOON_OK);
    assert(state.cue[PORTABLE_BALLOON_EGG].pending.x == 30);

    /* DrawCurBalloons activates only with both source gates satisfied. */
    assert(portable_balloons_prepare_frame(&state, 0, -1, &frame) ==
           PORTABLE_BALLOON_OK);
    assert(frame.activated_count == 0);
    assert(portable_balloons_prepare_frame(&state, 1, 0, &frame) ==
           PORTABLE_BALLOON_OK);
    assert(frame.activated_count == 0);
    assert(portable_balloons_prepare_frame(&state, 1, -1, &frame) ==
           PORTABLE_BALLOON_OK);
    assert(frame.activated_count == 1 &&
           frame.activation_order[0] == PORTABLE_BALLOON_EGG);
    assert(state.cue[PORTABLE_BALLOON_EGG].active == 1);
    assert(state.cue[PORTABLE_BALLOON_EGG].displayed.x == 30 &&
           state.cue[PORTABLE_BALLOON_EGG].displayed.y == 30 &&
           state.cue[PORTABLE_BALLOON_EGG].displayed_plane == 7);

    /* Active cues ignore new requests until the source mode-1 reset. */
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_EGG, &viewport,
                                  40, 40, 7) == PORTABLE_BALLOON_OK);
    assert(state.cue[PORTABLE_BALLOON_EGG].pending.x == 30);
    portable_balloons_simulation_reset(&state, 0);
    assert(state.cue[PORTABLE_BALLOON_EGG].active == 1 &&
           state.cue[PORTABLE_BALLOON_EGG].pending.x == 30);
    portable_balloons_simulation_reset(&state, 1);
    assert(state.cue[PORTABLE_BALLOON_EGG].active == 0);
    assert(state.cue[PORTABLE_BALLOON_EGG].pending.x == -1 &&
           state.cue[PORTABLE_BALLOON_EGG].pending.y == -1);
    assert(state.cue[PORTABLE_BALLOON_EGG].displayed.x == 30 &&
           state.cue[PORTABLE_BALLOON_EGG].displayed.y == 30 &&
           state.cue[PORTABLE_BALLOON_EGG].displayed_plane == 7);

    /* Reset preserves prior displayed coordinates; matching cue dedupes into
     * active state immediately instead of waiting for pending activation. */
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_EGG, &viewport,
                                  30, 30, 7) == PORTABLE_BALLOON_OK);
    assert(state.cue[PORTABLE_BALLOON_EGG].active == 1);
    assert(state.cue[PORTABLE_BALLOON_EGG].pending.x == -1);
    assert(portable_balloons_prepare_frame(&state, 1, -1, &frame) ==
           PORTABLE_BALLOON_OK);
    assert(frame.activated_count == 0);
}

static void test_source_activation_order_and_negative_coordinates(void)
{
    PortableBalloonState state;
    PortableBalloonViewport viewport = normal_view();
    PortableBalloonFrameResult frame;
    PortableBalloonViewport negative_view = {7, -10, -10, 20, 20};
    portable_balloons_init(&state);
    portable_balloons_simulation_reset(&state, 1);

    /* Submit in a different order; DrawCurBalloons transfer order is fixed. */
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_REST, &viewport,
                                  20, 30, 7) == PORTABLE_BALLOON_OK);
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_QUEEN, &viewport,
                                  21, 30, 7) == PORTABLE_BALLOON_OK);
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_EGG, &viewport,
                                  22, 30, 7) == PORTABLE_BALLOON_OK);
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_FIGHT, &viewport,
                                  23, 30, 7) == PORTABLE_BALLOON_OK);
    assert(portable_balloons_prepare_frame(&state, 1, -1, &frame) ==
           PORTABLE_BALLOON_OK);
    assert(frame.activated_count == 4);
    assert(frame.activation_order[0] == PORTABLE_BALLOON_FIGHT);
    assert(frame.activation_order[1] == PORTABLE_BALLOON_EGG);
    assert(frame.activation_order[2] == PORTABLE_BALLOON_QUEEN);
    assert(frame.activation_order[3] == PORTABLE_BALLOON_REST);
    assert(frame.activated_mask == 0x0f);

    portable_balloons_init(&state);
    portable_balloons_simulation_reset(&state, 1);
    assert(portable_balloon_submit(&state, PORTABLE_BALLOON_FIGHT,
                                  &negative_view, -5, 5, 7) ==
           PORTABLE_BALLOON_OK);
    assert(state.cue[PORTABLE_BALLOON_FIGHT].pending.x == -5);
    assert(portable_balloons_prepare_frame(&state, 1, -1, &frame) ==
           PORTABLE_BALLOON_OK);
    assert(frame.activated_count == 0);
    assert(state.cue[PORTABLE_BALLOON_FIGHT].active == 0);
}

int main(void)
{
    test_visibility_edges_and_word_wrap();
    test_pending_activation_reset_and_dedup();
    test_source_activation_order_and_negative_coordinates();
    puts("balloon cue model tests passed");
    return 0;
}
