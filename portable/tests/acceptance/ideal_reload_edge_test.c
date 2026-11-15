/* Real native provider/CLI/STI: a mode-3 low-to-high reload must deliver once. */
#define main device_baseline_main
#include "../audio/device_boundary.c"
#undef main
static unsigned chains;
static void observe_edge(void *ctx,uint64_t ns,unsigned event,uint32_t d,uint16_t c,uint16_t r) {
    (void)ctx;(void)ns;(void)d;(void)c;(void)r;
    if(event==2) ++chains;
}
int main(void) {
    PortableWholeAudioProvider p;
    assert(portable_whole_audio_provider_init(&p));
    PortableWholeAudioHost host={&p,configure,start,stop,opl_event,enable_samples,enable,NULL};
    assert(portable_whole_audio_bind(&host));
    p.timer_observer=observe_edge;
    snd_select_two_channel_timer(214,306);snd_start_sample_timer();
    unsigned initial_writes=writes;
    portable_whole_audio_provider_advance(&p,179352);
    assert(writes==initial_writes && p.fast); /* rational edge is 179352.403... ns */
    portable_whole_audio_provider_advance(&p,179353);
    assert(writes==initial_writes+2 && !p.fast);
    portable_whole_audio_provider_advance(&p,2000000);
    assert(!p.fast && chains==0); /* slow OUT is low, next edge at 3.049 ms */
    uint8_t bytes[5]={128,128,128,128,128};char *payload=(char *)bytes;
    PortableWholeAudioSample sample={0};sample.data=&payload;sample.len=5;
    snd_sample_channel_records[0].snd=&sample;
    snd_sample_channel_records[0].voltab=snd_volume_table_offset;
    snd_sample_channel_records[0].end=3;
    unsigned before=writes;
    dos_audio_host_interrupt_disable();
    snd_start_sample_timer(); /* source adapter's own STI releases the edge */
    assert(portable_whole_audio_interrupts_enabled());
    assert(!p.pending_irq && chains==1 && writes==before+2);
    assert(p.time_ns==2000000 && p.irq_ns==2179352);
    /* Same-instant restart at the high phase creates no second edge. */
    before=writes;snd_start_sample_timer();assert(writes==before && chains==1);
    /* An empty immediate fast IRQ reprograms the slow timer at this instant. */
    snd_sample_channel_records[0].snd=NULL;
    portable_whole_audio_provider_advance(&p,4000000);
    assert(!p.fast);snd_start_sample_timer();
    assert(!p.fast && p.irq_ns==6869638 && !p.pending_irq);
    snd_restore_bios_timer(0);portable_whole_audio_unbind();portable_whole_audio_provider_close(&p);
    puts("PASS: mode-3 low reload, STI delivery, high-phase negative");
    return 0;
}
