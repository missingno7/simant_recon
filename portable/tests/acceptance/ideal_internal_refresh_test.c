#include "portable/whole_program/platform/sdl3/input_time_host.h"
#include "portable/whole_program/platform/sdl3/host_modes.h"
#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x);exit(71);}}while(0)
int native_windows_translate(SDL_Event *e){(void)e;return 0;}
int native_windows_take_deferred(SDL_Event *e){(void)e;return 0;}
int native_windows_filter_root(SDL_Event *e){(void)e;return 0;}
int native_windows_pointer(float *x,float *y){(void)x;(void)y;return 0;}
void native_windows_root_pointer(float *x,float *y){(void)x;(void)y;}
static unsigned calls,isr;
static int guest_if=1;
static int interrupts_enabled(void){return guest_if;}
int portable_whole_audio_isr_active(void){return isr;}
static int refresh(void *ctx,SimTimingClock *clock){(void)ctx;(void)clock;++calls;return 1;}
int main(void){
 SimTimingClock game,bios;PortableInputTimeHost input;HostEvent e={0};
 CHECK(SDL_SetHint(SDL_HINT_VIDEO_DRIVER,"dummy"));
 portable_machine_clock_configure(1,1000000);
 Host *host=host_create_dimensions("internal admission control",1,640,480);CHECK(host);
 CHECK(sim_timing_clock_init_bios(&game,14318180,12)==SIM_TIMING_OK);
 CHECK(sim_timing_clock_init_bios(&bios,14318180,12)==SIM_TIMING_OK);
 CHECK(portable_input_time_host_init_clocks(&input,host,&game,&bios)==PORTABLE_INPUT_TIME_OK);
 CHECK(portable_input_time_host_set_clock_refresh(&input,refresh,NULL)==PORTABLE_INPUT_TIME_OK);
 CHECK(portable_input_time_host_bind(&input)==PORTABLE_INPUT_TIME_OK);
 CHECK(portable_input_time_host_refresh_service(&input,"TickCount")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==1000000 && calls==1);
 ++bios.tick_count; /* a foreground reload chains old INT08 at zero time */
 SDL_Event key={0};key.type=SDL_EVENT_KEY_DOWN;key.key.key=SDLK_A;key.key.scancode=SDL_SCANCODE_A;key.key.down=true;
 CHECK(SDL_PushEvent(&key));
 CHECK(portable_input_time_host_refresh_service(&input,"mouse_show_cursor")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==1000000 && calls==1 && input.key_count==0);
 CHECK(portable_input_time_host_refresh_service(&input,"TickCount")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==2000000 && calls==2 && input.key_count==1);
 isr=1;CHECK(portable_input_time_host_refresh_service(&input,"TickCount")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==2000000 && calls==2);isr=0;
 portable_machine_video_write();
 portable_input_time_host_set_interrupt_guard(&input,interrupts_enabled);
 guest_if=0;
 CHECK(portable_input_time_host_refresh_service(&input,"TickCount")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==2000000 && calls==2);
 guest_if=1;isr=1;
 CHECK(portable_input_time_host_refresh_service(&input,"TickCount")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==2000000 && calls==2);isr=0;
 CHECK(portable_input_time_host_refresh_service(&input,"mouse_show_cursor")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==2000000 && calls==2);
 CHECK(portable_input_time_host_refresh_service(&input,"TickCount")==PORTABLE_INPUT_TIME_OK);
 CHECK(host_time_ns()==16683218 && calls==3);
 (void)e;portable_input_time_host_shutdown(&input);host_destroy(host);
 puts("PASS: internal writes and ISR reads cannot admit input or charge time; next foreground read does");return 0;
}
