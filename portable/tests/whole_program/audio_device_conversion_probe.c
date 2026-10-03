#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "portable/whole_program/platform/audio.h"

void f_277E_0958(void);
void f_277E_0965(void);
int16_t f_293A_002D(void);
int16_t f_293A_0059(void);
void f_29D6_000A(int16_t a, int16_t note, int16_t volume, int16_t channel);
void f_29D6_00D9(int16_t a, int16_t note, int16_t volume, int16_t channel);

struct Event { int kind; uint16_t port; uint16_t value; };
struct NoteVector {
    int16_t note, volume, channel;
    uint16_t fm_word;
    uint8_t fm_byte;
    uint8_t psg[3];
};

static struct Event events[16];
static unsigned event_count;
static uint16_t bios_ax, bios_es, bios_bx, bios_signature;
static uint8_t bios_byte, cmos_byte;
int16_t fd_50F6_4B14;

static const struct NoteVector notes[] = {
    { 0, 0, 0, 11146, 159, { 141, 221, 159 } },
    { 12, 64, 1, 5549, 183, { 174, 238, 183 } },
    { 60, 64, 3, 3558, 247, { 238, 14, 247 } },
    { 127, 127, 7, 100, 112, { 100, 0, 112 } },
    { 84, 1, 15, 869, 127, { 107, 3, 127 } },
};

static void require(int ok, const char *message)
{
    if (!ok) { fprintf(stderr, "FAIL: %s\n", message); exit(1); }
}
static void clear_events(void) { event_count = 0; }
static void event(int kind, uint16_t port, uint16_t value)
{
    if (event_count == sizeof events / sizeof events[0]) abort();
    events[event_count++] = (struct Event){ kind, port, value };
}

void dos_audio_host_interrupt_disable(void) { event(5, 0, 0); }
void dos_audio_host_interrupt_enable(void) { event(6, 0, 0); }
void dos_audio_host_out8(uint16_t port, uint8_t value) { event(1, port, value); }
void dos_audio_host_out16(uint16_t port, uint16_t value) { event(2, port, value); }
uint8_t dos_audio_host_in8(uint16_t port)
{
    event(3, port, port == 0x0071 ? cmos_byte : 0xa5);
    return port == 0x0071 ? cmos_byte : 0xa5;
}
uint16_t dos_audio_host_bios_int1a_8100(void) { return bios_ax; }
void dos_audio_host_bios_int15_c000(uint16_t *es_out, uint16_t *bx_out)
{
    *es_out = bios_es;
    *bx_out = bios_bx;
}
uint8_t dos_audio_host_read_far_u8(uint16_t segment, uint16_t offset)
{
    (void)segment; (void)offset;
    return bios_byte;
}
uint16_t dos_audio_host_read_far_u16(uint16_t segment, uint16_t offset)
{
    (void)segment; (void)offset;
    return bios_signature;
}
_Noreturn void dos_audio_host_song_bounds_fault(uint16_t offset,
                                                 size_t length,
                                                 size_t song_size)
{
    (void)offset; (void)length; (void)song_size;
    abort();
}

/* m29F0's converted wrapper is outside this native test binary; these
 * fail-closed adapters capture m29D6's call into that existing boundary. */
void f_29F0_002A(int16_t port, int8_t value) { event(1, (uint16_t)port, (uint8_t)value); }
uint8_t f_29F0_0038(int16_t port) { return dos_audio_host_in8((uint16_t)port); }

/* Unused module peers abort if a supposedly covered case reaches them. */
void f_29BF_00E6(int16_t reg, int16_t value) { (void)reg; (void)value; abort(); }
void f_283E_000A(int8_t reg, int8_t value) { (void)reg; (void)value; abort(); }
int16_t f_29BF_0139(void) { return 0; }
int16_t f_29B8_0000(void) { return 0; }
void f_2815_0118(void) { abort(); }
void f_283E_0035(void) { abort(); }
int16_t fd_50F6_4A46;
int16_t fd_50F6_01F0[8];
uint16_t fd_55B3_7564;
int16_t fd_55B3_6BA0;
int16_t fd_55B3_74AD, fd_55B3_74AF, fd_55B3_74B1, fd_55B3_74B3;
int16_t fd_55B3_74B5, fd_55B3_74B7, fd_55B3_74B9;

static void verify_note_vectors(void)
{
    size_t i;
    for (i = 0; i < sizeof notes / sizeof notes[0]; ++i) {
        const struct NoteVector *v = &notes[i];
        fd_50F6_4B14 = 0x0220;
        clear_events();
        f_29D6_00D9(0, v->note, v->volume, v->channel);
        require(event_count == 2 && events[0].kind == 2 && events[1].kind == 1,
                "FM source writes one word then one byte");
        require(events[0].port == 0x0220 && events[0].value == v->fm_word &&
                events[1].port == 0x0220 && events[1].value == v->fm_byte,
                "FM source register words match pinned original DOS vectors");

        clear_events();
        f_29D6_000A(0, v->note, v->volume, v->channel);
        require(event_count == 3, "PSG source emits exactly three ordered writes");
        for (unsigned j = 0; j < 3; ++j)
            require(events[j].kind == 1 && events[j].port == 0x0205 &&
                    events[j].value == v->psg[j],
                    "PSG source writes match pinned original DOS vectors");
    }
}

static void verify_window_port_sequences(void)
{
    clear_events();
    f_277E_0958();
    require(event_count == 2 && events[0].kind == 3 && events[0].value == 0xa5 &&
            events[1].kind == 1 && events[1].port == 0x0061 && events[1].value == 0xa4,
            "speaker gate clears the two source bits at port 61h");
    clear_events();
    f_277E_0965();
    require(event_count == 3 && events[0].port == 0x000a && events[0].value == 5 &&
            events[1].port == 0x0220 && events[1].value == 0x0f &&
            events[2].port == 0x0221 && events[2].value == 0x60,
            "DMA/audio initialization preserves all three source writes");
}

static void verify_bios_predicates_follow_host_inputs(void)
{
    bios_ax = 0x00c4; bios_byte = 0;
    require(f_293A_002D() == 1, "INT 1A result 00C4 is a positive source predicate");
    bios_ax = 0; bios_byte = 0x21;
    require(f_293A_002D() == 1, "BIOS marker 21h is a positive source predicate");
    bios_ax = 0; bios_byte = 0;
    require(f_293A_002D() == 0, "negative BIOS inputs remain negative");

    clear_events(); bios_signature = 0x0000;
    require(f_293A_0059() == 0 && event_count == 0,
            "nonmatching INT 15 descriptor stops before CMOS I/O");
    bios_es = 0xf000; bios_bx = 0x0100; bios_signature = 0x0bfc;
    cmos_byte = 0x00; clear_events();
    require(f_293A_0059() == 0, "CMOS bit clear remains negative");
    require(event_count == 4 && events[0].kind == 5 && events[1].kind == 1 &&
            events[1].port == 0x0070 && events[1].value == 0x2f &&
            events[2].kind == 3 && events[2].port == 0x0071 &&
            events[3].kind == 6, "CMOS query retains disable/select/read/enable order");
    cmos_byte = 0x10; clear_events();
    require(f_293A_0059() == 1, "CMOS bit set follows the provider result");
}

int main(void)
{
    verify_note_vectors();
    verify_window_port_sequences();
    verify_bios_predicates_follow_host_inputs();
    puts("audio device boundary/source-semantics controls: PASS");
    return 0;
}
