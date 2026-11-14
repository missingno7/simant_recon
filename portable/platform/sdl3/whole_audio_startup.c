#include "whole_audio_startup.h"
#include "../../whole_program/platform/audio_native.h"
#include "../../audio/isa_devices.h"
#include "../../whole_program/platform/sdl3/host_modes.h"
#include <stdio.h>
#include <stdlib.h>
static uint64_t bus_time(PortableSdl3WholeAudio *a) {
    if(!a->provider.in_render && portable_sdl3_whole_audio_pump(a)!=PORTABLE_SDL3_WHOLE_AUDIO_OK) {
        fprintf(stderr,"Audio synchronization failed\n");exit(72);
    }
    uint64_t now=a->provider.in_render ? a->provider.time_ns : host_time_ns()-a->clock_origin_ns;
    /* ideal-v1: I/O is synchronous at the current machine instant. Polling a
     * ready direct-DAC device cannot create a second, provider-local clock. */
    a->bus_ns=now;
    return now;
}
static void out8(void *context,uint16_t port,uint8_t value) {
    PortableSdl3WholeAudio *a=context;
    uint64_t now=bus_time(a);sim_isa_audio_out(a->provider.devices,port,value,now);
}
static uint8_t in8(void *context,uint16_t port) {
    PortableSdl3WholeAudio *a=context;
    uint64_t now=bus_time(a);uint8_t v=sim_isa_audio_in(a->provider.devices,port,now);
    return v;
}
static void configure(void *context,uint16_t divisor,uint16_t chain,unsigned channels) {
    PortableSdl3WholeAudio *a=context;
    portable_whole_audio_provider_configure(&a->provider,divisor,chain,channels);
}
static void start(void *context) {
    PortableSdl3WholeAudio *a=context;
    if(!a->provider.in_render) bus_time(a);
    portable_whole_audio_provider_start(&a->provider);
}
static void stop(void *context) {
    PortableSdl3WholeAudio *a=context;
    portable_whole_audio_provider_stop(&a->provider);
}
static void enable_interrupts(void *context) {
    PortableSdl3WholeAudio *a=context;
    portable_whole_audio_provider_enable_interrupts(&a->provider);
}
int portable_sdl3_whole_audio_bind_source_services(PortableSdl3WholeAudio *a) {
    PortableWholeAudioHost host={a,configure,start,stop,out8,in8,enable_interrupts};
    const char *trace=getenv("SIMANT_AUDIO_TRACE");
    if(trace && !sim_isa_audio_trace(a->provider.devices,trace)) return 0;
    return portable_whole_audio_bind(&host);
}
void portable_sdl3_whole_audio_unbind_source_services(void) { portable_whole_audio_unbind(); }
