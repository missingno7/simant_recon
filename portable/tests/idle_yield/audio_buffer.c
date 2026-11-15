/* Real SDL consumer: exact device-sized blocks, no ordinary starvation, and a
 * stopped producer must be detected. No game/IRQ work on the audio thread. */
#include "portable/platform/sdl3/audio.h"
#include <SDL3/SDL.h>
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
int main(void)
{
    PortableSdl3Audio audio;
    assert(SDL_SetHint(SDL_HINT_AUDIO_DRIVER, "dummy"));
    assert(portable_sdl3_audio_open(&audio, 48000));
    size_t block = audio.block_frames;
    int16_t *pcm = calloc(block, 4);
    assert(pcm && block > 1);
    assert(portable_sdl3_audio_queue_frames(&audio, pcm, block-1));
    assert(audio.queue_calls == 0 && !audio.started);
    assert(portable_sdl3_audio_queue_frames(&audio, pcm, 1));
    assert(audio.queue_calls == 1 && audio.queued_frames == block && audio.started);
    uint64_t start = SDL_GetTicksNS(), supplied = block;
    while (SDL_GetTicksNS()-start < 2000000000) {
        uint64_t due = (SDL_GetTicksNS()-start)*48000/1000000000;
        while (supplied < due) {
            assert(portable_sdl3_audio_queue_frames(&audio, pcm, block));
            supplied += block;
        }
        SDL_Delay(1);
    }
    SDL_LockAudioStream(audio.stream);
    assert(audio.requests > 0 && audio.underruns == 0);
    SDL_UnlockAudioStream(audio.stream);
    SDL_Delay(300); /* Negative control: deliberately starve the consumer. */
    SDL_LockAudioStream(audio.stream);
    assert(audio.underruns > 0 && audio.missing_bytes > 0);
    printf("PASS device blocks=%zu requests=%llu detected-starvations=%llu\n", block,
        (unsigned long long)audio.requests, (unsigned long long)audio.underruns);
    SDL_UnlockAudioStream(audio.stream);
    portable_sdl3_audio_close(&audio);
    free(pcm);
    return 0;
}
