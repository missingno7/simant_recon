#include "portable/platform/sdl3/whole_audio_startup.h"
#include "portable/whole_program/platform/audio_native.h"
#include "portable/whole_program/platform/audio.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/sdl3/host_modes.h"
#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);exit(1); } } while(0)
/* Test-owned source boundary fixtures, without game algorithms. */
PortableWholeAudioRuntimeSample fd_55B3_6B4C[4];
uint8_t portable_canonical_volume_tables[2048];
uint16_t fd_55B3_6B9E=0x6ca3;
int16_t fd_55B3_6B42,fd_55B3_6B9C=5,fd_55B3_6BA0=0x22c;
int16_t fd_55B3_74AD=1,fd_55B3_74B5=5;
static unsigned sequencer_calls;
int16_t f_284A_067F(void) { ++sequencer_calls;return 2; }
typedef struct Result { uint64_t frames,time,irq,fraction;unsigned calls;int16_t divider; } Result;
static Result exercise(uint64_t quantum,unsigned polls) {
    PortableSdl3WholeAudio a;Result result;
    host_virtual_clock_configure(quantum);sequencer_calls=0;fd_55B3_6B42=1;
    CHECK(portable_sdl3_whole_audio_open(&a));
    CHECK(portable_sdl3_whole_audio_bind_source_services(&a));
    f_28BC_0488(214,306);f_28BC_03CC();
    SDL_Delay(20);
    CHECK(portable_sdl3_whole_audio_pump(&a)==PORTABLE_SDL3_WHOLE_AUDIO_OK);
    CHECK(a.provider.frame_cursor==0 && sequencer_calls==0);
    for(unsigned n=0;n<polls;++n) {
        host_virtual_clock_poll();
        CHECK(portable_sdl3_whole_audio_pump(&a)==PORTABLE_SDL3_WHOLE_AUDIO_OK);
    }
    CHECK(a.provider.frame_cursor==4800 && a.provider.time_ns==100000000);
    CHECK(SDL_GetAudioStreamQueued(a.output.stream)==0);
    CHECK(sequencer_calls>0);
    dos_audio_host_in8(0x388);uint64_t bus=a.bus_ns;
    CHECK(bus>=100000000);
    SDL_Delay(20);dos_audio_host_in8(0x388);
    CHECK(a.bus_ns==bus+1000 && host_time_ns()==100000000);
    result=(Result){a.provider.frame_cursor,a.provider.time_ns,a.provider.irq_ns,
                    a.provider.irq_fraction,sequencer_calls,fd_55B3_6B42};
    f_28BC_04E0(0);portable_sdl3_whole_audio_unbind_source_services();
    portable_sdl3_whole_audio_close(&a);return result;
}
int main(void) {
    CHECK(SDL_SetHint(SDL_HINT_AUDIO_DRIVER,"dummy"));
    Result small=exercise(1000000,100),large=exercise(100000000,1);
    CHECK(small.frames==large.frames && small.time==large.time && small.irq==large.irq &&
          small.fraction==large.fraction && small.calls==large.calls && small.divider==large.divider);
    printf("PASS: virtual Sound Mode 6 PIT/IRQ and ISA clock, %u sequencer calls; wall delay and pump chunking controls\n",small.calls);
    return 0;
}
