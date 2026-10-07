#include "../sdl3/host_modes.h"
#include "../pit_clock.h"
#include <SDL3/SDL.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#undef assert
#define assert(e) do { if (!(e)) { fprintf(stderr,"check failed at %d: %s\n",__LINE__,#e); exit(1); } } while(0)

static void await_event(Host *host, HostEventKind kind, HostEvent *observed)
{
    unsigned attempts;
    for(attempts=0;attempts<100;attempts++) {
        int result=host_poll_event(host,observed);
        assert(result>=0);
        if(result>0 && observed->kind==kind) return;
    }
    assert(0 && "scripted SDL event missing");
}

int main(void)
{
    HostDosDateTime date;
    SimTimingClock game, bios, bulk;
    Host *host;
    HostEvent event = {0}, observed;
    HostInputState state;
    unsigned i;
    uint64_t prior;
    host_virtual_clock_configure(0);
    assert(!host_virtual_clock_enabled());
    assert(!host_virtual_dos_datetime(&date));
    host_virtual_clock_configure(1000000);
    assert(host_time_ns() == 0);
    assert(host_virtual_dos_datetime(&date));
    assert(date.year==1992 && date.month==1 && date.day==1 && date.weekday==3);
    assert(date.hour==12 && date.minute==0 && date.second==0 && date.hundredth==0);
    assert(!host_virtual_dos_datetime(NULL));
    for (i=0;i<100000;i++) assert(host_time_ns()==0); /* Reads/computation cost no time. */
    assert(SDL_SetHintWithPriority(SDL_HINT_VIDEO_DRIVER,"dummy",SDL_HINT_OVERRIDE));
    SDL_Delay(20);
    host_wait_ms(20);
    assert(host_time_ns()==0); /* Wall scheduling and sleeps cannot move replay time. */
    assert(sim_timing_clock_init_bios(&game,14318180,12)==SIM_TIMING_OK);
    assert(sim_timing_clock_init_bios(&bios,14318180,12)==SIM_TIMING_OK);
    assert(sim_timing_clock_init_bios(&bulk,14318180,12)==SIM_TIMING_OK);
    for (i=0;i<1000;i++) {
        prior=host_time_ns(); host_virtual_clock_poll();
        assert(sim_timing_advance_nanoseconds(&game,host_time_ns()-prior)==SIM_TIMING_OK);
        assert(sim_timing_advance_nanoseconds(&bios,host_time_ns()-prior)==SIM_TIMING_OK);
    }
    assert(host_time_ns()==1000000000 && host_virtual_dos_elapsed_ms()==1000);
    assert(sim_timing_advance_nanoseconds(&bulk,host_time_ns())==SIM_TIMING_OK);
    assert(game.tick_count==18 && game.tick_count==bulk.tick_count);
    assert(game.pit_fraction==bulk.pit_fraction && game.ns_fraction==bulk.ns_fraction);
    sim_timing_set_tick_count_enabled(&game,0);
    assert(sim_timing_advance_nanoseconds(&game,1000000000)==SIM_TIMING_OK);
    assert(sim_timing_advance_nanoseconds(&bios,1000000000)==SIM_TIMING_OK);
    assert(game.tick_count==18 && bios.tick_count==36); /* Modal freeze doesn't freeze BIOS. */
    assert(sim_timing_clock_init_audio(&game,14318180,12)==SIM_TIMING_OK);
    assert(game.pit_divisor_counts==0xd6 && game.interrupts_per_tick==0x132);
    assert(sim_timing_advance_nanoseconds(&game,1000000000)==SIM_TIMING_OK);
    assert(game.tick_count==18); /* Audio's source-derived chained PIT rate. */
    assert(sim_timing_clock_init_bios(&game,14318180,12)==SIM_TIMING_OK);
    for(i=0;game.tick_count*3<7;i++)
        assert(sim_timing_advance_nanoseconds(&game,1000000)==SIM_TIMING_OK);
    assert(i==165); /* MacTickCount = TickCount * 3: Normal waits seven Mac ticks. */
    assert(sim_timing_clock_init_bios(&game,14318180,12)==SIM_TIMING_OK);
    for(i=0;game.tick_count*3<21;i++)
        assert(sim_timing_advance_nanoseconds(&game,1000000)==SIM_TIMING_OK);
    assert(i==385); /* Slow waits 21 Mac ticks, seven PIT ticks from phase zero. */
    host_virtual_clock_configure(UINT64_C(59)*86400000000000);
    host_virtual_clock_poll();
    assert(host_virtual_dos_datetime(&date));
    assert(date.year==1992 && date.month==2 && date.day==29 && date.hour==12);
    host_virtual_clock_configure(UINT64_C(60)*86400000000000);
    host_virtual_clock_poll();
    assert(host_virtual_dos_datetime(&date) && date.month==3 && date.day==1);
    host_virtual_clock_configure(UINT64_C(425)*86400000000000);
    host_virtual_clock_poll();
    assert(host_virtual_dos_datetime(&date) && date.year==1993 && date.month==3 && date.day==1);
    host_virtual_clock_configure(1000000);
    host=host_create_dimensions("virtual clock control",1,640,480);
    assert(host);
    while(host_poll_event(host,&observed)>0) {}
    assert(host_warp_pointer(host,240,320));
    assert(host_get_input_state(host,&state) && state.x==240 && state.y==320);
    event.kind=HOST_EVENT_MOUSE_DOWN; event.button=SDL_BUTTON_LEFT; event.x=100;event.y=200;
    assert(host_push_pointer_event(host,&event));
    await_event(host,HOST_EVENT_MOUSE_DOWN,&observed);
    assert(host_get_input_state(host,&state) && state.x==100 && state.y==200 && state.left_button_down);
    event.kind=HOST_EVENT_MOUSE_UP;
    assert(host_push_pointer_event(host,&event));
    await_event(host,HOST_EVENT_MOUSE_UP,&observed);
    assert(host_get_input_state(host,&state) && !state.left_button_down);
    assert(host_time_ns()==0); /* Event ingestion and warps aren't extra clock polls. */
    host_destroy(host);
    puts("virtual clock, PIT, civil date, wall-delay and pointer controls passed");
    return 0;
}
