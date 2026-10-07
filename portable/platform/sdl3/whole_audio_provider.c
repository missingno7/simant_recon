#include "whole_audio_provider.h"
#include "../../whole_program/platform/sdl3/host_modes.h"
#include <string.h>
int portable_sdl3_whole_audio_open(PortableSdl3WholeAudio *a) {
    memset(a,0,sizeof(*a));
    if(!portable_whole_audio_provider_init(&a->provider)) return 0;
    if(!portable_sdl3_audio_open(&a->output,48000)) {
        portable_whole_audio_provider_close(&a->provider);return 0;
    }
    a->clock_origin_ns=host_time_ns();a->active=1;return 1;
}
void portable_sdl3_whole_audio_close(PortableSdl3WholeAudio *a) {
    portable_sdl3_audio_close(&a->output);portable_whole_audio_provider_close(&a->provider);
    memset(a,0,sizeof(*a));
}
PortableSdl3WholeAudioStatus portable_sdl3_whole_audio_pump(PortableSdl3WholeAudio *a) {
    int16_t samples[1024*2];
    if(!a || !a->active) return PORTABLE_SDL3_WHOLE_AUDIO_INVALID_ARGUMENT;
    if(a->provider.in_render) return PORTABLE_SDL3_WHOLE_AUDIO_OK;
    uint64_t ns=host_time_ns()-a->clock_origin_ns;
    uint64_t frames=(ns/1000000000)*48000+(ns%1000000000)*48000/1000000000;
    /* Never run canonical IRQ callbacks ahead to fill an SDL queue. Virtual
     * mode performs the same elapsed PIT/IRQ work and discards presentation
     * PCM: asynchronous device consumption cannot clock the source state. */
    while(a->provider.frame_cursor<frames) {
        size_t count=(size_t)(frames-a->provider.frame_cursor);
        if(count>1024) count=1024;
        for(size_t i=0;i<count;++i) portable_whole_audio_provider_render_frame(&a->provider,&samples[2*i]);
        if(!host_virtual_clock_enabled() && !portable_sdl3_audio_queue_frames(&a->output,samples,count)) return PORTABLE_SDL3_WHOLE_AUDIO_SDL_ERROR;
    }
    return PORTABLE_SDL3_WHOLE_AUDIO_OK;
}
void portable_sdl3_whole_audio_set_source_timer_observer(PortableSdl3WholeAudio *a,PortableSdl3SourceTimerObserver o,void *c) {
    a->source_timer_observer=o;a->source_timer_observer_context=c;
}
