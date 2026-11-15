#ifndef SIMANT_NATIVE_AUDIO_RENDERER_H
#define SIMANT_NATIVE_AUDIO_RENDERER_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Render-only interface. No event returns source state or advances game time.
 * Payload/table bytes are copied at start, before canonical resource release. */
typedef struct SimAudioVoice {
    uint16_t object, length, step, end, loop, position;
    uint8_t fraction, flags, volume;
    const uint8_t *payload;
} SimAudioVoice;
void *sim_audio_create(const uint8_t volume_tables[2048]);
void sim_audio_destroy(void *renderer);
void sim_audio_opl(void *, uint64_t ns, uint8_t reg, uint8_t value);
void sim_audio_voice_start(void *, uint64_t ns, unsigned channel, const SimAudioVoice *);
void sim_audio_voice_stop(void *, uint64_t ns, unsigned channel);
void sim_audio_positions(void *, uint64_t ns, unsigned channels,
                         const uint16_t positions[4], const uint8_t volumes[4], unsigned active_mask);
void sim_audio_commit(void *, uint64_t ns);
void sim_audio_enable(void *, uint64_t ns, int enabled);
/* Timestamps are absolute game time, inclusive of events at each frame. */
void sim_audio_render(void *, int16_t *stereo, size_t frames, uint64_t first_frame);
uint64_t sim_audio_generated_frames(void *);
#ifdef __cplusplus
}
#endif
#endif
