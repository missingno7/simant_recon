#ifndef SIMANT_PLATFORM_AUDIO_MIXER_SERVICE_H
#define SIMANT_PLATFORM_AUDIO_MIXER_SERVICE_H

#include <stddef.h>
#include <stdint.h>

#include "../../audio/dac_mixer.h"

typedef enum PortableDacSchedulerStatus {
    PORTABLE_DAC_SCHEDULER_OK = 0,
    PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT
} PortableDacSchedulerStatus;

typedef struct PortableDacLiveVoice {
    uint8_t *pcm;
    size_t pcm_size;
    uint16_t position;
    uint16_t end;
    uint16_t loop_start;
    uint16_t step_8_8;
    uint8_t fraction;
    uint8_t volume_row;
    uint8_t looped;
    uint8_t active;
} PortableDacLiveVoice;

typedef struct PortableDacLiveScheduler {
    PortableDacLiveVoice voices[PORTABLE_DAC_MODE1_CHANNELS];
    uint8_t speaker_enabled;
} PortableDacLiveScheduler;

typedef struct PortableDacLiveTick {
    uint8_t output_generated;
    uint8_t mixed_register;
    uint8_t speaker_enabled;
} PortableDacLiveTick;

void portable_dac_live_scheduler_init(PortableDacLiveScheduler *scheduler);
void portable_dac_live_scheduler_close(PortableDacLiveScheduler *scheduler);
PortableDacSchedulerStatus portable_dac_live_scheduler_tick(
    PortableDacLiveScheduler *scheduler, PortableDacLiveTick *tick);

#endif
