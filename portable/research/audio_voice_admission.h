#ifndef SIMANT_PORTABLE_RESEARCH_AUDIO_VOICE_ADMISSION_H
#define SIMANT_PORTABLE_RESEARCH_AUDIO_VOICE_ADMISSION_H

#include <stdint.h>

enum { PORTABLE_DAC_VOICE_CHANNEL_COUNT = 2 };

typedef struct PortableDacVoiceChannel {
    uint8_t priority;       /* DOS Chan.c2 */
    int8_t instrument_id;   /* DOS Chan.c3; -1 means no previous instrument */
    uint8_t note;           /* DOS Chan.c4 */
    uint8_t age;            /* DOS Chan.c5, including byte wrap */
    uint8_t active;         /* DOS DAC SndChan.snd far pointer is nonzero */
    uint8_t owner_loaded;   /* DOS retained Sample.loaded == 1 */
    int16_t sound_id;
    int16_t sample_object_id;
    uint8_t velocity;      /* SfxNote.d, retained for subsequent synthesis */
} PortableDacVoiceChannel;

typedef struct PortableDacVoiceAllocator {
    PortableDacVoiceChannel channels[PORTABLE_DAC_VOICE_CHANNEL_COUNT];
} PortableDacVoiceAllocator;

typedef struct PortableDacVoiceRequest {
    int16_t sound_id;          /* index passed to source f_295C_0367 */
    int16_t instrument_id;     /* SfxNote.c, passed to f_295C_01EC */
    int16_t sample_object_id;  /* mapped DAC Sample.object */
    uint8_t priority;          /* SfxNote.b */
    uint8_t note;              /* SfxNote.a */
    uint8_t velocity;          /* SfxNote.d */
} PortableDacVoiceRequest;

typedef struct PortableDacVoiceDecision {
    int16_t selected_channel; /* -1 when source priority rule rejects */
    uint8_t priority;
    uint8_t release_count;
    int8_t released_owner_channels[PORTABLE_DAC_VOICE_CHANNEL_COUNT];
} PortableDacVoiceDecision;

void portable_dac_voice_allocator_init(PortableDacVoiceAllocator *allocator);

/* The request copies a source SfxNote row plus its mapped DAC Sample.object.
 * This allocator does not establish resource support or decode playback; the
 * caller must resolve a supported sample profile first.
 */

/* Source f_295C_00C9 for the mode-1 DAC's two type-1 channels. Each
 * nonzero-priority request clears priority on idle channels, releases their
 * retained loaded-owner marker, increments both age bytes, and selects the
 * oldest channel having the lowest numeric current priority. Priority zero
 * is rejected before any state mutation, matching the DOS early return.
 */
PortableDacVoiceDecision portable_dac_voice_admit(
    PortableDacVoiceAllocator *allocator, uint8_t incoming_priority);
PortableDacVoiceDecision portable_dac_voice_admit_request(
    PortableDacVoiceAllocator *allocator,
    const PortableDacVoiceRequest *request);

/* Apply the writes made by f_295C_01EC after a supported sample resource has
 * loaded and its channel start succeeded. This is separate from admission
 * because resource loading can fail after the allocator has selected a slot.
 */
int portable_dac_voice_commit_request(PortableDacVoiceAllocator *allocator,
                                      int16_t channel,
                                      const PortableDacVoiceRequest *request);

/* Reflect the DAC timer ISR's active-pointer state before the next request. */
int portable_dac_voice_set_active(PortableDacVoiceAllocator *allocator,
                                 int16_t channel, int active);

#endif
