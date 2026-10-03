#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_STARTUP_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_STARTUP_H

#include <stdint.h>

typedef enum PortableWholeAudioStartupStatus {
    PORTABLE_WHOLE_AUDIO_STARTUP_SELECTED = 0,
    PORTABLE_WHOLE_AUDIO_STARTUP_SILENT,
    PORTABLE_WHOLE_AUDIO_STARTUP_INVALID_ARGUMENT,
    PORTABLE_WHOLE_AUDIO_STARTUP_UNSUPPORTED_PROFILE,
    PORTABLE_WHOLE_AUDIO_STARTUP_OUTPUT_UNAVAILABLE,
    PORTABLE_WHOLE_AUDIO_STARTUP_SOURCE_REJECTED
} PortableWholeAudioStartupStatus;

/* Native profile gate for the original source mode numbers. Mode 0 is the
 * source silent profile. Mode 1 is supported only when the native sampled-DAC
 * backend has already opened. Modes 2..8 are legacy hardware profiles and
 * remain unavailable; this adapter never runs their DOS/BIOS probes.
 *
 * The source initializer is the generated f_277E_0000 entry. It is called only
 * for selected mode 1 with flag 0. On success, active_source_mode is updated;
 * on every failure it remains unchanged.
 */
PortableWholeAudioStartupStatus portable_whole_audio_startup_initialize(
    int16_t requested_source_mode, int native_sampled_dac_ready,
    int16_t (*source_initializer)(int16_t mode, int16_t flag),
    int16_t *active_source_mode);

#endif
