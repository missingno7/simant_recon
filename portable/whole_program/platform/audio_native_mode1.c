#include "audio_native_mode1.h"

#include "audio.h"
#include "audio_state.h"

#include <stdatomic.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct NativeMode1State {
    PortableWholeAudioMode1Host host;
    unsigned critical_depth;
    unsigned timer_start_count;
    int16_t pit_divisor;
    int16_t sequencer_reload;
    int configured;
    int armed;
} NativeMode1State;

static NativeMode1State state;

static _Noreturn void unavailable(const char *service)
{
    fprintf(stderr, "whole-program audio host service unavailable in native mode 1: %s\n",
            service != NULL ? service : "unknown");
    exit(70);
}

int portable_whole_audio_mode1_bind(const PortableWholeAudioMode1Host *host)
{
    if (host == NULL || host->attach_sequencer == NULL ||
        state.host.attach_sequencer != NULL || state.armed != 0 ||
        state.critical_depth != 0)
        return 0;
    state.host = *host;
    state.configured = 0;
    state.timer_start_count = 0;
    return 1;
}

void portable_whole_audio_mode1_unbind(void)
{
    if (state.armed != 0 || state.critical_depth != 0)
        unavailable("unbinding active mode-1 source timer/critical section");
    memset(&state, 0, sizeof(state));
}

int portable_whole_audio_mode1_timer_armed(void) { return state.armed; }
unsigned portable_whole_audio_mode1_timer_start_count(void)
{ return state.timer_start_count; }
int portable_whole_audio_mode1_timer_configuration(int16_t *pit_divisor,
                                                   int16_t *sequencer_reload)
{
    if (state.configured == 0 || pit_divisor == NULL || sequencer_reload == NULL)
        return 0;
    *pit_divisor = state.pit_divisor;
    *sequencer_reload = state.sequencer_reload;
    return 1;
}

/* Converted m29F0 cli/sti boundaries guard source-state changes on the one
 * source-control thread. The SDL device receives already-rendered bytes and
 * its callback does not access generated source globals. Signal fences keep
 * compiler motion within the source critical sections; these functions do
 * not claim to disable host interrupts or provide cross-thread locking.
 */
void dos_audio_host_interrupt_disable(void)
{
    if (state.host.attach_sequencer == NULL || state.critical_depth == UINT_MAX)
        unavailable("interrupt-disable outside bound mode-1 source thread");
    atomic_signal_fence(memory_order_seq_cst);
    ++state.critical_depth;
}

void dos_audio_host_interrupt_enable(void)
{
    if (state.host.attach_sequencer == NULL || state.critical_depth == 0)
        unavailable("unmatched interrupt-enable");
    --state.critical_depth;
    atomic_signal_fence(memory_order_seq_cst);
}

void dos_audio_host_out8(uint16_t port, uint8_t value)
{
    if (port == 0x0061 && state.host.attach_sequencer != NULL &&
        state.host.write_speaker_latch != NULL && (value & 0xfcu) == 0)
        state.host.write_speaker_latch(state.host.context, value);
    else
        unavailable("DOS/ISA out8 (only the mode-1 PC-speaker latch clear is hosted)");
}
void dos_audio_host_out16(uint16_t port, uint16_t value)
{ (void)port; (void)value; unavailable("DOS/ISA out16"); }
uint8_t dos_audio_host_in8(uint16_t port)
{
    if (port == 0x0061 && state.host.attach_sequencer != NULL &&
        state.host.read_speaker_latch != NULL)
        return state.host.read_speaker_latch(state.host.context);
    unavailable("DOS/ISA in8 (only the mode-1 PC-speaker latch is hosted)");
}
uint16_t dos_audio_host_bios_int1a_8100(void)
{ unavailable("BIOS INT 1Ah AX=8100h"); }
void dos_audio_host_bios_int15_c000(uint16_t *es_out, uint16_t *bx_out)
{ (void)es_out; (void)bx_out; unavailable("BIOS INT 15h AX=C000h"); }
uint8_t dos_audio_host_read_far_u8(uint16_t segment, uint16_t offset)
{ (void)segment; (void)offset; unavailable("real-mode far byte read"); }
uint16_t dos_audio_host_read_far_u16(uint16_t segment, uint16_t offset)
{ (void)segment; (void)offset; unavailable("real-mode far word read"); }
_Noreturn void dos_audio_host_song_bounds_fault(uint16_t offset,
                                                size_t length,
                                                size_t song_size)
{
    fprintf(stderr, "source song span outside locked handle: offset=%u length=%zu size=%zu\n",
            (unsigned)offset, length, song_size);
    exit(71);
}

/* Original m28BC mode-1 timer arguments are PIT divisor 0x00d6 and reload
 * 0x0132. SDL renders exactly one source PIT output step per queued byte and
 * invokes the original sequencer on the source divider. */
void f_28BC_0488(int16_t pit_divisor, int16_t sequencer_reload)
{
    if (state.host.attach_sequencer == NULL || pit_divisor != 0x00d6 ||
        sequencer_reload != 0x0132 || state.armed != 0)
        unavailable("unexpected source timer profile (only mode-1 0x00d6/0x0132 is supported)");
    state.configured = 1;
    state.pit_divisor = pit_divisor;
    state.sequencer_reload = sequencer_reload;
}

extern int16_t fd_55B3_6B42;
extern int16_t f_284A_067F(void);

void f_28BC_03CC(void)
{
    if (state.host.attach_sequencer == NULL || state.configured == 0)
        unavailable("source timer start without selected native mode-1 profile");
    ++state.timer_start_count;
    if (state.armed == 0) {
        state.host.attach_sequencer(state.host.context,
                                    (uint16_t)state.pit_divisor,
                                    (uint16_t)state.sequencer_reload,
                                    &fd_55B3_6B42,
                                    f_284A_067F);
        state.armed = 1;
    }
}

void f_28BC_046B(int16_t pit_divisor, int16_t sequencer_reload)
{
    (void)pit_divisor;
    (void)sequencer_reload;
    unavailable("legacy accelerated DOS timer profile f_28BC_046B");
}

void f_28BC_04E0(int16_t divisor)
{
    if (state.host.attach_sequencer == NULL || divisor != 0)
        unavailable("unexpected source timer stop");
    /* The original cleanup path can call this before mode-1 setup has ever
     * armed a timer (for example while unwinding an earlier startup failure).
     * There is then no host attachment to undo. Keep the host binding alive:
     * a later sound initialization may configure and arm the same service. */
    if (state.armed != 0) {
        state.host.attach_sequencer(state.host.context, 0, 0, NULL, NULL);
        state.armed = 0;
    }
    state.configured = 0;
    state.pit_divisor = 0;
    state.sequencer_reload = 0;
}

void f_283E_000A(uint8_t reg, uint8_t value)
{ (void)reg; (void)value; unavailable("AdLib/OPL register write"); }
void f_283E_0035(void) { unavailable("AdLib/OPL reset"); }
void f_29BF_0008(int16_t base_port)
{ (void)base_port; unavailable("Sound Blaster port initialization"); }
int16_t f_29BF_0139(void)
{ unavailable("Sound Blaster port detection"); }
void f_29BF_00E6(int16_t reg, int16_t value)
{ (void)reg; (void)value; unavailable("legacy serial/MIDI output"); }

/* Current canonical ASM OFFSET expressions, resolved by the source assembler,
 * remain source selector words;
 * they are not host function pointers. The native SDL provider routes through
 * its explicit mode-1 binding and never indirects through these DOS offsets.
 * Every other output backend remains fail-closed above rather than guessing a
 * native translation for a real-mode code pointer.
 */
extern int16_t g_693C ;
extern int16_t fd_55B3_6B4A ;
extern int16_t fd_55B3_6B9C ; /* initial out_speaker near-code offset */
extern int16_t fd_55B3_6BA0;
extern int16_t fd_55B3_74AD ; /* out_speaker */
extern int16_t fd_55B3_74AF ; /* out_adlib */
extern int16_t fd_55B3_74B1 ; /* out_lpt */
extern int16_t fd_55B3_74B3 ; /* out_200 */
extern int16_t fd_55B3_74B5 ; /* out_sb */
extern int16_t fd_55B3_74B7 ; /* out_222 */
extern int16_t fd_55B3_74B9 ; /* out_6B4A */
/* The original offset is an AdLib-only volume correction field; mode 1 uses
 * the DAC's distinct fd_55B3_74C0 base instead. */
extern int16_t fd_50F6_4B16;
/* OPL-only table storage is deliberately opaque. Any actual OPL path reaches
 * an unavailable register-write boundary and aborts; this does not implement
 * or approximate the source table's values. */
