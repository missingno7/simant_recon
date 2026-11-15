#include "audio.h"
#include "../../whole_program/platform/audio_native.h"

#include <SDL3/SDL.h>
#include <limits.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

typedef struct AudioMarker {
    uint64_t id, source_frame, trigger_ns, epoch, offset, lower_ns, upper_ns;
    unsigned kind, channel, object;
    int submitted, resolved, printed;
} AudioMarker;
typedef struct AudioObservation {
    FILE *file;
    uint64_t previous_ns, last_snapshot;
    unsigned count;
    AudioMarker markers[8192];
} AudioObservation;

enum { AUDIO_TARGET_PERIODS=4, AUDIO_LIMIT_PERIODS=5 };
static int replace_queue(PortableSdl3Audio *a,int reason);

/* Physical production-rate observations gate presentation only. A long service
 * gap means source reads may now catch up in a burst. Do not start/restart the
 * consumer in that burst. No source callback or clock setter is called here. */
int portable_sdl3_audio_begin(PortableSdl3Audio *a,uint64_t frame) {
    uint64_t now=SDL_GetTicksNS();
    uint64_t period=(uint64_t)a->block_frames*1000000000/a->sample_rate;
    if(!a->timeline || (a->started && !a->gated && now-a->service_wall>period*AUDIO_LIMIT_PERIODS)) {
        a->gate_reason=a->timeline?2:1;
        a->timeline=1;a->gated=1;a->gate_ready=0;
        a->gate_wall=now;a->gate_frame=frame;
        /* Refill the retained window with NEW source blocks. A shallow or
         * slow catch-up must not replay PCM already heard before the gap. */
        a->recent_frames=0;
        if(a->started) { if(!SDL_PauseAudioStreamDevice(a->stream)) return 0;++a->stall_restarts; }
    }
    a->service_wall=now;
    if(a->gated && frame-a->gate_frame>=a->block_frames && now-a->gate_wall>=period) {
        uint64_t elapsed=now-a->gate_wall;
        uint64_t physical_frames=(elapsed/1000000000)*a->sample_rate+(elapsed%1000000000)*a->sample_rate/1000000000;
        if(frame-a->gate_frame<=physical_frames+(a->sample_rate+999)/1000) a->gate_ready=1;
        else { a->gate_ready=0;a->gate_wall=now;a->gate_frame=frame; }
    }
    return 1;
}

/* A get callback is before the read. The following observation detects the
 * consumed prefix, so head arrival is bracketed by successive observations,
 * normally one device period apart. This is queue-head, not speaker latency. */
static void observe_head(PortableSdl3Audio *a) {
    AudioObservation *o=a->observation;
    if(!o) return;
    int bytes=SDL_GetAudioStreamQueued(a->stream);
    if(bytes<0) return;
    uint64_t ns=SDL_GetTicksNS(),head=a->stream_tail-(unsigned)bytes/4;
    for(unsigned i=0;i<o->count;++i) {
        AudioMarker *m=&o->markers[i];
        if(m->submitted && !m->resolved && m->epoch==a->stream_epoch && m->offset<head) {
            m->lower_ns=o->previous_ns>m->trigger_ns?o->previous_ns:m->trigger_ns;
            m->upper_ns=ns;m->resolved=1;
        }
    }
    o->previous_ns=ns;
}
void portable_sdl3_audio_trigger(PortableSdl3Audio *a,uint64_t game_ns,unsigned kind,unsigned channel,unsigned object) {
    AudioObservation *o=a->observation;
    if(!o) return;
    SDL_LockAudioStream(a->stream);
    if(kind==PORTABLE_AUDIO_SAMPLE_EMISSION || kind==PORTABLE_AUDIO_SAMPLE_STOP) {
        for(unsigned i=o->count;i>0;--i) {
            AudioMarker *m=&o->markers[i-1];
            if(m->kind==PORTABLE_AUDIO_SAMPLE_SETUP && m->channel==channel && m->source_frame==UINT64_MAX) {
                if(kind==PORTABLE_AUDIO_SAMPLE_STOP) m->resolved=2;
                else {
                    m->source_frame=(game_ns/1000000000)*48000+((game_ns%1000000000)*48000+999999999)/1000000000;
                    fprintf(o->file,"{\"tag\":\"sample_emission\",\"id\":%llu,\"game_ns\":%llu,\"wall_ns\":%llu}\n",(unsigned long long)m->id,(unsigned long long)game_ns,(unsigned long long)SDL_GetTicksNS());
                }
                break;
            }
        }
        SDL_UnlockAudioStream(a->stream);return;
    }
    if(o->count<8192) {
        AudioMarker *m=&o->markers[o->count++];
        m->id=o->count;m->source_frame=(game_ns/1000000000)*48000+((game_ns%1000000000)*48000+999999999)/1000000000;
        if(kind==PORTABLE_AUDIO_SAMPLE_SETUP) m->source_frame=UINT64_MAX;
        m->trigger_ns=SDL_GetTicksNS();m->kind=kind;m->channel=channel;m->object=object;
        fprintf(o->file,"{\"tag\":\"trigger\",\"id\":%llu,\"wall_ns\":%llu,\"game_ns\":%llu,\"kind\":%u,\"channel\":%u,\"object\":%u}\n",
            (unsigned long long)m->id,(unsigned long long)m->trigger_ns,(unsigned long long)game_ns,kind,channel,object);
    }
    SDL_UnlockAudioStream(a->stream);
}
void portable_sdl3_audio_observe(PortableSdl3Audio *a,uint64_t game_ns) {
    AudioObservation *o=a->observation;
    if(!o) return;
    SDL_LockAudioStream(a->stream);observe_head(a);
    uint64_t now=SDL_GetTicksNS();
    if(now-o->last_snapshot>=10000000) {
        fprintf(o->file,"{\"tag\":\"queue\",\"wall_ns\":%llu,\"game_ns\":%llu,\"frames\":%d,\"pending\":%zu,\"started\":%d,\"gated\":%d,\"resets\":%llu,\"overflow_resets\":%llu,\"underruns\":%llu}\n",
            (unsigned long long)now,(unsigned long long)game_ns,SDL_GetAudioStreamQueued(a->stream)/4,a->pending_frames,a->started,a->gated,(unsigned long long)a->resets,(unsigned long long)a->overflow_resets,(unsigned long long)a->underruns);
        o->last_snapshot=now;
    }
    for(unsigned i=0;i<o->count;++i) {
        AudioMarker *m=&o->markers[i];
        if(m->resolved && !m->printed) {
            fprintf(o->file,"{\"tag\":\"%s\",\"id\":%llu,\"lower_ns\":%llu,\"upper_ns\":%llu,\"trigger_ns\":%llu}\n",
                m->resolved==2?"discarded":"head",(unsigned long long)m->id,(unsigned long long)m->lower_ns,(unsigned long long)m->upper_ns,(unsigned long long)m->trigger_ns);
            m->printed=1;
        }
    }
    SDL_UnlockAudioStream(a->stream);
}

/* The ring contains exactly the newest four completed source blocks. Clearing
 * and rebuilding under the stream lock is equivalent to dropping the oldest
 * queued prefix, without using SDL's consumer/resampler to discard samples.
 * This also works when the hardware changes its format. Pending partial source
 * PCM follows the retained blocks and keeps its original position. */
static int replace_queue(PortableSdl3Audio *a,int reason) {
    const size_t target=a->block_frames*AUDIO_TARGET_PERIODS;
    uint64_t started=SDL_GetTicksNS();
    SDL_LockAudioStream(a->stream);observe_head(a);
    int bytes=SDL_GetAudioStreamQueued(a->stream);
    if(bytes<0) { SDL_UnlockAudioStream(a->stream);return 0; }
    int queued=bytes/4;
    if((uint64_t)queued>a->queue_peak_frames) a->queue_peak_frames=queued;
    if(!SDL_ClearAudioStream(a->stream)) { SDL_UnlockAudioStream(a->stream);return 0; }
    ++a->stream_epoch;a->stream_tail=0;
    size_t tail=target-a->recent_cursor;
    int ok=SDL_PutAudioStreamData(a->stream,a->recent+a->recent_cursor*2,(int)tail*4) &&
        (!a->recent_cursor || SDL_PutAudioStreamData(a->stream,a->recent,(int)a->recent_cursor*4));
    if(!ok) { SDL_UnlockAudioStream(a->stream);return 0; }
    a->stream_tail=target;++a->resets;
    a->queue_calls+=a->recent_cursor?2:1;a->queued_frames+=target;
    if(reason==3) ++a->overflow_resets;
    if((size_t)queued>target) a->discarded_frames+=(size_t)queued-target;
    AudioObservation *o=a->observation;
    if(o) {
        const int64_t base=(int64_t)a->recent_end-(int64_t)target;
        for(unsigned i=0;i<o->count;++i) {
            AudioMarker *m=&o->markers[i];
            if(m->resolved) continue;
            if(m->source_frame==UINT64_MAX) continue;
            if((int64_t)m->source_frame<base) m->resolved=2;
            else if(m->source_frame<a->recent_end+a->pending_frames) {
                m->submitted=1;m->epoch=a->stream_epoch;m->offset=(int64_t)m->source_frame-base;
            } else m->submitted=0;
        }
        o->previous_ns=SDL_GetTicksNS();
        fprintf(o->file,"{\"tag\":\"replace\",\"wall_ns\":%llu,\"reason\":%d,\"old_frames\":%d,\"kept_frames\":%zu,\"source_end\":%llu}\n",
            (unsigned long long)o->previous_ns,reason,queued,target,(unsigned long long)a->recent_end);
    }
    a->submission_ns+=SDL_GetTicksNS()-started;
    SDL_UnlockAudioStream(a->stream);return 1;
}
int portable_sdl3_audio_service(PortableSdl3Audio *a) {
    if(a->gated) {
        if(!a->gate_ready || a->recent_frames<a->block_frames*AUDIO_TARGET_PERIODS) return 1;
        if(!replace_queue(a,a->gate_reason) || !SDL_ResumeAudioStreamDevice(a->stream)) return 0;
        if(!a->started) a->start_delay_ns=SDL_GetTicksNS()-a->opened_ns;
        a->started=1;a->gated=0;
    } else {
        int bytes=SDL_GetAudioStreamQueued(a->stream);
        if(bytes<0) return 0;
        int queued=bytes/4;
        if((uint64_t)queued>a->queue_peak_frames) a->queue_peak_frames=queued;
        if((size_t)queued+a->pending_frames>a->block_frames*AUDIO_LIMIT_PERIODS && !replace_queue(a,3)) return 0;
    }
    return 1;
}

/* SDL calls this under the stream lock on its consumer thread. Observe only:
 * canonical device/IRQ work must stay on the game thread and machine timeline.
 * A positive additional request is a conservative stream-underrun count (SDL
 * may slightly overestimate resampling input). It is never hidden by a refill. */
static void SDLCALL observe_consumption(void *context, SDL_AudioStream *stream,
                                       int additional, int total)
{
    PortableSdl3Audio *audio = context;
    (void)stream; (void)total;
    ++audio->requests;
    observe_head(audio);
    if (additional > 0) { ++audio->underruns; audio->missing_bytes += additional; }
}

void portable_sdl3_audio_performance(PortableSdl3Audio *audio, FILE *f)
{
    if (audio->stream) SDL_LockAudioStream(audio->stream);
    fprintf(f, "\"audio_block_frames\":%zu,\"audio_queue_calls\":%llu,\"audio_queued_frames\":%llu,\"audio_underruns\":%llu,\"audio_missing_bytes\":%llu,\"audio_requests\":%llu,\"audio_pending_frames\":%zu,\"audio_queue_frames\":%d,",
        audio->block_frames, (unsigned long long)audio->queue_calls,
        (unsigned long long)audio->queued_frames, (unsigned long long)audio->underruns,
        (unsigned long long)audio->missing_bytes, (unsigned long long)audio->requests,
        audio->pending_frames, audio->stream ? SDL_GetAudioStreamQueued(audio->stream)/4 : 0);
    fprintf(f, "\"audio_submission_ns\":%llu,", (unsigned long long)audio->submission_ns);
    fprintf(f,"\"audio_target_frames\":%zu,\"audio_limit_frames\":%zu,\"audio_queue_peak_frames\":%llu,\"audio_queue_resets\":%llu,\"audio_overflow_resets\":%llu,\"audio_stall_restarts\":%llu,\"audio_discarded_frames\":%llu,\"audio_gated_frames\":%llu,\"audio_start_delay_ns\":%llu,\"audio_gated\":%d,",
        audio->block_frames*AUDIO_TARGET_PERIODS,audio->block_frames*AUDIO_LIMIT_PERIODS,(unsigned long long)audio->queue_peak_frames,
        (unsigned long long)audio->resets,(unsigned long long)audio->overflow_resets,(unsigned long long)audio->stall_restarts,
        (unsigned long long)audio->discarded_frames,(unsigned long long)audio->gated_frames,(unsigned long long)audio->start_delay_ns,audio->gated);
    if (audio->stream) SDL_UnlockAudioStream(audio->stream);
}

int portable_sdl3_audio_open(PortableSdl3Audio *audio, int sample_rate)
{
    SDL_AudioSpec spec;
    SDL_AudioStream *stream;
    if (audio == NULL || sample_rate <= 0) return 0;
    memset(audio, 0, sizeof(*audio));
    audio->opened_ns=SDL_GetTicksNS();
    if (!SDL_WasInit(SDL_INIT_AUDIO)) {
        if (!SDL_InitSubSystem(SDL_INIT_AUDIO)) return 0;
        audio->owns_subsystem = 1;
    }
    spec.format = SDL_AUDIO_S16;
    spec.channels = 2;
    spec.freq = sample_rate;
    stream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,
                                       &spec, NULL, NULL);
    if (stream == NULL) {
        if (audio->owns_subsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
        memset(audio, 0, sizeof(*audio));
        return 0;
    }
    audio->stream = stream;
    audio->sample_rate = sample_rate;
    SDL_AudioSpec device;
    int device_frames;
    if (!SDL_GetAudioDeviceFormat(SDL_GetAudioStreamDevice(stream), &device, &device_frames) ||
        device.freq <= 0 || device_frames <= 0) {
        portable_sdl3_audio_close(audio);
        return 0;
    }
    audio->block_frames = ((uint64_t)device_frames * sample_rate + device.freq-1)/device.freq;
    if (!audio->block_frames || audio->block_frames > INT_MAX/4) {
        portable_sdl3_audio_close(audio); return 0;
    }
    audio->pending = calloc(audio->block_frames, 4);
    audio->recent = calloc(audio->block_frames*AUDIO_TARGET_PERIODS,4);
    if (!audio->pending || !audio->recent) { portable_sdl3_audio_close(audio); return 0; }
    const char *trace=getenv("SIMANT_AUDIO_QUEUE_TRACE");
    if(trace) {
        AudioObservation *o=calloc(1,sizeof(*o));
        if(!o || !(o->file=fopen(trace,"w"))) { free(o);portable_sdl3_audio_close(audio);return 0; }
        audio->observation=o;
        fprintf(o->file,"{\"tag\":\"open\",\"wall_ns\":%llu,\"block_frames\":%zu,\"sample_rate\":%d}\n",(unsigned long long)SDL_GetTicksNS(),audio->block_frames,sample_rate);
    }
    /* Presentation latency only: four device periods absorb producer/consumer
     * phase and host scheduling jitter. No source IRQ is run into the future.
     * Start consumption with the first complete real block, after startup I/O. */
    for (unsigned i=0; i<4; ++i) {
        if (!SDL_PutAudioStreamData(stream, audio->pending, (int)audio->block_frames*4)) {
            portable_sdl3_audio_close(audio); return 0;
        }
    }
    audio->stream_tail=4*audio->block_frames;
    if (!SDL_SetAudioStreamGetCallback(stream, observe_consumption, audio)) {
        portable_sdl3_audio_close(audio);
        return 0;
    }
    return 1;
}

void portable_sdl3_audio_close(PortableSdl3Audio *audio)
{
    if (audio == NULL) return;
    if(audio->stream && audio->observation) portable_sdl3_audio_observe(audio,
        (audio->source_frame/48000)*1000000000+(audio->source_frame%48000)*1000000000/48000);
    if (audio->stream != NULL)
        SDL_DestroyAudioStream((SDL_AudioStream *)audio->stream);
    if(audio->observation) {
        AudioObservation *o=audio->observation;
        for(unsigned i=0;i<o->count;++i) if(!o->markers[i].printed)
            fprintf(o->file,"{\"tag\":\"pending_at_close\",\"id\":%llu}\n",(unsigned long long)o->markers[i].id);
        fclose(o->file);free(o);
    }
    free(audio->pending);
    free(audio->recent);
    if (audio->owns_subsystem) SDL_QuitSubSystem(SDL_INIT_AUDIO);
    memset(audio, 0, sizeof(*audio));
}

int portable_sdl3_audio_queue_frames(PortableSdl3Audio *audio,
                                     const int16_t *pcm, size_t frames)
{ return portable_sdl3_audio_queue_at(audio,pcm,frames,audio?audio->source_frame:0); }
int portable_sdl3_audio_queue_at(PortableSdl3Audio *audio,
                                     const int16_t *pcm, size_t frames,uint64_t first)
{
    size_t pcm_size = frames * 2 * sizeof(int16_t);
    if (audio == NULL || audio->stream == NULL ||
        (pcm == NULL && pcm_size != 0) || pcm_size > INT_MAX)
        return 0;
    if (pcm_size == 0) return 1;
    while (frames) {
        size_t count = audio->block_frames - audio->pending_frames;
        if (count > frames) count = frames;
        memcpy(audio->pending + audio->pending_frames*2, pcm, count*4);
        if(audio->observation && !audio->gated) {
            AudioObservation *o=audio->observation;
            SDL_LockAudioStream(audio->stream);
            for(unsigned i=0;i<o->count;++i) {
                AudioMarker *m=&o->markers[i];
                if(!m->submitted && m->source_frame<first+count) {
                    m->epoch=audio->stream_epoch;
                    m->offset=audio->stream_tail+audio->pending_frames+(m->source_frame>first?m->source_frame-first:0);
                    m->submitted=1;
                }
            }
            SDL_UnlockAudioStream(audio->stream);
        }
        audio->pending_frames += count; pcm += count*2; frames -= count;
        first+=count;audio->source_frame=first;
        if (audio->pending_frames == audio->block_frames) {
            const size_t target=audio->block_frames*AUDIO_TARGET_PERIODS;
            memcpy(audio->recent+audio->recent_cursor*2,audio->pending,audio->block_frames*4);
            audio->recent_cursor=(audio->recent_cursor+audio->block_frames)%target;
            audio->recent_frames+=audio->block_frames;if(audio->recent_frames>target) audio->recent_frames=target;
            audio->recent_end=audio->source_frame;
            if(audio->gated) { audio->gated_frames+=audio->block_frames;audio->pending_frames=0;continue; }
            uint64_t started = SDL_GetTicksNS();
            SDL_LockAudioStream(audio->stream);
            if (!SDL_PutAudioStreamData(audio->stream, audio->pending, (int)audio->block_frames*4)) { SDL_UnlockAudioStream(audio->stream);return 0; }
            audio->stream_tail+=audio->block_frames;
            SDL_UnlockAudioStream(audio->stream);
            audio->submission_ns += SDL_GetTicksNS() - started;
            ++audio->queue_calls; audio->queued_frames += audio->block_frames;
            audio->pending_frames = 0;
            if (!audio->started) {
                if (!SDL_ResumeAudioStreamDevice(audio->stream)) return 0;
                audio->started = 1;
            }
        }
    }
    return audio->timeline?1:portable_sdl3_audio_service(audio);
}
