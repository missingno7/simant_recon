#ifndef SIMANT_PORTABLE_PLATFORM_SDL3_WHOLE_AUDIO_PROVIDER_H
#define SIMANT_PORTABLE_PLATFORM_SDL3_WHOLE_AUDIO_PROVIDER_H

#include "audio.h"
#include "../../whole_program/platform/audio_events.h"
#include "../../whole_program/platform/whole_audio_provider.h"

typedef enum PortableSdl3WholeAudioStatus {
    PORTABLE_SDL3_WHOLE_AUDIO_OK = 0,
    PORTABLE_SDL3_WHOLE_AUDIO_INVALID_ARGUMENT,
    PORTABLE_SDL3_WHOLE_AUDIO_SDL_ERROR,
    PORTABLE_SDL3_WHOLE_AUDIO_PROVIDER_ERROR,
    PORTABLE_SDL3_WHOLE_AUDIO_UNSUPPORTED_BACKEND
} PortableSdl3WholeAudioStatus;

typedef enum PortableSdl3WholeAudioBackend {
    PORTABLE_SDL3_WHOLE_AUDIO_MODE1_SAMPLED_DAC = 1
} PortableSdl3WholeAudioBackend;

typedef void (*PortableSdl3SourceTimerObserver)(void *context,
                                                uint16_t pit_divisor,
                                                uint16_t chain_reload);

typedef struct PortableSdl3WholeAudio {
    PortableSdl3Audio output;
    PortableWholeAudioProvider provider;
    PortableWholeAudioEventQueue *events; /* Borrowed, bound while open. */
    uint64_t clock_origin_ns;
    PortableSdl3SourceTimerObserver source_timer_observer;
    void *source_timer_observer_context;
    uint16_t source_pit_divisor;
    uint16_t source_chain_reload;
    int source_timer_active;
    int active;
} PortableSdl3WholeAudio;

/* The caller explicitly selects the source mode-1 sampled-DAC path. There is
 * no automatic DOS device detection and no MIDI/OPL/port emulation here.
 * The event queue must be initialized and not already bound.
 */
int portable_sdl3_whole_audio_open(PortableSdl3WholeAudio *audio,
                                   PortableWholeAudioEventQueue *events,
                                   PortableSdl3WholeAudioBackend backend);
/* Bind the generated original f_284A_067F entry to the source m28BC tick
 * divider. The callback runs at the exact mode-1 divider cadence while audio
 * frames are rendered; its source return value reloads the 16-bit counter.
 */
void portable_sdl3_whole_audio_set_sequencer(
    PortableSdl3WholeAudio *audio, int16_t *source_divider,
    int16_t (*tick)(void));
/* Optional game-clock bridge. The source mode-1 attach emits its exact PIT
 * divisor and chained-INT08 reload once; detach emits (0,0). */
void portable_sdl3_whole_audio_set_source_timer_observer(
    PortableSdl3WholeAudio *audio, PortableSdl3SourceTimerObserver observer,
    void *context);
void portable_sdl3_whole_audio_close(PortableSdl3WholeAudio *audio);

/* Keep the SDL stream near target_queued_frames. Each queued U8 frame advances
 * one source mode-1 PIT output step. SDL presents at 5,576 Hz, the nearest
 * integer to the exact source rate 14,318,180/(12*214); event clocks preserve
 * that exact rational independently. Returns an explicit error rather than
 * dropping source events.
 */
PortableSdl3WholeAudioStatus portable_sdl3_whole_audio_pump(
    PortableSdl3WholeAudio *audio, size_t target_queued_frames);

#endif
