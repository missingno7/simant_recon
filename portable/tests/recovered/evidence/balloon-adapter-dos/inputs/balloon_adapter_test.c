#include "../../game/recovered/balloon_adapter.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void bind_and_run(RecoveredState *state,
                         void (*call)(int16_t, int16_t, int16_t),
                         int16_t x, int16_t y, int16_t plane)
{
    RecoveredBindingFrame frame;
    recovered_bind_begin(&frame, state);
    call(x, y, plane);
    recovered_bind_end(&frame, state);
}

static void test_each_source_cue_mapping(void)
{
    RecoveredState state;
    PortableBalloonViewport view = {2, 10, 20, 32, 24};
    recovered_state_init(&state);
    state.MapPlane = view.plane;
    state.fd_50F6_0508[0] = view.left;
    state.fd_50F6_0508[1] = view.top;
    state.fd_50F6_10E0 = view.columns;
    state.fd_50F6_10DE = view.rows;
    state.fd_50F6_0EF6 = 0;
    state.fd_50F6_08DE.x = 1;
    state.fd_50F6_08DE.y = 2;
    state.fd_50F6_0AD8 = 1;
    state.fd_50F6_0852.v = -1;
    state.fd_50F6_0852.h = -1;
    state.fd_50F6_0ACA = -8;
    state.fd_50F6_0F06 = 0;
    state.fd_50F6_09F2.x = 1;
    state.fd_50F6_09F2.y = 2;
    state.fd_50F6_0B06 = 1;
    state.fd_50F6_08EC.v = -1;
    state.fd_50F6_08EC.h = -1;
    state.fd_50F6_0AEA = -8;
    state.fd_50F6_0F10 = 0;
    state.fd_50F6_0A8A.x = 1;
    state.fd_50F6_0A8A.y = 2;
    state.fd_50F6_0C3A = 1;
    state.fd_50F6_0A02.v = -1;
    state.fd_50F6_0A02.h = -1;
    state.fd_50F6_0B08 = -8;
    state.fd_50F6_0F2E = 0;
    state.fd_50F6_0AB2.x = 1;
    state.fd_50F6_0AB2.y = 2;
    state.fd_50F6_0D9A = 1;
    state.fd_50F6_0AA2.v = -1;
    state.fd_50F6_0AA2.h = -1;
    state.fd_50F6_0D68 = -8;

    bind_and_run(&state, sim_recovered_egg_balloons, 11, 23, 2);
    assert(state.fd_50F6_0852.v == 11 && state.fd_50F6_0852.h == 23 &&
           state.fd_50F6_0ACA == 2);
    bind_and_run(&state, sim_recovered_fight_balloons, 12, 24, 2);
    assert(state.fd_50F6_08EC.v == 12 && state.fd_50F6_08EC.h == 24 &&
           state.fd_50F6_0AEA == 2);
    bind_and_run(&state, sim_recovered_queen_balloons, 13, 25, 2);
    assert(state.fd_50F6_0A02.v == 13 && state.fd_50F6_0A02.h == 25 &&
           state.fd_50F6_0B08 == 2);
    bind_and_run(&state, sim_recovered_rest_balloons, 14, 26, 2);
    assert(state.fd_50F6_0AA2.v == 14 && state.fd_50F6_0AA2.h == 26 &&
           state.fd_50F6_0D68 == 2);

    /* The four operations preserve each other’s state and all prior display
     * tuples, proving that no adapter shadow survives the TLS binding. */
    assert(state.fd_50F6_0EF6 == 0 && state.fd_50F6_0F06 == 0 &&
           state.fd_50F6_0F10 == 0 && state.fd_50F6_0F2E == 0);
    assert(state.fd_50F6_08DE.x == 1 && state.fd_50F6_08DE.y == 2 &&
           state.fd_50F6_0AD8 == 1);
    assert(state.fd_50F6_09F2.x == 1 && state.fd_50F6_09F2.y == 2 &&
           state.fd_50F6_0B06 == 1);
    assert(state.fd_50F6_0A8A.x == 1 && state.fd_50F6_0A8A.y == 2 &&
           state.fd_50F6_0C3A == 1);
    assert(state.fd_50F6_0AB2.x == 1 && state.fd_50F6_0AB2.y == 2 &&
           state.fd_50F6_0D9A == 1);
}

static void test_guards_visibility_and_prior_point_dedup(void)
{
    RecoveredState state;
    recovered_state_init(&state);
    state.MapPlane = 1;
    state.fd_50F6_0508[0] = 10;
    state.fd_50F6_0508[1] = 20;
    state.fd_50F6_10E0 = 30;
    state.fd_50F6_10DE = 20;
    state.fd_50F6_0EF6 = 0;
    state.fd_50F6_08DE.x = 12;
    state.fd_50F6_08DE.y = 26;
    state.fd_50F6_0AD8 = 1;
    state.fd_50F6_0852.v = 4;
    state.fd_50F6_0852.h = 5;
    state.fd_50F6_0ACA = 9;

    /* Matching the preserved display tuple reactivates immediately. */
    bind_and_run(&state, sim_recovered_egg_balloons, 12, 26, 1);
    assert(state.fd_50F6_0EF6 == 1);
    assert(state.fd_50F6_0852.v == 4 && state.fd_50F6_0852.h == 5 &&
           state.fd_50F6_0ACA == 9);

    /* Active guard, plane mismatch, and viewport misses preserve state. */
    state.fd_50F6_0EF6 = 3;
    bind_and_run(&state, sim_recovered_egg_balloons, 20, 26, 1);
    assert(state.fd_50F6_0EF6 == 3 && state.fd_50F6_0852.v == 4);
    state.fd_50F6_0EF6 = 0;
    bind_and_run(&state, sim_recovered_egg_balloons, 20, 26, 2);
    bind_and_run(&state, sim_recovered_egg_balloons, 40, 26, 1);
    bind_and_run(&state, sim_recovered_egg_balloons, 20, 22, 1);
    assert(state.fd_50F6_0EF6 == 0 && state.fd_50F6_0852.v == 4 &&
           state.fd_50F6_0852.h == 5 && state.fd_50F6_0ACA == 9);

    /* A visible nonmatching cue replaces pending x/y/plane. */
    bind_and_run(&state, sim_recovered_egg_balloons, 20, 26, 1);
    assert(state.fd_50F6_0852.v == 20 && state.fd_50F6_0852.h == 26 &&
           state.fd_50F6_0ACA == 1);
}

static void test_mode_one_reset_preserves_display_tuples(void)
{
    RecoveredState state;
    RecoveredBindingFrame frame;
    recovered_state_init(&state);
    state.fd_50F6_0EF6 = 1;
    state.fd_50F6_0F06 = 1;
    state.fd_50F6_0F10 = 1;
    state.fd_50F6_0F2E = 1;
    state.fd_50F6_0852.v = 11; state.fd_50F6_0852.h = 12;
    state.fd_50F6_0ACA = 3;
    state.fd_50F6_08EC.v = 21; state.fd_50F6_08EC.h = 22;
    state.fd_50F6_0AEA = 4;
    state.fd_50F6_0A02.v = 31; state.fd_50F6_0A02.h = 32;
    state.fd_50F6_0B08 = 5;
    state.fd_50F6_0AA2.v = 41; state.fd_50F6_0AA2.h = 42;
    state.fd_50F6_0D68 = 6;
    state.fd_50F6_08DE.x = 51; state.fd_50F6_08DE.y = 52;
    state.fd_50F6_0AD8 = 7;
    state.fd_50F6_09F2.x = 61; state.fd_50F6_09F2.y = 62;
    state.fd_50F6_0B06 = 8;
    state.fd_50F6_0A8A.x = 71; state.fd_50F6_0A8A.y = 72;
    state.fd_50F6_0C3A = 9;
    state.fd_50F6_0AB2.x = 81; state.fd_50F6_0AB2.y = 82;
    state.fd_50F6_0D9A = 10;

    recovered_bind_begin(&frame, &state);
    sim_recovered_balloons_simulation_reset(0);
    recovered_bind_end(&frame, &state);
    assert(state.fd_50F6_0EF6 == 1 && state.fd_50F6_0F06 == 1 &&
           state.fd_50F6_0F10 == 1 && state.fd_50F6_0F2E == 1);

    recovered_bind_begin(&frame, &state);
    sim_recovered_balloons_simulation_reset(1);
    recovered_bind_end(&frame, &state);
    assert(state.fd_50F6_0EF6 == 0 && state.fd_50F6_0F06 == 0 &&
           state.fd_50F6_0F10 == 0 && state.fd_50F6_0F2E == 0);
    assert(state.fd_50F6_0852.v == -1 && state.fd_50F6_0852.h == -1 &&
           state.fd_50F6_0ACA == 3);
    assert(state.fd_50F6_08EC.v == -1 && state.fd_50F6_08EC.h == -1 &&
           state.fd_50F6_0AEA == 4);
    assert(state.fd_50F6_0A02.v == -1 && state.fd_50F6_0A02.h == -1 &&
           state.fd_50F6_0B08 == 5);
    assert(state.fd_50F6_0AA2.v == -1 && state.fd_50F6_0AA2.h == -1 &&
           state.fd_50F6_0D68 == 6);
    assert(state.fd_50F6_08DE.x == 51 && state.fd_50F6_08DE.y == 52 &&
           state.fd_50F6_0AD8 == 7);
    assert(state.fd_50F6_09F2.x == 61 && state.fd_50F6_09F2.y == 62 &&
           state.fd_50F6_0B06 == 8);
    assert(state.fd_50F6_0A8A.x == 71 && state.fd_50F6_0A8A.y == 72 &&
           state.fd_50F6_0C3A == 9);
    assert(state.fd_50F6_0AB2.x == 81 && state.fd_50F6_0AB2.y == 82 &&
           state.fd_50F6_0D9A == 10);
}

int main(void)
{
    test_each_source_cue_mapping();
    test_guards_visibility_and_prior_point_dedup();
    test_mode_one_reset_preserves_display_tuples();
    puts("recovered balloon adapter tests passed");
    return 0;
}
