#include "portable/whole_program/platform/whole_audio_provider.h"
#include "portable/whole_program/platform/audio_native.h"
#include "portable/whole_program/platform/audio.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/audio/isa_devices.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <windows.h>
#undef assert
#define assert(expr) do { if (!(expr)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#expr);exit(1); } } while(0)
/* Test-owned canonical externs. The production program uses only source owners. */
PortableWholeAudioRuntimeSample fd_55B3_6B4C[4];
uint8_t portable_canonical_volume_tables[2048];
uint16_t fd_55B3_6B9E=0x6ca3;
int16_t fd_55B3_6B42=100,fd_55B3_6B9C=5,fd_55B3_6BA0=0x22c;
int16_t fd_55B3_74AD=1,fd_55B3_74B5=5;
static unsigned sequencer_calls,writes;
static int restart_in_sequencer;
static uint8_t values[8192];
int16_t f_284A_067F(void) { ++sequencer_calls;if(restart_in_sequencer) f_28BC_03CC();return 2; }
static void configure(void *ctx,uint16_t d,uint16_t c,unsigned n) { portable_whole_audio_provider_configure(ctx,d,c,n); }
static void start(void *ctx) { portable_whole_audio_provider_start(ctx); }
static void stop(void *ctx) { portable_whole_audio_provider_stop(ctx); }
static void enable(void *ctx) { portable_whole_audio_provider_enable_interrupts(ctx); }
static void out(void *ctx,uint16_t port,uint8_t value) {
    PortableWholeAudioProvider *p=ctx;
    if(port==0x22c) { assert(writes<sizeof(values));values[writes++]=value; }
    sim_isa_audio_out(p->devices,port,value,p->time_ns);
}
static uint8_t in(void *ctx,uint16_t port) { PortableWholeAudioProvider *p=ctx;return sim_isa_audio_in(p->devices,port,p->time_ns); }
static void frames(PortableWholeAudioProvider *p,unsigned n) { int16_t stereo[2];while(n--) portable_whole_audio_provider_render_frame(p,stereo); }
static void fm(void *d,uint8_t r,uint8_t v,uint64_t t) { sim_isa_audio_out(d,0x388,r,t);sim_isa_audio_out(d,0x389,v,t); }
int main(int argc,char **argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    (void)argv;
    if(argc>1) {
        void *unsupported=sim_isa_audio_create();
        sim_isa_audio_out(unsupported,0x22c,0x14,0);
        return 1;
    }
    PortableWholeAudioProvider p;
    assert(portable_whole_audio_provider_init(&p));
    PortableWholeAudioHost host={&p,configure,start,stop,out,in,enable};
    assert(portable_whole_audio_bind(&host));
    for(unsigned i=0;i<2048;++i) portable_canonical_volume_tables[i]=(uint8_t)i;
    f_28BC_0488(214,306);f_28BC_03CC();
    /* Inactive mixer emits one neutral DSP sample then switches to slow PIT.
     * The song divider advances only on each slow IRQ (3424 PIT clocks). */
    frames(&p,2000);
    assert(writes==2 && values[0]==0x10 && values[1]==128);
    assert(p.fast==0 && fd_55B3_6B42==86); // 14 slow ticks by 41.666 ms
    dos_audio_host_interrupt_disable();frames(&p,500);
    assert(p.pending_irq==1 && fd_55B3_6B42==86);
    dos_audio_host_interrupt_enable();
    assert(!p.pending_irq && fd_55B3_6B42==85); // one coalesced IRQ, not a burst
    f_28BC_04E0(0);
    memset(fd_55B3_6B4C,0,sizeof(fd_55B3_6B4C));writes=0;
    uint8_t bytes[]={128,240,32,64,128};char *payload=(char *)bytes;
    PortableWholeAudioSample sample={0};sample.data=&payload;sample.len=5;
    fd_55B3_6B4C[0].snd=&sample;fd_55B3_6B4C[0].owner=&sample;
    fd_55B3_6B4C[0].step=256;fd_55B3_6B4C[0].end=3;
    fd_55B3_6B4C[0].voltab=fd_55B3_6B9E;
    f_28BC_03CC();frames(&p,40);
    /* Three source samples; the fourth over-end interrupt has no OUT and
     * clears canonical snd, retaining owner until the source allocator frees it. */
    assert(fd_55B3_6B4C[0].snd==NULL && fd_55B3_6B4C[0].owner==&sample);
    assert(writes==6 && values[1]==184 && values[3]==80 && values[5]==96);
    assert(fd_55B3_6B4C[0].pos==4);
    frames(&p,20);assert(writes==8); // next inactive interrupt outputs neutral
    f_28BC_04E0(0);
    writes=0;fd_55B3_6B4C[0].snd=&sample;fd_55B3_6B4C[0].step=1;
    fd_55B3_6B4C[0].pos=0;fd_55B3_6B4C[0].frac=0;
    p.mix_divider=16;fd_55B3_6B42=1;restart_in_sequencer=1;
    f_28BC_03CC();unsigned generation=p.timer_generation;frames(&p,138);
    assert(p.timer_generation>generation && p.irq_ns>p.time_ns && p.irq_ns-p.time_ns<180000);
    restart_in_sequencer=0;f_28BC_04E0(0);
    p.time_ns=UINT64_C(7200000000000);f_28BC_03CC();
    assert(p.irq_ns>p.time_ns && p.irq_ns-p.time_ns<180000); // two-hour clock must not overflow
    f_28BC_04E0(0);portable_whole_audio_unbind();
    /* Direct DSP commands preserve unsigned 8-bit DAC magnitude and mute. */
    sim_isa_audio_destroy(p.devices);p.devices=sim_isa_audio_create();
    void *d=p.devices;int16_t s[2];
    sim_isa_audio_out(d,0x226,1,0);sim_isa_audio_out(d,0x226,0,1000);
    assert(sim_isa_audio_in(d,0x22e,1000)==0x80);
    assert(sim_isa_audio_in(d,0x22a,1000)==0xaa);
    sim_isa_audio_out(d,0x22c,0xd1,2000);sim_isa_audio_out(d,0x22c,0x10,2000);
    sim_isa_audio_out(d,0x22c,160,2000);sim_isa_audio_render(d,s,3000);
    assert(s[0]==8192 && s[1]==8192);
    assert(sim_isa_audio_in(d,0x22e,3000)==0 && sim_isa_audio_in(d,0x22a,3000)==0xff);
    sim_isa_audio_out(d,0x22c,0xd3,4000);sim_isa_audio_render(d,s,5000);
    assert(!s[0] && !s[1]);
    sim_isa_audio_out(d,0x22c,0xd1,10000000);sim_isa_audio_out(d,0x22c,0x10,10000000);
    sim_isa_audio_out(d,0x22c,160,10000000);
    sim_isa_audio_render(d,s,9999000);assert(!s[0] && !s[1]); // future OUT not audible early
    sim_isa_audio_render(d,s,10000000);assert(s[0]==8192 && s[1]==8192);
    sim_isa_audio_out(d,0x22c,0xd3,10001000);
    /* OPL positive and negative controls: timer status, keyed tone, key-off. */
    fm(d,4,0x80,10002000);assert((sim_isa_audio_in(d,0x388,10002000)&0xe0)==0);
    fm(d,2,255,10002000);fm(d,4,0x21,10002000);
    assert((sim_isa_audio_in(d,0x388,11000000)&0xe0)==0xc0);
    fm(d,4,0x80,11000000);assert((sim_isa_audio_in(d,0x388,11000000)&0xe0)==0);
    sim_isa_audio_destroy(d);d=sim_isa_audio_create();p.devices=d;
    fm(d,0x20,0x21,0);fm(d,0x23,0x21,0);fm(d,0x40,63,0);fm(d,0x43,0,0);
    fm(d,0x60,0xf0,0);fm(d,0x63,0xf0,0);fm(d,0x80,0x0f,0);fm(d,0x83,0x0f,0);
    fm(d,0xc0,0,0);fm(d,0xa0,0x98,0);fm(d,0xb0,0x31,0);
    unsigned audible=0;
    for(unsigned i=1;i<4800;++i) { sim_isa_audio_render(d,s,(uint64_t)i*1000000000/48000);if(s[0]||s[1])++audible; }
    assert(audible>4000);
    fm(d,0xb0,0x11,100000000);
    for(unsigned i=4800;i<48000;++i) sim_isa_audio_render(d,s,(uint64_t)i*1000000000/48000);
    assert(!s[0] && !s[1]);
    portable_whole_audio_provider_close(&p);
    puts("PASS: canonical ISR cadence/completion, DSP DAC magnitude/mute, OPL timer/tone/key-off");
    return 0;
}
