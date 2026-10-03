#ifndef SIMANT_PORTABLE_PLATFORM_SDL3_WHOLE_AUDIO_STARTUP_H
#define SIMANT_PORTABLE_PLATFORM_SDL3_WHOLE_AUDIO_STARTUP_H

#include "whole_audio_provider.h"
#include "../../whole_program/platform/audio_startup.h"

/* Select and initialize original source mode 1 against the already-open SDL
 * sampled-DAC stream. The source m28BC timer boundary binds the original
 * generated f_284A_067F callback and divider as part of source initialization.
 */
PortableWholeAudioStartupStatus portable_sdl3_whole_audio_start_source(
    PortableSdl3WholeAudio *audio, int16_t requested_source_mode,
    int16_t (*source_initializer)(int16_t mode, int16_t flag),
    int16_t *active_source_mode);

/* Install native host services before the original DOS application entry is
 * called. The original startup remains the only caller of f_277E_0000. */
int portable_sdl3_whole_audio_bind_source_services(
    PortableSdl3WholeAudio *audio);
void portable_sdl3_whole_audio_unbind_source_services(void);

#endif
