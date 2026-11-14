/* Readable hardware ISR projection of src/sound/sample_timer.asm. No private voice
 * copy: completion clears the same snd field consumed by canonical m295C. */
#include "whole_audio_provider.h"
#include "audio_native.h"
#include "audio_state.h"
#include "audio.h"
#include "portable/audio/isa_devices.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
static PortableWholeAudioProvider *replay_provider;
extern uint8_t portable_canonical_volume_tables[2048];
extern int16_t snd_song_process_due_events(void);
int portable_whole_audio_provider_init(PortableWholeAudioProvider *p) {
    memset(p,0,sizeof(*p));replay_provider=p;p->mix_divider=16;p->devices=sim_isa_audio_create();
    return p->devices!=NULL;
}
void portable_whole_audio_provider_close(PortableWholeAudioProvider *p) {
    if(replay_provider==p) replay_provider=NULL;
    sim_isa_audio_destroy(p->devices);memset(p,0,sizeof(*p));
}
void portable_whole_audio_provider_configure(PortableWholeAudioProvider *p,uint16_t divisor,uint16_t chain,unsigned channels) {
    p->divisor=divisor;p->chain=chain;p->channels=channels;
}
static void next_interrupt(PortableWholeAudioProvider *p,unsigned factor) {
    uint64_t numerator=p->irq_fraction+(uint64_t)p->divisor*factor*12*UINT64_C(1000000000);
    p->irq_ns+=numerator/UINT64_C(14318180);
    p->irq_fraction=numerator%UINT64_C(14318180);
}
void portable_whole_audio_provider_start(PortableWholeAudioProvider *p) {
    /* m03CC reloads PIT0 and reinstalls the fast ISR on every sample start. */
    p->fast=1;p->armed=1;
    ++p->timer_generation;
    p->irq_ns=p->time_ns;p->irq_fraction=0;next_interrupt(p,1);
}
void portable_whole_audio_provider_stop(PortableWholeAudioProvider *p) { p->armed=0;p->pending_irq=0; }
static void sequencer(void) {
    midi_service_countdown=(int16_t)((uint16_t)midi_service_countdown-1);
    if(midi_service_countdown==0) midi_service_countdown=snd_song_process_due_events();
}
static void interrupt(PortableWholeAudioProvider *p,unsigned reentrant) {
    /* Fast entry's busy guard acknowledges a nested IRQ without advancing
     * channels or the sequencer. Normal host callbacks cannot nest. */
    if(reentrant) return;
    unsigned ch,sum=0;int active=0,skip=0;
    if(!p->fast) { sequencer();return; }
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
            unsigned row=(uint16_t)(c->voltab-snd_volume_table_offset)>>8;
            if(row>7) { fprintf(stderr,"Unsupported canonical volume table row %u\n",row);abort(); }
            sample=portable_canonical_volume_tables[row*256+((uint8_t *)*c->snd->data)[c->pos]];
        }
        sum+=sample;
    }
    if(!skip) {
        uint8_t mixed=(uint8_t)(sum/p->channels);
        if(snd_sample_output_routine==snd_sb_output_pointer) {
            while(dos_audio_host_in8((uint16_t)snd_sb_dsp_write_port)&0x80) {}
            dos_audio_host_out8((uint16_t)snd_sb_dsp_write_port,0x10);
            while(dos_audio_host_in8((uint16_t)snd_sb_dsp_write_port)&0x80) {}
            dos_audio_host_out8((uint16_t)snd_sb_dsp_write_port,mixed);
        } else { fprintf(stderr,"Unsupported canonical audio output selector (native device profile is Sound Blaster)\n");exit(70); }
    }
    if(--p->mix_divider==0) { p->mix_divider=16;sequencer(); }
    /* STD marks at least one live sample. Original L0148 switches to slow
     * PIT/ISR only when DF remains clear and the divider did not hit zero. */
    else if(!active) p->fast=0;
}
/* Run the existing translated canonical ISR at a recorded service boundary.
 * The observed fast/slow identity is checked, never installed as native state. */
void portable_whole_audio_replay_interrupt(unsigned fast) {
    PortableWholeAudioProvider *p=replay_provider;
    if(!p || !p->armed || p->in_render) { fprintf(stderr,"Audio replay has no armed timer\n");abort(); }
    /* A nested fast IRQ runs the original busy early exit: PIC acknowledgement
     * only, with no channel/sequencer/device-write effects. Its nesting is
     * observed schedule input, not inferred from expected sound state. */
    if(fast<2 && (unsigned)p->fast!=fast) {
        static unsigned reports;
        if(reports++<8) fprintf(stderr,"Audio timer mode differs: DOS=%u native=%u\n",fast,(unsigned)p->fast);
    }
    p->in_render=1;interrupt(p,fast==2);p->in_render=0;
}
void portable_whole_audio_provider_enable_interrupts(PortableWholeAudioProvider *p) {
    /* PIC IRQ0 coalesces edges while IF is clear. Source callbacks cannot
     * reenter the private sequencer stack in this single-thread projection. */
    if(!getenv("SIMANT_TEST_AUDIO_TIMER") && p->armed && p->pending_irq && !p->in_render) {
        p->pending_irq=0;p->in_render=1;interrupt(p,0);p->in_render=0;
    }
}
void portable_whole_audio_provider_render_frame(PortableWholeAudioProvider *p,int16_t stereo[2]) {
    if(portable_whole_audio_interrupts_enabled()) portable_whole_audio_provider_enable_interrupts(p);
    ++p->frame_cursor;
    uint64_t target=(p->frame_cursor/48000)*UINT64_C(1000000000)+
                    (p->frame_cursor%48000)*UINT64_C(1000000000)/48000;
    p->in_render=1;
    while(!getenv("SIMANT_TEST_AUDIO_TIMER") && p->armed && p->irq_ns<=target) {
        unsigned generation=p->timer_generation;
        p->time_ns=p->irq_ns;
        if(portable_whole_audio_interrupts_enabled()) interrupt(p,0);
        else p->pending_irq=1;
        if(generation==p->timer_generation) next_interrupt(p,p->fast?1:16);
    }
    p->time_ns=target;sim_isa_audio_render(p->devices,stereo,target);p->in_render=0;
}
