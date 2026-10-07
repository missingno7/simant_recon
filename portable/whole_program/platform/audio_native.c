/* Hardware leaves projected from canonical m28BC/m283E ASM. Ordinary sound
 * selection, songs, instruments and channel state remain canonical. */
#include "audio_native.h"
#include "audio.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdatomic.h>
static PortableWholeAudioHost host;
static int armed, interrupts = 1;
static _Noreturn void unavailable(const char *service) {
    fprintf(stderr,"Unimplemented audio hardware service: %s\n",service); exit(70);
}
int portable_whole_audio_bind(const PortableWholeAudioHost *h) {
    if(!h || !h->configure_timer || !h->out8 || !h->in8 || host.out8) return 0;
    host=*h; interrupts=1; return 1;
}
void portable_whole_audio_unbind(void) { memset(&host,0,sizeof(host)); armed=0; }
int portable_whole_audio_timer_armed(void) { return armed; }
int portable_whole_audio_interrupts_enabled(void) { return interrupts; }
/* CLI/STI set IF; they are not nesting-counted locks. All source execution and
 * device commands run on the application thread. SDL only consumes PCM. */
void dos_audio_host_interrupt_disable(void) { atomic_signal_fence(memory_order_seq_cst); interrupts=0; }
void dos_audio_host_interrupt_enable(void) {
    interrupts=1;atomic_signal_fence(memory_order_seq_cst);
    if(host.enable_interrupts) host.enable_interrupts(host.context);
}
void dos_audio_host_out8(uint16_t port,uint8_t value) {
    if(!host.out8) unavailable("OUT before host binding");
    host.out8(host.context,port,value);
}
uint8_t dos_audio_host_in8(uint16_t port) {
    if(!host.in8) unavailable("IN before host binding");
    return host.in8(host.context,port);
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
void f_28BC_0488(int16_t divisor,int16_t chain) { configure(divisor,chain,2); }
void f_28BC_046B(int16_t divisor,int16_t chain) { configure(divisor,chain,4); }
void f_28BC_03CC(void) {
    if(!host.start_timer) unavailable("PIT start");
    host.start_timer(host.context);armed=1; interrupts=1;
}
void f_28BC_040C(void) { unavailable("manual ISR0422 transition"); }
void f_28BC_04E0(int16_t divisor) {
    if(divisor) unavailable("nonzero PIT stop");
    if(armed && host.stop_timer) host.stop_timer(host.context);
    armed=0;interrupts=1;
}
/* m283E_0020 emits index, 10 status reads, data, 40 status reads. Preserve
 * the complete guest I/O order; no host register-to-note approximation. */
void f_283E_000A(uint8_t reg,uint8_t value) {
    unsigned i;dos_audio_host_out8(0x388,reg);
    for(i=0;i<10;++i) dos_audio_host_in8(0x388);
    dos_audio_host_out8(0x389,value);
    for(i=0;i<40;++i) dos_audio_host_in8(0x388);
}
void f_283E_0035(void) {
    f_283E_000A(0x20,0x21);f_283E_000A(0x60,0xf0);
    f_283E_000A(0x80,0xf0);f_283E_000A(0xc0,1);
    f_283E_000A(0xe0,0);f_283E_000A(0x43,0x3f);
    f_283E_000A(0xb0,1);f_283E_000A(0xa0,0x8f);
    f_283E_000A(0xb0,0x2e);
    /* Mode 4 uses the canonical 0x952-PIT-count delay. It remains outside
     * the Sound Blaster profile until the PIT-latch poll is hosted. */
    unavailable("AdLib-only reset PIT delay");
}
/* m29BF is the alternate indexed chip at 220/221, not the SB DSP. */
void f_29BF_0008(int16_t port) { (void)port;unavailable("indexed sound chip"); }
int16_t f_29BF_0139(void) { unavailable("indexed sound chip detection"); }
void f_29BF_00E6(int16_t reg,int16_t value) { (void)reg;(void)value;unavailable("indexed sound chip register"); }
