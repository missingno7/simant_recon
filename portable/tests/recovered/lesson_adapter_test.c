#include "../../game/recovered/lesson_adapter.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct HostState {
    int32_t mac_ticks;
    int16_t front_window;
    int16_t front_result;
    int16_t alarm_state;
    int16_t alarm_quiet;
    unsigned clock_calls;
    unsigned front_calls;
    unsigned alarm_calls;
} HostState;

static int32_t get_mac_ticks(void *context)
{
    HostState *host=(HostState *)context;
    host->clock_calls++;
    return host->mac_ticks;
}

static int16_t is_window_front(void *context,int16_t window_id)
{
    HostState *host=(HostState *)context;
    host->front_calls++;
    host->front_window=window_id;
    return host->front_result;
}

static void set_alarm_drop(void *context,int16_t state,int16_t quiet)
{
    HostState *host=(HostState *)context;
    host->alarm_calls++;
    host->alarm_state=state;
    host->alarm_quiet=quiet;
}

static int done_for(SimGameWorld *world,SimTickState *tick,SimNestRuntime *nest,
                    SimLessonState *lesson_state,const SimLessonServices *services,
                    int16_t lesson)
{
    int16_t done=-1;
    assert(sim_lesson_done(world,tick,nest,lesson_state,services,lesson,&done)==SIM_LESSON_OK);
    return done;
}

int main(void)
{
    SimGameWorld world={0};
    SimTickState tick={0};
    SimNestRuntime nest={0};
    SimLessonState lesson_state={0};
    HostState host={0};
    SimLessonServices services={get_mac_ticks,is_window_front,set_alarm_drop,&host};
    SimLessonServices no_services={0};
    int16_t done;

    assert(done_for(&world,&tick,&nest,&lesson_state,&services,1)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,57)==0);

    world.source_state_0204=10;
    nest.dug_b_count=10;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,3)==1);
    lesson_state.fd_50F6_0AA0=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,3)==0);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,4)==0);
    lesson_state.fd_50F6_0AA0=0;
    nest.dug_b_count=11;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,4)==1);

    world.current_ant_plane=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,5)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,20)==1);
    world.me_x=4; world.me_y=5;
    lesson_state.fd_50F6_1074=10;
    lesson_state.fd_50F6_0B1E=0;
    world.source_state_0204=10;
    host.mac_ticks=11;
    host.clock_calls=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,7)==1);
    assert(host.clock_calls==1);
    lesson_state.fd_50F6_1074=9;
    host.clock_calls=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,7)==0);
    assert(host.clock_calls==0);
    lesson_state.fd_50F6_1074=10;
    lesson_state.fd_50F6_0B1E=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,26)==0);
    assert(host.clock_calls==0);

    world.map_view_x=3; world.map_view_y=4;
    lesson_state.fd_50F6_1074=8;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,9)==1);
    lesson_state.fd_50F6_1074=7;
    host.clock_calls=0;
    host.mac_ticks=10;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,9)==0);
    assert(host.clock_calls==1);

    host.front_result=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,10)==1);
    assert(host.front_window==0x0100);
    host.front_result=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,10)==0);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,12)==0);
    assert(host.front_window==0);
    host.front_result=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,32)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,42)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,39)==1);
    assert(host.front_window==0x1200);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,47)==1);
    assert(host.front_window==0x1300);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,49)==1);
    assert(host.front_window==0);
    assert(sim_lesson_done(&world,&tick,&nest,&lesson_state,&no_services,
                           39,&done)==SIM_LESSON_SERVICE_UNAVAILABLE);

    world.me_x=5; world.me_y=6;
    world.current_ant_plane=1;
    world.tiles.surface[5][6]=0x48;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,13)==1);
    world.tiles.surface[5][6]=0x47;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,13)==0);
    world.me_x=-1;
    assert(sim_lesson_done(&world,&tick,&nest,&lesson_state,&services,13,&done)==
           SIM_LESSON_MAP_COORDINATE_UNAVAILABLE);
    world.current_ant_plane=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,13)==0);

    world.me_health=0x5a;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,14)==0);
    world.me_health=0x5b;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,14)==1);
    world.me_type=0x18;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,16)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,22)==0);
    world.me_type=0x10;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,19)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,22)==1);
    world.me_type=0x28;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,21)==1);

    tick.history_black[5]=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,24)==0);
    tick.history_black[5]=2;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,24)==1);
    tick.history_black[5]=0x28;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,52)==0);
    tick.history_black[5]=0x29;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,52)==1);

    world.me_x=4; world.me_y=5;
    lesson_state.fd_50F6_1074=10;
    lesson_state.fd_50F6_0B1E=0;
    nest.alarm_drop_state=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,27)==1);
    lesson_state.fd_50F6_1074=9;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,27)==0);
    lesson_state.fd_50F6_1074=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,30)==0);
    assert(host.alarm_calls==1 && host.alarm_state==0 && host.alarm_quiet==1);
    assert(sim_lesson_done(&world,&tick,&nest,&lesson_state,&no_services,
                           30,&done)==SIM_LESSON_SERVICE_UNAVAILABLE);
    nest.alarm_drop_state=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,30)==0);

    world.map_plane=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,33)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,38)==0);
    world.map_plane=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,38)==1);
    lesson_state.fd_50F6_035C=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,36)==1);
    lesson_state.fd_50F6_035C=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,36)==0);

    lesson_state.fd_50F6_1074=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,8)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,43)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,46)==1);
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,50)==1);
    lesson_state.fd_50F6_1074=0;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,8)==0);

    lesson_state.modeLevels[0]=0x7fff;
    lesson_state.modeLevels[1]=1;
    lesson_state.fd_50F6_1074=(int16_t)-0x8000;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,41)==0);
    world.current_ant_plane=3;
    lesson_state.fd_50F6_1074=99;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,54)==1);
    assert(lesson_state.fd_50F6_1074==0);
    world.current_ant_plane=2;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,54)==1);
    assert(lesson_state.fd_50F6_1074==1);
    world.current_ant_plane=1;
    assert(done_for(&world,&tick,&nest,&lesson_state,&services,54)==0);
    assert(lesson_state.fd_50F6_1074==1);

    assert(sim_lesson_done(NULL,&tick,&nest,&lesson_state,&services,1,&done)==
           SIM_LESSON_INVALID_ARGUMENT);
    puts("LessonDone source adapter directed state/clock/window/alarm cases passed");
    return 0;
}
