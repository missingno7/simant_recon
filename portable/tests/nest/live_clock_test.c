#include "../../game/simulation/nest.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, \
                #condition); \
        exit(1); \
    } \
} while (0)

typedef struct TestClock {
    int32_t now;
    unsigned calls;
    unsigned fail_on_call;
    unsigned advance_after_first_tick;
    unsigned saw_first_tick;
} TestClock;

static int test_tick_count(void *context, int32_t *value)
{
    TestClock *clock = context;
    ++clock->calls;
    if (clock->calls == clock->fail_on_call)
        return 0;
    *value = clock->now;
    return 1;
}

static int advance_clock_after_tick(void *context, const SimNestEvent *event)
{
    TestClock *clock = context;
    if (event->kind == SIM_NEST_TICK) {
        if (!clock->saw_first_tick) {
            clock->saw_first_tick = 1;
            if (clock->advance_after_first_tick)
                clock->now += 5;
        }
    }
    return 1;
}

static void setup_world(SimGameWorld *world, SimNestRuntime *runtime,
                        SimRng *rng)
{
    memset(world, 0, sizeof(*world));
    memset(runtime, 0, sizeof(*runtime));
    memset(rng, 0, sizeof(*rng));
    world->current_ant_plane = 1;
    world->me_x = 10;
    world->me_y = 10;
    world->me_type = 0x20;
    world->me_direction = 0;
    runtime->theme_last_tick = 0;
}

static void test_second_sample_observes_callback_clock_advance(void)
{
    SimGameWorld world;
    SimNestRuntime runtime;
    SimNestRequest empty_request = {{0, 0}, 0};
    SimNestTrace trace;
    SimRng rng;
    TestClock clock = {7200, 0, 0, 1, 0};
    SimNestStatus status;
    unsigned i;
    int32_t sampled[2] = {0, 0};
    unsigned sampled_count = 0;

    setup_world(&world, &runtime, &rng);
    status = sim_enter_nest_with_tick_provider(
        &world, &rng, &runtime, &empty_request, &trace,
        advance_clock_after_tick, &clock, test_tick_count, &clock);
    assert(status == SIM_NEST_OK);
    assert(clock.calls == 2);
    assert(clock.saw_first_tick == 1);
    assert(runtime.theme_last_tick == 7205);
    for (i = 0; i < trace.count; ++i) {
        if (trace.events[i].kind == SIM_NEST_TICK && sampled_count < 2)
            sampled[sampled_count++] = trace.events[i].arguments[0];
    }
    assert(sampled_count == 2);
    assert(sampled[0] == 7200 && sampled[1] == 7205);
}

static void test_provider_failure_stops_before_theme_commit(void)
{
    SimGameWorld world;
    SimNestRuntime runtime;
    SimNestRequest empty_request = {{0, 0}, 0};
    SimNestTrace trace;
    SimRng rng;
    TestClock clock = {7200, 0, 2, 1, 0};
    SimNestStatus status;

    setup_world(&world, &runtime, &rng);
    status = sim_enter_nest_with_tick_provider(
        &world, &rng, &runtime, &empty_request, &trace,
        advance_clock_after_tick, &clock, test_tick_count, &clock);
    assert(status == SIM_NEST_TICK_PROVIDER_FAILED);
    assert(clock.calls == 2);
    assert(runtime.theme_index == 0);
    assert(runtime.theme_last_tick == 0);
}

static void test_nonexpired_theme_reads_clock_only_once(void)
{
    SimGameWorld world;
    SimNestRuntime runtime;
    SimNestRequest empty_request = {{0, 0}, 0};
    SimNestTrace trace;
    SimRng rng;
    TestClock clock = {7199, 0, 0, 0, 0};
    SimNestStatus status;

    setup_world(&world, &runtime, &rng);
    status = sim_enter_nest_with_tick_provider(
        &world, &rng, &runtime, &empty_request, &trace,
        NULL, NULL, test_tick_count, &clock);
    assert(status == SIM_NEST_OK);
    assert(clock.calls == 1);
    assert(runtime.theme_index == 0);
    assert(runtime.theme_last_tick == 0);
}

int main(void)
{
    test_second_sample_observes_callback_clock_advance();
    test_provider_failure_stops_before_theme_commit();
    test_nonexpired_theme_reads_clock_only_once();
    puts("nest live TickCount provider: source-order cases pass");
    return 0;
}
