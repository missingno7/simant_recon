#include "portable/whole_program/platform/whole_audio_provider.h"
#include "portable/whole_program/platform/audio_native.h"
#include "portable/whole_program/platform/audio.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/audio/native_renderer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <windows.h>
#undef assert
#define assert(expr) do { if (!(expr)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#expr);exit(1); } } while(0)
/* Test-owned canonical externs. The production program uses only source owners. */
PortableWholeAudioRuntimeSample snd_sample_channel_records[4];
uint8_t portable_canonical_volume_tables[2048];
uint16_t snd_volume_table_offset=0x6ca3;
int16_t midi_service_countdown=100,snd_sample_output_routine=5,snd_sb_dsp_write_port=0x22c;
int16_t snd_speaker_output_pointer=1,snd_sb_output_pointer=5;
static unsigned sequencer_calls,writes;
static int restart_in_sequencer;
static uint8_t values[8192];
int16_t snd_song_process_due_events(void) { ++sequencer_calls;if(restart_in_sequencer) snd_start_sample_timer();return 2; }
static void configure(void *ctx,uint16_t d,uint16_t c,unsigned n) { portable_whole_audio_provider_configure(ctx,d,c,n); }
static void start(void *ctx) { portable_whole_audio_provider_start(ctx); }
static void stop(void *ctx) { portable_whole_audio_provider_stop(ctx); }
static void enable(void *ctx) { portable_whole_audio_provider_enable_interrupts(ctx); }
static void opl_event(void *ctx,uint8_t r,uint8_t v) { portable_whole_audio_provider_opl(ctx,r,v); }
static void enable_samples(void *ctx,int enabled) { portable_whole_audio_provider_sample_enable(ctx,enabled); }
void portable_test_audio_mix(unsigned a,unsigned b) {
    assert(writes+2<=sizeof(values));values[writes++]=0x10;values[writes++]=(a+b)/2;
}
static int16_t rendered[2];
static void frames(PortableWholeAudioProvider *p,unsigned n) { while(n--) portable_whole_audio_provider_render_frame(p,rendered); }
static void fm(void *d,uint8_t r,uint8_t v,uint64_t t) { sim_audio_opl(d,t,r,v); }
int main(int argc,char **argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc>1) {
        if(!strcmp(argv[1],"--invalid-position") || !strcmp(argv[1],"--invalid-volume")) {
            uint8_t b[2]={128,255};uint16_t pos[4]={2};uint8_t vol[4]={0};int16_t pcm[2];
            SimAudioVoice v={14,2,256,0,0,0,0,0,0,b};
            if(!strcmp(argv[1],"--invalid-volume")) v.volume=8;
            void *d=sim_audio_create(portable_canonical_volume_tables);
            sim_audio_voice_start(d,0,0,&v);sim_audio_positions(d,0,2,pos,vol,1);sim_audio_commit(d,0);
            sim_audio_render(d,pcm,1,0);return 1;
        }
        if(!strcmp(argv[1],"--backward-event")) {
            void *d=sim_audio_create(portable_canonical_volume_tables);
            sim_audio_opl(d,2,0,0);sim_audio_opl(d,1,0,0);return 1;
        }
        PortableWholeAudioHost unsupported={NULL,configure,start,stop,opl_event,enable_samples,enable,NULL};
        assert(portable_whole_audio_bind(&unsupported));
        dos_audio_host_out8(0x22c,0x14);
        return 1;
    }
    PortableWholeAudioProvider p;
    assert(portable_whole_audio_provider_init(&p));
    PortableWholeAudioHost host={&p,configure,start,stop,opl_event,enable_samples,enable,NULL};
    assert(portable_whole_audio_bind(&host));
    for(unsigned i=0;i<2048;++i) portable_canonical_volume_tables[i]=(uint8_t)i;
    snd_select_two_channel_timer(214,306);snd_start_sample_timer();
    /* Inactive mixer emits one neutral DSP sample then switches to slow PIT.
     * The song divider advances only on each slow IRQ (3424 PIT clocks). */
    frames(&p,2000);
    assert(writes==2 && values[0]==0x10 && values[1]==128);
    assert(p.fast==0 && midi_service_countdown==86); // 14 slow ticks by 41.666 ms
    dos_audio_host_interrupt_disable();frames(&p,500);
    assert(p.pending_irq==1 && midi_service_countdown==86);
    dos_audio_host_interrupt_enable();
    assert(!p.pending_irq && midi_service_countdown==85); // one coalesced IRQ, not a burst
    snd_restore_bios_timer(0);
    memset(snd_sample_channel_records,0,sizeof(snd_sample_channel_records));writes=0;
    uint8_t bytes[]={128,240,32,64,128};char *payload=(char *)bytes;
    PortableWholeAudioSample sample={0};sample.data=&payload;sample.len=5;
    snd_sample_channel_records[0].snd=&sample;snd_sample_channel_records[0].owner=&sample;
    snd_sample_channel_records[0].step=256;snd_sample_channel_records[0].end=3;
    snd_sample_channel_records[0].voltab=snd_volume_table_offset;
    portable_whole_audio_provider_set_rendering(&p,1);
    portable_whole_audio_provider_sample_enable(&p,1);
    snd_start_sample_timer();frames(&p,40);
    /* Three source samples; the fourth over-end interrupt has no OUT and
     * clears canonical snd, retaining owner until the source allocator frees it. */
    assert(snd_sample_channel_records[0].snd==NULL && snd_sample_channel_records[0].owner==&sample);
    assert(writes==6 && values[1]==184 && values[3]==80 && values[5]==96);
    assert(snd_sample_channel_records[0].pos==4);
    assert(rendered[0]==-8192 && rendered[1]==-8192); // held final contribution on skipped output
    frames(&p,20);assert(writes==8 && !rendered[0] && !rendered[1]); // next inactive interrupt outputs neutral
    portable_whole_audio_provider_set_rendering(&p,0);
    snd_restore_bios_timer(0);
    writes=0;snd_sample_channel_records[0].snd=&sample;snd_sample_channel_records[0].step=1;
    snd_sample_channel_records[0].pos=0;snd_sample_channel_records[0].frac=0;
    p.mix_divider=16;midi_service_countdown=1;restart_in_sequencer=1;
    snd_start_sample_timer();unsigned generation=p.timer_generation;frames(&p,138);
    assert(p.timer_generation>generation && p.irq_ns>p.time_ns && p.irq_ns-p.time_ns<180000);
    restart_in_sequencer=0;snd_restore_bios_timer(0);
    p.time_ns=UINT64_C(7200000000000);snd_start_sample_timer();
    assert(p.irq_ns>p.time_ns && p.irq_ns-p.time_ns<180000); // two-hour clock must not overflow
    snd_restore_bios_timer(0);portable_whole_audio_unbind();
    portable_whole_audio_provider_close(&p);
    /* Native voice events copy payloads, hold source positions, apply volume,
     * mix inactive channels at 128 and never play future events early. */
    void *d=sim_audio_create(portable_canonical_volume_tables);int16_t pcm[9600];
    uint8_t native_bytes[]={128,192,255,0};
    SimAudioVoice v={14,4,256,2,2,0,0,0,0,native_bytes};
    sim_audio_enable(d,0,1);sim_audio_voice_start(d,0,0,&v);
    uint16_t pos[4]={1,0,0,0};uint8_t vol[4]={0};
    sim_audio_positions(d,10000000,2,pos,vol,1);sim_audio_commit(d,10000000);
    native_bytes[1]=0; // producer may free/mutate immediately after start
    sim_audio_render(d,pcm,480,0);assert(!pcm[958]);
    sim_audio_render(d,pcm,1,480);assert(pcm[0]==8192 && pcm[1]==8192);
    sim_audio_enable(d,10001000,0);sim_audio_render(d,pcm,1,481);assert(!pcm[0]);
    sim_audio_destroy(d);
    /* Same OPL2 keyed tone and key-off controls, now with direct registers. */
    d=sim_audio_create(portable_canonical_volume_tables);
    fm(d,0x20,0x21,0);fm(d,0x23,0x21,0);fm(d,0x40,63,0);fm(d,0x43,0,0);
    fm(d,0x60,0xf0,0);fm(d,0x63,0xf0,0);fm(d,0x80,0x0f,0);fm(d,0x83,0x0f,0);
    fm(d,0xc0,0,0);fm(d,0xa0,0x98,0);fm(d,0xb0,0x31,0);
    sim_audio_render(d,pcm,4800,0);
    unsigned audible=0;for(unsigned i=0;i<4800;++i) if(pcm[2*i] || pcm[2*i+1]) ++audible;
    assert(audible>4000);
    fm(d,0xb0,0x11,100000000);
    for(unsigned i=4800;i<48000;i+=4800) sim_audio_render(d,pcm,4800,i);
    assert(!pcm[9598] && !pcm[9599]);sim_audio_destroy(d);
    /* Renderer must not invent sample progression. Fractional rate and loop
     * metadata alone produce no movement; only source position events do. */
    d=sim_audio_create(portable_canonical_volume_tables);
    native_bytes[1]=192;v.step=384;v.flags=128;v.loop=1;
    sim_audio_enable(d,0,1);sim_audio_voice_start(d,0,0,&v);
    pos[0]=1;sim_audio_positions(d,0,2,pos,vol,1);sim_audio_commit(d,0);
    sim_audio_render(d,pcm,4800,0);
    assert(pcm[0]==8192 && pcm[9598]==8192);
    /* Four-channel overlap and original integer averaging. */
    sim_audio_voice_start(d,100000000,1,&v);
    pos[0]=pos[1]=2;sim_audio_positions(d,100000000,4,pos,vol,3);sim_audio_commit(d,100000000);
    sim_audio_render(d,pcm,1,4800);assert(pcm[0]==16128); // floor((255+255+128+128)/4)
    sim_audio_destroy(d);
    puts("PASS: canonical ISR cadence/completion; native payload copy, magnitude/mute, future events; direct OPL tone/key-off");
    return 0;
}
