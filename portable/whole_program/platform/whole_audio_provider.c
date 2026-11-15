/* Logical ISR projection of src/sound/sample_timer.asm. Completion clears the
 * canonical snd field consumed by m295C; observed[] only caches event delivery.
 * PCM and FM synthesis cannot update this source state or the PIT schedule. */
#include "whole_audio_provider.h"
#include "audio_native.h"
#include "audio_state.h"
#include "audio.h"
#include "portable/audio/native_renderer.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
extern void portable_test_audio_mix(unsigned,unsigned) __attribute__((weak));
extern void portable_test_audio_tick(unsigned) __attribute__((weak));
extern void portable_test_audio_progress(unsigned) __attribute__((weak));
static PortableWholeAudioProvider *active_provider;
extern uint8_t portable_canonical_volume_tables[2048];
extern int16_t snd_song_process_due_events(void);
int portable_whole_audio_isr_active(void) {
    return active_provider && active_provider->in_render;
}
int portable_whole_audio_provider_init(PortableWholeAudioProvider *p) {
    memset(p,0,sizeof(*p));active_provider=p;p->mix_divider=16;
    return 1;
}
void portable_whole_audio_provider_close(PortableWholeAudioProvider *p) {
    if(active_provider==p) active_provider=NULL;
    sim_audio_destroy(p->renderer);memset(p,0,sizeof(*p));
}
void portable_whole_audio_provider_set_rendering(PortableWholeAudioProvider *p,int enabled) {
    if(enabled && !p->renderer) {
        p->renderer=sim_audio_create(portable_canonical_volume_tables);
        sim_audio_enable(p->renderer,p->time_ns,p->sample_enabled);
        portable_whole_audio_provider_sync_samples(p,1);
    } else if(!enabled && p->renderer) { sim_audio_destroy(p->renderer);p->renderer=NULL; }
}
void portable_whole_audio_provider_opl(PortableWholeAudioProvider *p,uint8_t reg,uint8_t value) {
    if(p->playback_observer && reg>=0xb0 && reg<=0xb8 && (value&0x20))
        p->playback_observer(p->playback_observer_context,p->time_ns,PORTABLE_AUDIO_OPL_KEY_ON,reg-0xb0,value);
    if(p->renderer) sim_audio_opl(p->renderer,p->time_ns,reg,value);
}
void portable_whole_audio_provider_sample_enable(PortableWholeAudioProvider *p,int enabled) {
    p->sample_enabled=enabled;
    if(p->renderer) sim_audio_enable(p->renderer,p->time_ns,enabled);
}
void portable_whole_audio_provider_sync_samples(PortableWholeAudioProvider *p,int restart) {
    if(!p->renderer) return;
    for(unsigned ch=0;ch<p->channels;++ch) {
        PortableWholeAudioRuntimeSample *c=&snd_sample_channel_records[ch],*old=&p->observed[ch];
        if(c->snd && c->snd->data && *c->snd->data) {
            if(restart || c->snd!=old->snd || c->step!=old->step || c->end!=old->end ||
               c->start!=old->start || c->flags!=old->flags || (c->pos==0 && old->pos!=0)) {
                SimAudioVoice v={(uint16_t)c->snd->object,c->snd->len,c->step,c->end,c->start,c->pos,
                    c->frac,c->flags,(uint16_t)(c->voltab-snd_volume_table_offset)>>8,(uint8_t *)*c->snd->data};
                sim_audio_voice_start(p->renderer,p->time_ns,ch,&v);
                if(p->playback_observer && (!old->snd || c->snd!=old->snd || (c->pos==0 && old->pos!=0))) {
                    p->observation_pending|=1u<<ch;
                    p->playback_observer(p->playback_observer_context,p->time_ns,PORTABLE_AUDIO_SAMPLE_SETUP,ch,(uint16_t)c->snd->object);
                }
            }
        } else if(old->snd) {
            sim_audio_voice_stop(p->renderer,p->time_ns,ch);
            p->observation_pending&=~(1u<<ch);
            if(p->playback_observer) p->playback_observer(p->playback_observer_context,p->time_ns,PORTABLE_AUDIO_SAMPLE_STOP,ch,0);
        }
        *old=*c;
    }
}
void portable_whole_audio_provider_configure(PortableWholeAudioProvider *p,uint16_t divisor,uint16_t chain,unsigned channels) {
    p->divisor=divisor;p->chain=chain;p->channels=channels;
}
static void next_interrupt(PortableWholeAudioProvider *p,unsigned factor) {
    uint64_t numerator=p->irq_fraction+(uint64_t)p->divisor*factor*12*UINT64_C(1000000000);
    p->irq_ns+=numerator/UINT64_C(14318180);
    p->irq_fraction=numerator%UINT64_C(14318180);
}
static void timer_event(PortableWholeAudioProvider *p,unsigned event) {
    if(p->timer_observer) p->timer_observer(p->timer_observer_context,p->time_ns,event,
        p->fast?p->divisor:(uint32_t)p->divisor*16,
        p->fast?p->chain:p->chain>>4,p->chain_remaining);
}
/* Mode 3 is high for the first half and low for the second. A control/count
 * reload forces OUT high; its rising edge remains pending while source IF is
 * clear. irq_fraction locates the next edge exactly, without ns rounding. */
static int pit_output_low(const PortableWholeAudioProvider *p) {
    if(!p->armed || p->in_render) return 0;
    uint64_t period=(uint64_t)p->divisor*(p->fast?1:16)*12*UINT64_C(1000000000);
    uint64_t remaining=(p->irq_ns-p->time_ns)*UINT64_C(14318180)+p->irq_fraction;
    return remaining && remaining*2<=period;
}
void portable_whole_audio_provider_start(PortableWholeAudioProvider *p) {
    portable_whole_audio_provider_sync_samples(p,1);
    /* m03CC reloads PIT0 and reinstalls the fast ISR on every sample start. */
    if(pit_output_low(p)) p->pending_irq=1;
    p->fast=1;p->armed=1;p->chain_remaining=1;
    ++p->timer_generation;
    p->irq_ns=p->time_ns;p->irq_fraction=0;next_interrupt(p,1);
    timer_event(p,1);
}
void portable_whole_audio_provider_stop(PortableWholeAudioProvider *p) {
    timer_event(p,3);p->armed=0;p->pending_irq=0;
}
static void chain_timer(PortableWholeAudioProvider *p) {
    if(--p->chain_remaining==0) {
        p->chain_remaining=p->fast?p->chain:p->chain>>4;
        timer_event(p,2);
    }
}
static void sequencer(void) {
    midi_service_countdown=(int16_t)((uint16_t)midi_service_countdown-1);
    if(midi_service_countdown==0) midi_service_countdown=snd_song_process_due_events();
}
static void interrupt(PortableWholeAudioProvider *p) {
    unsigned contributions[4]={128,128,128,128};
    unsigned ch;int active=0,skip=0;
    if(!p->fast) { sequencer();chain_timer(p);return; }
    for(ch=0;ch<p->channels;++ch) {
        PortableWholeAudioRuntimeSample *c=&snd_sample_channel_records[ch];
        unsigned sample=128;
        if(c->snd && c->snd->data && *c->snd->data) {
            uint16_t phase=(uint16_t)(c->frac+c->step);
            active=1;c->frac=(uint8_t)phase;
            c->pos=(uint16_t)(c->pos+(phase>>8));
            if(c->pos>c->end) {
                if(c->flags&0x80) c->pos=c->start;
                else c->snd=NULL;
                skip=1;break; // L00C5 skips output and later channels only
            }
            /* Payload/attenuation observation is optional. Production logical
             * IRQ work only advances source state; the renderer mixes voices. */
            if(portable_test_audio_mix) {
                unsigned row=(uint16_t)(c->voltab-snd_volume_table_offset)>>8;
                if(row>7) { fprintf(stderr,"Unsupported canonical volume table row %u\n",row);abort(); }
                sample=portable_canonical_volume_tables[row*256+((uint8_t *)*c->snd->data)[c->pos]];
            }
        }
        contributions[ch]=sample;
    }
    if(!skip) {
        if(portable_test_audio_mix && p->channels==2) portable_test_audio_mix(contributions[0],contributions[1]);
        if(snd_sample_output_routine!=snd_sb_output_pointer) { fprintf(stderr,"Unsupported canonical audio output selector (native profile is mode 6)\n");exit(70); }
    }
    if(p->renderer) {
        uint16_t positions[4]={0};uint8_t volumes[4]={0};unsigned mask=0;
        portable_whole_audio_provider_sync_samples(p,0);
        for(ch=0;ch<p->channels;++ch) {
            PortableWholeAudioRuntimeSample *c=&snd_sample_channel_records[ch];
            positions[ch]=c->pos;volumes[ch]=(uint16_t)(c->voltab-snd_volume_table_offset)>>8;
            if(c->snd && c->snd->data && *c->snd->data) mask|=1u<<ch;
        }
        sim_audio_positions(p->renderer,p->time_ns,p->channels,positions,volumes,mask);
        if(!skip) {
            sim_audio_commit(p->renderer,p->time_ns);
            if(p->playback_observer) for(ch=0;ch<p->channels;++ch) if((p->observation_pending&mask)&(1u<<ch)) {
                p->playback_observer(p->playback_observer_context,p->time_ns,PORTABLE_AUDIO_SAMPLE_EMISSION,ch,(uint16_t)snd_sample_channel_records[ch].snd->object);
                p->observation_pending&=~(1u<<ch);
            }
        }
    }
    if(--p->mix_divider==0) { p->mix_divider=16;sequencer(); }
    /* STD marks at least one live sample. Original L0148 switches to slow
     * PIT/ISR only when DF remains clear and the divider did not hit zero. */
    else if(!active) {
        p->fast=0;p->chain_remaining=(p->chain_remaining>>4)+1;
        timer_event(p,1);return; /* L0428 returns without decrementing g_74A3. */
    }
    chain_timer(p);
}
void portable_whole_audio_provider_enable_interrupts(PortableWholeAudioProvider *p) {
    /* PIC IRQ0 coalesces edges while IF is clear. Source callbacks cannot
     * reenter the private sequencer stack in this single-thread projection. */
    if(p->armed && p->pending_irq && !p->in_render) {
        unsigned generation=p->timer_generation;int was_fast=p->fast;
        p->pending_irq=0;p->in_render=1;
        if(portable_test_audio_tick) portable_test_audio_tick(p->fast?1:0);
        interrupt(p);
        if(generation==p->timer_generation && was_fast && !p->fast) {
            p->irq_ns=p->time_ns;p->irq_fraction=0;next_interrupt(p,16);
        }
        if(portable_test_audio_progress) portable_test_audio_progress(0);
        p->in_render=0;
    }
}
void portable_whole_audio_provider_render_frame(PortableWholeAudioProvider *p,int16_t stereo[2]) {
    if(portable_whole_audio_interrupts_enabled()) portable_whole_audio_provider_enable_interrupts(p);
    ++p->frame_cursor;
    uint64_t target=(p->frame_cursor/48000)*UINT64_C(1000000000)+
                    (p->frame_cursor%48000)*UINT64_C(1000000000)/48000;
    portable_whole_audio_provider_advance(p,target);
    portable_whole_audio_provider_render(p,stereo,1,p->frame_cursor);
}
void portable_whole_audio_provider_render(PortableWholeAudioProvider *p,int16_t *pcm,size_t count,uint64_t first) {
    if(p->renderer) sim_audio_render(p->renderer,pcm,count,first);
    else memset(pcm,0,count*2*sizeof(*pcm));
}
void portable_whole_audio_provider_advance(PortableWholeAudioProvider *p,uint64_t target) {
    if(target<p->time_ns) return;
    p->in_render=1;
    while(p->armed && (p->irq_ns<target || (p->irq_ns==target && !p->irq_fraction))) {
        unsigned generation=p->timer_generation;
        p->time_ns=p->irq_ns;
        timer_event(p,0);
        if(portable_whole_audio_interrupts_enabled()) {
            if(portable_test_audio_tick) portable_test_audio_tick(p->fast?1:0);
            interrupt(p);
            if(portable_test_audio_progress) portable_test_audio_progress(0);
        }
        else p->pending_irq=1;
        if(generation==p->timer_generation) next_interrupt(p,p->fast?1:16);
    }
    p->time_ns=target;timer_event(p,0);p->in_render=0;
}
