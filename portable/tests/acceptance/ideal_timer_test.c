/* Actual translated ISR, with test-owned canonical globals/device services.
 * Independent rational expected event times catch an omitted slow notification. */
#define main device_baseline_main
#include "../audio/device_boundary.c"
#undef main
static unsigned reloads,chains;
static uint64_t first_chain,previous_ns;
static void observe(void *context,uint64_t ns,unsigned event,uint32_t divisor,uint16_t chain,uint16_t remaining) {
    (void)context;
    assert(ns>=previous_ns);previous_ns=ns;
    if(event==1) {
        ++reloads;
        if(reloads==1) assert(divisor==214 && chain==306 && remaining==1);
        else assert(divisor==3424 && chain==19 && remaining==1);
    }
    if(event==2) { ++chains;if(!first_chain) first_chain=ns; }
}
int main(void) {
    assert(device_baseline_main(1,NULL)==0);
    PortableWholeAudioProvider p;
    assert(portable_whole_audio_provider_init(&p));
    PortableWholeAudioHost host={&p,configure,start,stop,opl_event,enable_samples,enable,NULL};
    assert(portable_whole_audio_bind(&host));
    memset(snd_sample_channel_records,0,sizeof(snd_sample_channel_records));
    p.timer_observer=observe;writes=0;
    snd_select_two_channel_timer(214,306);snd_start_sample_timer();
    portable_whole_audio_provider_advance(&p,UINT64_C(1000000000));
    uint64_t first=(uint64_t)(214+3424)*12*1000000000/14318180;
    assert(reloads==2 && first_chain==first);
    assert(chains==1+(UINT64_C(1000000000)*14318180-(uint64_t)(214+3424)*12*1000000000)/((uint64_t)3424*19*12*1000000000));
    uint64_t next=p.irq_ns,fraction=p.irq_fraction;
    snd_restore_bios_timer(0);portable_whole_audio_unbind();portable_whole_audio_provider_close(&p);
    /* Partitioning one second into irregular Qs preserves every rational
     * remainder and final IRQ schedule, including a reload inside the first Q. */
    assert(portable_whole_audio_provider_init(&p));assert(portable_whole_audio_bind(&host));
    reloads=chains=0;first_chain=previous_ns=0;p.timer_observer=observe;writes=0;
    snd_select_two_channel_timer(214,306);snd_start_sample_timer();
    for(uint64_t t=1;t<1000000000;t+=7919) portable_whole_audio_provider_advance(&p,t);
    portable_whole_audio_provider_advance(&p,1000000000);
    assert(p.irq_ns==next && p.irq_fraction==fraction && reloads==2 && first_chain==first);
    snd_restore_bios_timer(0);portable_whole_audio_unbind();portable_whole_audio_provider_close(&p);
    puts("PASS: slow reload notification, first-chain phase, rational Q partition control");
    return 0;
}
