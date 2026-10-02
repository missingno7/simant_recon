#ifndef SIMANT_GAME_RECOVERED_AUDIO_ADAPTER_H
#define SIMANT_GAME_RECOVERED_AUDIO_ADAPTER_H

#include "recovered_state.h"
#include "../../audio/intent.h"

typedef int (*SimRecoveredSongDoneProvider)(void *context);

typedef struct SimRecoveredAudioBinding {
    PortableAudioIntents *intents;
    int driver_ready;
    SimRecoveredSongDoneProvider song_done;
    void *song_done_context;
    unsigned song_status_calls;
} SimRecoveredAudioBinding;

/* Bind for the duration of recovered-core calls. Audio options are read from
 * the active recovered state on each source entry, so menu changes take
 * effect without copying potentially stale settings into the host binding.
 */
void sim_recovered_audio_bind(SimRecoveredAudioBinding *binding);
int sim_recovered_audio_unbind(SimRecoveredAudioBinding *binding);

/* Source-compatible host boundaries from root:m00DF. Generated callers may
 * pass two song arguments; the original consumes only the ID. The adapter
 * preserves both logical arguments in the typed intent for host inspection.
 */
void myBeginSong(int16_t song, int16_t arg);
void myBeginSound(int16_t sound, int16_t arg_a, int16_t arg_b);
int16_t mySongIsDone(void);
int16_t mySoundIsDone(void);

#endif
