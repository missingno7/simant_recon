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

typedef struct PortableSdl3WholeAudio {
    PortableSdl3Audio output;
    PortableWholeAudioProvider provider;
    PortableWholeAudioEventQueue *events; /* Borrowed, bound while open. */
    uint64_t clock_origin_ns;
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
void portable_sdl3_whole_audio_close(PortableSdl3WholeAudio *audio);

/* Keep the SDL stream near target_queued_frames. Each queued U8 frame is one
 * source mode-1 PIT output sample at 11932 Hz, mapped to the host stream rate
 * by SDL. Returns an explicit error rather than dropping source events.
 */
PortableSdl3WholeAudioStatus portable_sdl3_whole_audio_pump(
    PortableSdl3WholeAudio *audio, size_t target_queued_frames);

#endif
