#include "../../audio/intent.h"
#include "../../game/recovered/audio_adapter.h"

#include <assert.h>
#include <stdio.h>

typedef struct SongStatus {
    int value;
    unsigned calls;
} SongStatus;

static int song_done(void *context)
{
    SongStatus *status = (SongStatus *)context;
    ++status->calls;
    return status->value;
}

int main(void)
{
    RecoveredState state;
    RecoveredBindingFrame frame;
    PortableAudioIntents intents;
    SimRecoveredAudioBinding binding;
    SongStatus song_status = { 0, 0 };
    PortableAudioIntent intent;

    recovered_state_init(&state);
    state.fd_3D57_07A8[1] = 0;
    state.fd_3D57_07A8[2] = 0;
    recovered_bind_begin(&frame, &state);
    portable_audio_intents_init(&intents);
    binding.intents = &intents;
    binding.driver_ready = 1;
    binding.song_done = song_done;
    binding.song_done_context = &song_status;
    binding.song_status_calls = 0;
    sim_recovered_audio_bind(&binding);

    myBeginSound(0x2f, 0, -5);
    myBeginSong(0x2afa, 0x7e);
    assert(intents.count == 0); /* both live source options were disabled */
    assert(mySongIsDone() == 1);
    assert(song_status.calls == 0);

    /* Options are read from the currently bound RecoveredState every call. */
    fd_3D57_07A8[2] = 1;
    myBeginSound(0x2f, 0x1234, -5);
    fd_3D57_07A8[1] = 1;
    myBeginSong(0x2afa, 0x7e);
    assert(intents.count == 3);
    assert(portable_audio_next_intent(&intents, &intent));
    assert(intent.kind == PORTABLE_AUDIO_INTENT_SOUND);
    assert(intent.id == 0x2f && intent.arg_a == 0x1234 && intent.arg_b == -5);
    assert(portable_audio_next_intent(&intents, &intent));
    assert(intent.kind == PORTABLE_AUDIO_INTENT_STOP_SONG);
    assert(portable_audio_next_intent(&intents, &intent));
    assert(intent.kind == PORTABLE_AUDIO_INTENT_SONG);
    assert(intent.id == 0x2afa && intent.arg_a == 0x7e);

    assert(mySongIsDone() == 0);
    assert(song_status.calls == 1 && binding.song_status_calls == 1);
    song_status.value = 1;
    assert(mySongIsDone() == 1);
    assert(song_status.calls == 2 && binding.song_status_calls == 2);
    assert(mySoundIsDone() == 1);

    fd_3D57_07A8[1] = 0;
    assert(mySongIsDone() == 1);
    assert(song_status.calls == 2);
    assert(sim_recovered_audio_unbind(&binding));
    recovered_bind_end(&frame, &state);
    puts("recovered audio adapter: PASS");
    return 0;
}
