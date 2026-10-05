#ifndef SIMANT_PORTABLE_AUDIO_DAC_MIXER_H
#define SIMANT_PORTABLE_AUDIO_DAC_MIXER_H

#include <stdint.h>

enum { PORTABLE_DAC_MODE1_CHANNELS = 2 };

/* Releases decoded PCM retained by the source-derived native mixer. */
void portable_dac_free_pcm(uint8_t *pcm);

#endif
