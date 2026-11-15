/* Real SDL queue/PCM with a deterministic physical clock and device lifecycle.
 * Source timestamps are supplied by the test; there is no game or sequencer. */
#include "portable/platform/sdl3/audio.h"
#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)) { fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x);exit(1); } } while(0)
static uint64_t now;
static unsigned starts,pauses;
Uint64 SDLCALL __wrap_SDL_GetTicksNS(void) { return now; }
SDL_AudioStream * SDLCALL __wrap_SDL_OpenAudioDeviceStream(SDL_AudioDeviceID id,const SDL_AudioSpec *spec,SDL_AudioStreamCallback callback,void *context) {
    (void)id;(void)callback;(void)context;return SDL_CreateAudioStream(spec,spec);
}
SDL_AudioDeviceID SDLCALL __wrap_SDL_GetAudioStreamDevice(SDL_AudioStream *s) { (void)s;return 1; }
bool SDLCALL __wrap_SDL_GetAudioDeviceFormat(SDL_AudioDeviceID id,SDL_AudioSpec *spec,int *frames) {
    (void)id;*spec=(SDL_AudioSpec){SDL_AUDIO_S16,2,48000};*frames=480;return true;
}
bool SDLCALL __wrap_SDL_ResumeAudioStreamDevice(SDL_AudioStream *s) { (void)s;++starts;return true; }
bool SDLCALL __wrap_SDL_PauseAudioStreamDevice(SDL_AudioStream *s) { (void)s;++pauses;return true; }
static void supply(PortableSdl3Audio *a,unsigned block,unsigned count) {
    int16_t pcm[960];
    while(count--) {
        for(unsigned i=0;i<960;++i) pcm[i]=(int16_t)block;
        CHECK(portable_sdl3_audio_queue_at(a,pcm,480,(uint64_t)block*480));++block;
    }
}
static void consume(PortableSdl3Audio *a,unsigned blocks) {
    int16_t pcm[960];while(blocks--) CHECK(SDL_GetAudioStreamData(a->stream,pcm,sizeof(pcm))==sizeof(pcm));
}
int main(void) {
    PortableSdl3Audio a;CHECK(SDL_SetHint(SDL_HINT_AUDIO_DRIVER,"dummy"));CHECK(portable_sdl3_audio_open(&a,48000));
    /* Startup I/O can look balanced before a full target exists. That early
     * observation must be revoked if source reads then catch up rapidly. */
    portable_sdl3_audio_begin(&a,0);supply(&a,0,1);now=14000000;
    portable_sdl3_audio_begin(&a,480);CHECK(portable_sdl3_audio_service(&a));CHECK(!starts);
    supply(&a,1,29);portable_sdl3_audio_begin(&a,14400);CHECK(portable_sdl3_audio_service(&a));CHECK(!starts);
    portable_sdl3_audio_close(&a);now=0;CHECK(portable_sdl3_audio_open(&a,48000));
    /* 300 ms of game catch-up in 1 ms of physical time must not start audio. */
    portable_sdl3_audio_begin(&a,0);supply(&a,0,30);now=1000000;
    portable_sdl3_audio_begin(&a,14400);CHECK(portable_sdl3_audio_service(&a));CHECK(!starts && a.gated);
    now=11000000;portable_sdl3_audio_begin(&a,14880);supply(&a,30,1);CHECK(portable_sdl3_audio_service(&a));CHECK(!starts);
    now=21000000;portable_sdl3_audio_begin(&a,15360);supply(&a,31,1);CHECK(portable_sdl3_audio_service(&a));
    CHECK(starts==1 && !a.gated && SDL_GetAudioStreamQueued(a.stream)==1920*4);
    /* Only the newest four source blocks survive startup, in original order. */
    int16_t pcm[3840];CHECK(SDL_GetAudioStreamData(a.stream,pcm,sizeof(pcm))==sizeof(pcm));
    for(unsigned block=0;block<4;++block) for(unsigned i=0;i<960;++i) CHECK(pcm[block*960+i]==28+(int)block);
    /* Normal balanced production/consumption never trims. */
    supply(&a,32,4);CHECK(portable_sdl3_audio_service(&a));
    for(unsigned b=36;b<136;++b) {
        now+=10000000;portable_sdl3_audio_begin(&a,(uint64_t)b*480);consume(&a,1);supply(&a,b,1);CHECK(portable_sdl3_audio_service(&a));
    }
    CHECK(a.overflow_resets==0 && a.underruns==0);
    /* A large unexpected queue surplus drops the OLD prefix once. */
    supply(&a,136,20);CHECK(portable_sdl3_audio_service(&a));CHECK(a.overflow_resets==1);
    CHECK(SDL_GetAudioStreamQueued(a.stream)==1920*4);
    CHECK(SDL_GetAudioStreamData(a.stream,pcm,sizeof(pcm))==sizeof(pcm));
    for(unsigned block=0;block<4;++block) for(unsigned i=0;i<960;++i) CHECK(pcm[block*960+i]==152+(int)block);
    /* A stalled producer is gated, catches up without feeding the consumer,
     * and restarts once with current content. No source time was changed. */
    now+=1000000000;portable_sdl3_audio_begin(&a,156*480);CHECK(a.gated && pauses==1);
    now+=10000000;portable_sdl3_audio_begin(&a,157*480);supply(&a,156,1);CHECK(portable_sdl3_audio_service(&a));CHECK(starts==1);
    supply(&a,157,99);portable_sdl3_audio_begin(&a,256*480);CHECK(portable_sdl3_audio_service(&a));CHECK(starts==1);
    now+=10000000;portable_sdl3_audio_begin(&a,257*480);supply(&a,256,1);CHECK(portable_sdl3_audio_service(&a));
    CHECK(starts==2 && !a.gated && a.stall_restarts==1 && a.overflow_resets==1);
    portable_sdl3_audio_close(&a);
    puts("PASS: startup pacing gate, steady queue, newest-prefix retention and single stall restart");return 0;
}
