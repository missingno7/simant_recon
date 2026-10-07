#ifndef SIMANT_SDL3_WHOLE_AUDIO_H
#define SIMANT_SDL3_WHOLE_AUDIO_H
#include "audio.h"
#include "../../whole_program/platform/whole_audio_provider.h"
typedef enum PortableSdl3WholeAudioStatus {
    PORTABLE_SDL3_WHOLE_AUDIO_OK=0,
    PORTABLE_SDL3_WHOLE_AUDIO_INVALID_ARGUMENT,
    PORTABLE_SDL3_WHOLE_AUDIO_SDL_ERROR,
    PORTABLE_SDL3_WHOLE_AUDIO_PROVIDER_ERROR
} PortableSdl3WholeAudioStatus;
typedef void (*PortableSdl3SourceTimerObserver)(void *,uint16_t,uint16_t);
typedef struct PortableSdl3WholeAudio {
    PortableSdl3Audio output;
    PortableWholeAudioProvider provider;
    uint64_t clock_origin_ns, bus_ns;
    PortableSdl3SourceTimerObserver source_timer_observer;
    void *source_timer_observer_context;
    int active;
} PortableSdl3WholeAudio;
int portable_sdl3_whole_audio_open(PortableSdl3WholeAudio *audio);
void portable_sdl3_whole_audio_close(PortableSdl3WholeAudio *audio);
PortableSdl3WholeAudioStatus portable_sdl3_whole_audio_pump(PortableSdl3WholeAudio *audio);
void portable_sdl3_whole_audio_set_source_timer_observer(PortableSdl3WholeAudio *audio,PortableSdl3SourceTimerObserver observer,void *context);
#endif
