#include "audio_voice_admission.h"

#include <stddef.h>
#include <string.h>

void portable_dac_voice_allocator_init(PortableDacVoiceAllocator *allocator)
{
    size_t i;
    if (allocator == NULL) return;
    memset(allocator, 0, sizeof(*allocator));
    for (i = 0; i < PORTABLE_DAC_VOICE_CHANNEL_COUNT; ++i) {
        allocator->channels[i].instrument_id = -1;
        allocator->channels[i].age = 15;
        allocator->channels[i].sample_object_id = -1;
        allocator->channels[i].sound_id = -1;
    }
}

PortableDacVoiceDecision portable_dac_voice_admit(
    PortableDacVoiceAllocator *allocator, uint8_t incoming_priority)
{
    PortableDacVoiceDecision result;
    uint8_t best_priority = 15;
    uint8_t best_age = 0;
    int16_t best_index = 0;
    size_t i;

    memset(&result, 0, sizeof(result));
    result.selected_channel = -1;
    result.priority = incoming_priority;
    if (allocator == NULL || incoming_priority < 1) return result;

    /* A byte increment and unsigned byte age comparison reproduce the Chan
     * fields and instructions at root:m295C:f_295C_00C9. */
    for (i = 0; i < PORTABLE_DAC_VOICE_CHANNEL_COUNT; ++i) {
        PortableDacVoiceChannel *channel = &allocator->channels[i];
        if (channel->active == 0) {
            channel->priority = 0;
            if (channel->owner_loaded != 0) {
                result.released_owner_channels[result.release_count++] =
                    (int8_t)i;
                channel->owner_loaded = 0;
            }
            channel->sound_id = -1;
            channel->sample_object_id = -1;
        }
        channel->age = (uint8_t)(channel->age + 1u);
        if (channel->priority < best_priority ||
            (channel->priority == best_priority && channel->age > best_age)) {
            best_priority = channel->priority;
            best_index = (int16_t)i;
            best_age = channel->age;
        }
    }
    if (incoming_priority >= best_priority)
        result.selected_channel = best_index;
    return result;
}

PortableDacVoiceDecision portable_dac_voice_admit_request(
    PortableDacVoiceAllocator *allocator,
    const PortableDacVoiceRequest *request)
{
    PortableDacVoiceDecision result;
    memset(&result, 0, sizeof(result));
    result.selected_channel = -1;
    if (allocator == NULL || request == NULL || request->sound_id < 0 ||
        request->instrument_id < 0 || request->sample_object_id < 0)
        return result;
    return portable_dac_voice_admit(allocator, request->priority);
}

int portable_dac_voice_commit_request(PortableDacVoiceAllocator *allocator,
                                      int16_t channel_index,
                                      const PortableDacVoiceRequest *request)
{
    PortableDacVoiceChannel *channel;
    if (allocator == NULL || channel_index < 0 ||
        channel_index >= PORTABLE_DAC_VOICE_CHANNEL_COUNT ||
        request == NULL || request->priority < 1 || request->sound_id < 0 ||
        request->instrument_id < 0 || request->instrument_id > INT8_MAX ||
        request->sample_object_id < 0)
        return 0;
    channel = &allocator->channels[channel_index];
    channel->priority = request->priority;
    channel->instrument_id = (int8_t)request->instrument_id;
    channel->note = request->note;
    channel->age = 0;
    channel->active = 1;
    channel->owner_loaded = 1;
    channel->sound_id = request->sound_id;
    channel->sample_object_id = request->sample_object_id;
    channel->velocity = request->velocity;
    return 1;
}

int portable_dac_voice_set_active(PortableDacVoiceAllocator *allocator,
                                 int16_t channel_index, int active)
{
    if (allocator == NULL || channel_index < 0 ||
        channel_index >= PORTABLE_DAC_VOICE_CHANNEL_COUNT ||
        (active != 0 && active != 1))
        return 0;
    allocator->channels[channel_index].active = (uint8_t)active;
    return 1;
}
