#include "audio_startup.h"

PortableWholeAudioStartupStatus portable_whole_audio_startup_initialize(
    int16_t requested_source_mode, int native_sampled_dac_ready,
    int16_t (*source_initializer)(int16_t mode, int16_t flag),
    int16_t *active_source_mode)
{
    int16_t initialized_mode;

    if (active_source_mode == 0 ||
        (native_sampled_dac_ready != 0 && native_sampled_dac_ready != 1))
        return PORTABLE_WHOLE_AUDIO_STARTUP_INVALID_ARGUMENT;
    if (requested_source_mode == 0) {
        *active_source_mode = 0;
        return PORTABLE_WHOLE_AUDIO_STARTUP_SILENT;
    }
    if (requested_source_mode < 0 || requested_source_mode > 8)
        return PORTABLE_WHOLE_AUDIO_STARTUP_INVALID_ARGUMENT;
    if (requested_source_mode != 1)
        return PORTABLE_WHOLE_AUDIO_STARTUP_UNSUPPORTED_PROFILE;
    if (native_sampled_dac_ready == 0)
        return PORTABLE_WHOLE_AUDIO_STARTUP_OUTPUT_UNAVAILABLE;
    if (source_initializer == 0)
        return PORTABLE_WHOLE_AUDIO_STARTUP_INVALID_ARGUMENT;

    initialized_mode = source_initializer(1, 0);
    if (initialized_mode != 1)
        return PORTABLE_WHOLE_AUDIO_STARTUP_SOURCE_REJECTED;
    *active_source_mode = 1;
    return PORTABLE_WHOLE_AUDIO_STARTUP_SELECTED;
}
