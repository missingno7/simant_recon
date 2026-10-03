#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "portable/whole_program/platform/audio.h"

void f_29F0_000A(void);
void f_29F0_0012(void);
void f_29F0_001A(void);
void f_29F0_0022(void);
void f_29F0_002A(int16_t port, int16_t value);
uint8_t f_29F0_0038(int16_t port);

static int events[16];
static unsigned event_count;
static uint16_t last_port;
static uint8_t last_value;
static uint16_t fault_offset;
static size_t fault_length, fault_size;
static jmp_buf fault_jump;

static void require(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "FAIL: %s\n", message);
        exit(1);
    }
}

void dos_audio_host_interrupt_disable(void) { events[event_count++] = 1; }
void dos_audio_host_interrupt_enable(void) { events[event_count++] = 2; }
void dos_audio_host_out8(uint16_t port, uint8_t value)
{
    events[event_count++] = 3;
    last_port = port;
    last_value = value;
}
uint8_t dos_audio_host_in8(uint16_t port)
{
    events[event_count++] = 4;
    last_port = port;
    return 0xa5;
}
_Noreturn void dos_audio_host_song_bounds_fault(uint16_t offset,
                                                 size_t length,
                                                 size_t song_size)
{
    fault_offset = offset;
    fault_length = length;
    fault_size = song_size;
    longjmp(fault_jump, 1);
}

int main(void)
{
    uint8_t bytes[] = { 0x10, 0x20, 0x30, 0x40 };

    f_29F0_000A();
    f_29F0_0012();
    f_29F0_001A();
    f_29F0_0022();
    f_29F0_002A(0x1338, 0x01ab);
    require(f_29F0_0038(0x0338) == 0xa5, "IN8 returns provider byte");
    require(event_count == 6, "six converted helper calls reach providers once");
    require(events[0] == 1 && events[1] == 2 && events[2] == 1 && events[3] == 2,
            "CLI/STI source order is preserved");
    require(events[4] == 3 && last_value == 0xab,
            "OUT8 truncates value to AL byte");
    require(events[5] == 4 && last_port == 0x0338,
            "IN8 truncates port to DX word");
    /* Reissue OUT to inspect its final normalized port/value independently. */
    f_29F0_002A(0x1338, 0x01ab);
    require(last_port == 0x1338 && last_value == 0xab,
            "OUT8 truncates value but preserves its low-word port");
    f_29F0_002A(-1, -1);
    require(last_port == 0xffff && last_value == 0xff,
            "OUT8 uses 16-bit DX and 8-bit AL truncation for negative words");

    require(*dos_audio_song_span(bytes, sizeof bytes, 0, 1) == 0x10,
            "song first byte span");
    require(*dos_audio_song_span(bytes, sizeof bytes, 3, 1) == 0x40,
            "song final byte span");
    require(dos_audio_song_span(bytes, sizeof bytes, 4, 0) == bytes + 4,
            "empty span at allocation end");
    if (setjmp(fault_jump) == 0) {
        (void)dos_audio_song_span(bytes, sizeof bytes, 4, 1);
        require(0, "end-plus-one access must fault");
    }
    require(fault_offset == 4 && fault_length == 1 && fault_size == sizeof bytes,
            "bounds leaf receives precise end-plus-one request");
    if (setjmp(fault_jump) == 0) {
        (void)dos_audio_song_span(bytes, sizeof bytes, 3, 2);
        require(0, "cross-end access must fault");
    }
    require(fault_offset == 3 && fault_length == 2 && fault_size == sizeof bytes,
            "bounds leaf receives precise crossing request");
    if (setjmp(fault_jump) == 0) {
        (void)dos_audio_song_span(bytes, sizeof bytes, 5, 0);
        require(0, "offset beyond allocation must fault even for empty span");
    }
    require(fault_offset == 5 && fault_length == 0 && fault_size == sizeof bytes,
            "bounds leaf receives beyond-end empty request");
    if (setjmp(fault_jump) == 0) {
        (void)dos_audio_song_span(bytes, sizeof bytes, 0xffff, SIZE_MAX);
        require(0, "unrepresentably large requested span must fault");
    }
    require(fault_offset == 0xffff && fault_length == SIZE_MAX &&
            fault_size == sizeof bytes,
            "bounds check rejects huge length without arithmetic wrap");
    puts("audio host-intent and song-boundary controls: PASS");
    return 0;
}
