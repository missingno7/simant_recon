/* Hardware leaves projected from canonical m28BC/m283E ASM. Ordinary sound
 * selection, songs, instruments and channel state remain canonical. */
#include "audio_native.h"
#include "audio.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdatomic.h>
extern void portable_test_audio_write(uint16_t,uint8_t) __attribute__((weak));
static PortableWholeAudioHost host;
static int armed, interrupts = 1, reset_high, reset_response;
static _Noreturn void unavailable(const char *service) {
    fprintf(stderr,"Unimplemented audio hardware service: %s\n",service); exit(70);
}
int portable_whole_audio_bind(const PortableWholeAudioHost *h) {
    if(!h || !h->configure_timer || !h->opl_register || !h->sample_enable || host.opl_register) return 0;
    host=*h; interrupts=1;reset_high=reset_response=0; return 1;
}
void portable_whole_audio_unbind(void) { memset(&host,0,sizeof(host)); armed=0; }
int portable_whole_audio_timer_armed(void) { return armed; }
int portable_whole_audio_interrupts_enabled(void) { return interrupts; }
/* CLI/STI set IF; they are not nesting-counted locks. All source execution and
 * device commands run on the application thread. SDL only consumes PCM. */
void dos_audio_host_interrupt_disable(void) { atomic_signal_fence(memory_order_seq_cst); interrupts=0; }
void dos_audio_host_interrupt_enable(void) {
    interrupts=1;atomic_signal_fence(memory_order_seq_cst);
    if(host.synchronize) host.synchronize(host.context);
    if(host.enable_interrupts) host.enable_interrupts(host.context);
}
/* The unchanged mode-6 startup still calls its canonical reset/probe leaves.
 * This fixed capability adapter has no DSP command stream or audio clock.
 * Playback uses native events below; other hardware remains unsupported. */
void dos_audio_host_out8(uint16_t port,uint8_t value) {
    if(!host.sample_enable) unavailable("OUT before host binding");
    if(host.synchronize) host.synchronize(host.context);
    if(portable_test_audio_write) portable_test_audio_write(port,value);
    if(port==0x226) {
        if(reset_high && !value) { reset_response=1;host.sample_enable(host.context,0); }
        reset_high=value!=0;
    } else if(port==0x22c && (value==0xd1 || value==0xd3)) host.sample_enable(host.context,value==0xd1);
    else if(port>=0x210 && port<=0x26f && (port&15)==6) { /* absent probe base */ }
    else unavailable("unsupported native audio port/control (no DSP/DMA)");
}
uint8_t dos_audio_host_in8(uint16_t port) {
    if(!host.sample_enable) unavailable("IN before host binding");
    if(host.synchronize) host.synchronize(host.context);
    if(port==0x22c || port==0x388) return 0;
    if(port==0x22e) return reset_response?0x80:0;
    if(port==0x22a) { uint8_t v=reset_response?0xaa:0xff;reset_response=0;return v; }
    if(port>=0x210 && port<=0x26f) return 0xff;
    unavailable("unsupported native audio capability query");
}
void dos_audio_host_out16(uint16_t port,uint16_t value) { (void)port;(void)value;unavailable("OUT word"); }
uint16_t dos_audio_host_bios_int1a_8100(void) { unavailable("Tandy BIOS INT1A"); }
void dos_audio_host_bios_int15_c000(uint16_t *es,uint16_t *bx) { (void)es;(void)bx;unavailable("BIOS INT15"); }
uint8_t dos_audio_host_read_far_u8(uint16_t s,uint16_t o) { (void)s;(void)o;unavailable("physical BIOS byte"); }
uint16_t dos_audio_host_read_far_u16(uint16_t s,uint16_t o) { (void)s;(void)o;unavailable("physical BIOS word"); }
_Noreturn void dos_audio_host_song_bounds_fault(uint16_t offset,size_t len,size_t size) {
    fprintf(stderr,"Song bounds: offset=%u length=%zu size=%zu\n",offset,len,size);exit(71);
}
static void configure(int16_t divisor,int16_t chain,unsigned channels) {
    if(!host.configure_timer || divisor!=214 || chain!=306) unavailable("PIT configuration");
    host.configure_timer(host.context,(uint16_t)divisor,(uint16_t)chain,channels);
}
void snd_select_two_channel_timer(int16_t divisor,int16_t chain) { configure(divisor,chain,2); }
void snd_select_four_channel_timer(int16_t divisor,int16_t chain) { configure(divisor,chain,4); }
void snd_start_sample_timer(void) {
    if(!host.start_timer) unavailable("PIT start");
    host.start_timer(host.context);armed=1; dos_audio_host_interrupt_enable();
}
void snd_slow_sample_timer(void) { unavailable("manual ISR0422 transition"); }
void snd_restore_bios_timer(int16_t divisor) {
    if(divisor) unavailable("nonzero PIT stop");
    if(armed && host.stop_timer) host.stop_timer(host.context);
    armed=0;interrupts=1;
}
/* m283E_0020's hardware leaf: register/value intent, without ISA latch/delays.
 * Historical OUT projection exists only for read-only acceptance diagnostics. */
void snd_opl_write_regs(uint8_t reg,uint8_t value) {
    if(!host.opl_register) unavailable("OPL before host binding");
    if(host.synchronize) host.synchronize(host.context);
    if(portable_test_audio_write) { portable_test_audio_write(0x388,reg);portable_test_audio_write(0x389,value); }
    host.opl_register(host.context,reg,value);
}
void snd_opl_write(uint8_t reg,uint8_t value) {
    snd_opl_write_regs(reg,value);
}
void snd_opl_probe_tone(void) {
    snd_opl_write_regs(0x20,0x21);snd_opl_write_regs(0x60,0xf0);
    snd_opl_write_regs(0x80,0xf0);snd_opl_write_regs(0xc0,1);
    snd_opl_write_regs(0xe0,0);snd_opl_write_regs(0x43,0x3f);
    snd_opl_write_regs(0xb0,1);snd_opl_write_regs(0xa0,0x8f);
    snd_opl_write_regs(0xb0,0x2e);
    /* Mode 4 uses the canonical 0x952-PIT-count delay. It remains outside
     * the Sound Blaster profile until the PIT-latch poll is hosted. */
    unavailable("AdLib-only reset PIT delay");
}
/* m29BF is the alternate indexed chip at 220/221, not the SB DSP. */
void snd_regchip_initialize(int16_t port) { (void)port;unavailable("indexed sound chip"); }
int16_t snd_regchip_detect(void) { unavailable("indexed sound chip detection"); }
void snd_regchip_write(int16_t reg,int16_t value) { (void)reg;(void)value;unavailable("indexed sound chip register"); }
