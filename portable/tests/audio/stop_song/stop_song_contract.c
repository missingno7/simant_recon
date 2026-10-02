/* Isolated native boundary model for root:284A StopSong.
 * This file is a test fixture, not production audio code.
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct StopSongState {
    int16_t active;
    int16_t song_number;
    uint32_t song_token;
    int song_data_live;
} StopSongState;

typedef struct StopSongOps {
    void (*release_current_song)(StopSongState *state);
    void (*reset_synth)(StopSongState *state);
} StopSongOps;

static void release_current_song(StopSongState *state)
{
    printf("release|active=%d|song=%d|token=%" PRIu32 "|data_before=%d\n",
           state->active, state->song_number, state->song_token,
           state->song_data_live);
    state->song_data_live = 0;
}

static void reset_synth(StopSongState *state)
{
    printf("reset|active=%d|data=%d\n", state->active,
           state->song_data_live);
}

static void stop_song(StopSongState *state, const StopSongOps *ops)
{
    if (state->active != 0) {
        state->active = 0;
        ops->release_current_song(state);
        ops->reset_synth(state);
    }
}

int main(int argc, char **argv)
{
    StopSongState state;
    const StopSongOps ops = { release_current_song, reset_synth };
    int repetitions;
    int i;

    if (argc != 3) return 2;
    state.active = (int16_t)strtol(argv[1], NULL, 0);
    state.song_number = (int16_t)strtol(argv[2], NULL, 0);
    state.song_token = UINT32_C(1);
    state.song_data_live = 1;
    repetitions = 2;
    for (i = 0; i < repetitions; ++i) stop_song(&state, &ops);
    printf("final|active=%d|song=%d|data=%d|calls=%d\n", state.active,
           state.song_number, state.song_data_live, repetitions);
    return 0;
}
