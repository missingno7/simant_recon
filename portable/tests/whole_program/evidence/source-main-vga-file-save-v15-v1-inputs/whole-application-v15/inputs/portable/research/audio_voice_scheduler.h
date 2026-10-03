#ifndef SIMANT_PORTABLE_RESEARCH_AUDIO_VOICE_SCHEDULER_H
#define SIMANT_PORTABLE_RESEARCH_AUDIO_VOICE_SCHEDULER_H

#include "audio_voice_admission.h"
#include "../audio/dac_mixer.h"

typedef enum PortableDacSchedulerStatus {
    PORTABLE_DAC_SCHEDULER_OK = 0,
    PORTABLE_DAC_SCHEDULER_INVALID_ARGUMENT,
    PORTABLE_DAC_SCHEDULER_UNSUPPORTED_PROFILE,
    PORTABLE_DAC_SCHEDULER_RESOURCE_ERROR,
    PORTABLE_DAC_SCHEDULER_OUT_OF_MEMORY
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
} PortableDacLiveVoice;

typedef struct PortableDacLiveScheduler {
    PortableDacVoiceAllocator allocator;
    PortableDacLiveVoice voices[PORTABLE_DAC_VOICE_CHANNEL_COUNT];
    uint8_t speaker_enabled;
} PortableDacLiveScheduler;

typedef struct PortableDacLiveStart {
    PortableDacVoiceDecision admission;
    int16_t stopped_channel; /* accepted voice that source f_290D_026C replaced */
    int16_t started_channel;
} PortableDacLiveStart;

typedef struct PortableDacLiveTick {
    uint8_t output_generated; /* false when ISR's over-end branch skips out_speaker */
    uint8_t mixed_register;   /* AL at source out_speaker entry, when generated */
    uint8_t speaker_enabled;  /* source PC-speaker state after threshold handling */
} PortableDacLiveTick;

void portable_dac_live_scheduler_init(PortableDacLiveScheduler *scheduler);
void portable_dac_live_scheduler_close(PortableDacLiveScheduler *scheduler);

/* Start a source-table SFX after profile validation and exact two-channel
 * allocator admission. Unsupported IDs do not age or mutate voice state.
 * Successful starts retain decoded PCM and replace only the selected channel.
 */
PortableDacSchedulerStatus portable_dac_live_scheduler_start(
    PortableDatabase *database, PortableDacLiveScheduler *scheduler,
    const PortableDacVoiceRequest *request, uint16_t master_volume,
    PortableDacLiveStart *start);

/* Advance one mode-1 PIT tick, matching the two-channel order, 8.8 stepping,
 * volume-table transform, centered average, and source end/loop early exit.
 */
PortableDacSchedulerStatus portable_dac_live_scheduler_tick(
    PortableDacLiveScheduler *scheduler, PortableDacLiveTick *tick);

#endif
