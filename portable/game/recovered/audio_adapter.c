#include "audio_adapter.h"

#include <stdlib.h>

static _Thread_local SimRecoveredAudioBinding *active_binding;

static void refresh_options(void)
{
    SimRecoveredAudioBinding *binding = active_binding;
    if (binding == NULL || binding->intents == NULL) abort();
    portable_audio_intents_set_options(binding->intents,
                                       binding->driver_ready,
                                       fd_3D57_07A8[2],
                                       fd_3D57_07A8[1]);
}

void sim_recovered_audio_bind(SimRecoveredAudioBinding *binding)
{
    if (binding == NULL || binding->intents == NULL || active_binding != NULL)
        abort();
    binding->song_status_calls = 0;
    active_binding = binding;
    refresh_options();
}

int sim_recovered_audio_unbind(SimRecoveredAudioBinding *binding)
{
    if (binding == NULL || active_binding != binding) return 0;
    active_binding = NULL;
    return 1;
}

void myBeginSong(int16_t song, int16_t arg)
{
    refresh_options();
    if (!portable_audio_begin_song(active_binding->intents, song, arg)) abort();
}

void myBeginSound(int16_t sound, int16_t arg_a, int16_t arg_b)
{
    refresh_options();
    if (!portable_audio_begin_sound(active_binding->intents, sound,
                                    arg_a, arg_b)) abort();
}

int16_t mySongIsDone(void)
{
    int provider_result = 1;
    if (active_binding == NULL || active_binding->intents == NULL) abort();
    refresh_options();
    if (active_binding->intents->driver_ready &&
        active_binding->intents->songs_enabled) {
        if (active_binding->song_done == NULL) abort();
        ++active_binding->song_status_calls;
        provider_result = active_binding->song_done(
            active_binding->song_done_context);
    }
    return (int16_t)portable_audio_song_done(active_binding->intents,
                                              provider_result);
}

int16_t mySoundIsDone(void)
{
    return (int16_t)portable_audio_sound_done();
}
