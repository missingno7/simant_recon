#include "whole_audio_provider.h"
#include "../../whole_program/platform/sdl3/host_modes.h"
#include <string.h>
#include <SDL3/SDL.h>
/* The existing native alias inventory exports snd_requested_driver_mode as
 * g_610A (the same storage read by converted snd_init_driver_once). */
extern int16_t g_610A, snd_interface_initialized;
int portable_sdl3_whole_audio_open(PortableSdl3WholeAudio *a) {
    memset(a,0,sizeof(*a));
    if(!portable_whole_audio_provider_init(&a->provider)) return 0;
    a->clock_origin_ns=host_time_ns();a->active=1;return 1;
}
void portable_sdl3_whole_audio_close(PortableSdl3WholeAudio *a) {
    portable_sdl3_audio_close(&a->output);portable_whole_audio_provider_close(&a->provider);
    memset(a,0,sizeof(*a));
}
PortableSdl3WholeAudioStatus portable_sdl3_whole_audio_pump(PortableSdl3WholeAudio *a) {
    int16_t samples[1024*2];
    if(!a || !a->active) return PORTABLE_SDL3_WHOLE_AUDIO_INVALID_ARGUMENT;
    ++a->pump_calls;
    if(a->provider.in_render) return PORTABLE_SDL3_WHOLE_AUDIO_OK;
    uint64_t ns=host_time_ns()-a->clock_origin_ns;
    uint64_t frames=(ns/1000000000)*48000+(ns%1000000000)*48000/1000000000;
    /* Logical IRQ work always runs, independently of physical playback. No FM
     * core, PCM generation or device is needed by deterministic/headless runs.
     * Read-only source playback observations do not need a renderer either. */
    int audible=!host_virtual_clock_enabled() &&
        (g_610A || snd_interface_initialized || a->provider.armed) &&
        (!SDL_GetCurrentVideoDriver() || strcmp(SDL_GetCurrentVideoDriver(),"dummy"));
    if(!audible) {
        ++a->silent_advances;
        a->provider.frame_cursor=frames;
        portable_whole_audio_provider_set_rendering(&a->provider,0);
        portable_whole_audio_provider_advance(&a->provider,ns);
        return PORTABLE_SDL3_WHOLE_AUDIO_OK;
    }
    if(!a->output.stream && !portable_sdl3_audio_open(&a->output,48000)) return PORTABLE_SDL3_WHOLE_AUDIO_SDL_ERROR;
    portable_whole_audio_provider_set_rendering(&a->provider,1);
    /* All decisions precede block rendering. Neither queue fill nor the SDL
     * consumer can run source callbacks or move the machine clock. */
    portable_whole_audio_provider_advance(&a->provider,ns);
    while(a->provider.frame_cursor<frames) {
        size_t count=(size_t)(frames-a->provider.frame_cursor);
        if(count>1024) count=1024;
        portable_whole_audio_provider_render(&a->provider,samples,count,a->provider.frame_cursor+1);
        a->provider.frame_cursor+=count;
        a->rendered_frames+=count;
        if(!portable_sdl3_audio_queue_frames(&a->output,samples,count)) return PORTABLE_SDL3_WHOLE_AUDIO_SDL_ERROR;
    }
    /* IRQs between the last PCM frame and the service endpoint belong to this
     * transaction too. PCM consumption never decides timer delivery. */
    return PORTABLE_SDL3_WHOLE_AUDIO_OK;
}
void portable_sdl3_whole_audio_set_source_timer_observer(PortableSdl3WholeAudio *a,PortableSdl3SourceTimerObserver o,void *c) {
    a->source_timer_observer=o;a->source_timer_observer_context=c;
    a->provider.timer_observer=o;a->provider.timer_observer_context=c;
}
