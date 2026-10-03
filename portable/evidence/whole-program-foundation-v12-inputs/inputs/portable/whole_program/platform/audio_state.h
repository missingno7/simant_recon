#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_STATE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_STATE_H

#include <stdint.h>

#pragma pack(push, 1)
typedef struct PortableWholeAudioSample {
    char **data;
    uint16_t len;
    uint16_t loop;
    char looped;
    uint8_t octave;
    int16_t tune;
    int16_t loaded;
    char name[15];
    int16_t object;
} PortableWholeAudioSample;
#pragma pack(pop)

/* Shared native ownership for source audio globals. Several original TUs use
 * fd_50F6_0000 at DOS address 50F6:0000 with different semantic declarations:
 * m0000/m290D see {kind, Sample *}, m277E sees {a, void *}, m2815 sees
 * {kind, patch *}, and m295C sees {count, driver-info *}. Every view accesses
 * the same two-byte discriminator and far-pointer payload. This native table
 * preserves that single identity and gives the payload a host-width pointer.
 * Do not define per-module copies of this symbol.
 */
#pragma pack(push, 2)
typedef struct PortableWholeAudioInstrumentEntry {
    int16_t kind;
    void *payload;
} PortableWholeAudioInstrumentEntry;

typedef struct PortableWholeAudioRuntimeChannel {
    uint8_t type;
    uint8_t num;
    uint8_t c2;
    uint8_t c3;
    uint8_t c4;
    uint8_t c5;
} PortableWholeAudioRuntimeChannel;

typedef struct PortableWholeAudioRuntimeSample {
    uint16_t pos;
    PortableWholeAudioSample *snd;
    uint16_t end;
    uint16_t start;
    uint16_t step;
    uint16_t voltab;
    uint8_t frac;
    uint8_t flags;
    PortableWholeAudioSample *owner;
} PortableWholeAudioRuntimeSample;

typedef struct PortableWholeAudioVoiceSlot {
    int32_t busy;
    int16_t w4;
    int16_t w6;
    int16_t w8;
    int16_t wA;
    int16_t wC;
    void *snd;
    int16_t w12;
} PortableWholeAudioVoiceSlot;
#pragma pack(pop)

/* Source bounds: fd_50F6_0000 has 56 table entries (the nine DATA instrument
 * tables each contain 56 entries); fd_50F6_0150 is the 39-entry sample free
 * list used by f_0000_0149; fd_50F6_01F0's seven words are addressed directly
 * by f_277E_00AF/0000. Native views are independent symbols because pointer
 * widening makes original DOS byte offsets unsuitable as host offsets.
 */
extern PortableWholeAudioInstrumentEntry fd_50F6_0000[56];
extern PortableWholeAudioSample *fd_50F6_0150[39];
extern int16_t fd_50F6_01F0[7];

/* Source m277E initializes/scans 0x21 six-byte channel records. The native
 * bytes are unsigned as read by m295C; m277E's -1 initializer is stored as
 * 0xff and is not normalized to a signed host value. Audio mode 1
 * uses two; four-slot mode can use four. The remaining entries are the source
 * zero-type sentinel/available rows consumed by m295C's original scan.
 */
extern PortableWholeAudioRuntimeChannel fd_50F6_4A4E[33];
extern int16_t fd_50F6_4A46;
extern int16_t fd_50F6_4A48;
extern int16_t fd_50F6_4A4A;
extern int16_t fd_50F6_4A4C;
extern int16_t fd_50F6_4B14;
extern int16_t fd_50F6_4B16;

/* MIDI parser state: 18 source tracks and 14 source channel instrument maps. */
extern char **fd_50F6_4B28;
extern int16_t fd_50F6_4B2C;
extern int16_t fd_50F6_4B2E;
extern uint8_t fd_50F6_4B30[18];
extern int32_t fd_50F6_4B42[18];
extern int32_t fd_50F6_4B8A;
extern int16_t fd_50F6_4B8E[14];
extern int16_t fd_50F6_4BAA[14];

/* Audio device configuration scalars remain owned by the generated state
 * aliases/source modules. These declarations centralize their shared ABI;
 * this header deliberately provides no storage for them. */
extern int16_t fd_55B3_6B4A;
extern int16_t fd_55B3_6B9C;
extern int16_t fd_55B3_6BA0;
extern int16_t fd_55B3_74AD;
extern int16_t fd_55B3_74AF;
extern int16_t fd_55B3_74B1;
extern int16_t fd_55B3_74B3;
extern int16_t fd_55B3_74B5;
extern int16_t fd_55B3_74B7;
extern int16_t fd_55B3_74B9;
extern int16_t fd_55B3_74C0;
extern uint16_t fd_55B3_7564;
extern int16_t (*fd_55B3_74DA[9])(void);
extern int16_t fd_55B3_6BA4[];

static inline PortableWholeAudioSample *portable_whole_audio_sample(
    const PortableWholeAudioInstrumentEntry *entry)
{
    return (PortableWholeAudioSample *)entry->payload;
}

static inline uint8_t *portable_whole_audio_patch_bytes(
    const PortableWholeAudioInstrumentEntry *entry)
{
    return (uint8_t *)entry->payload;
}

static inline int16_t *portable_whole_audio_driver_info(
    const PortableWholeAudioInstrumentEntry *entry)
{
    return (int16_t *)entry->payload;
}

/* Source m28BC/m290D timer and sampled-channel state. */
extern int16_t fd_55B3_6B42;
extern PortableWholeAudioRuntimeSample fd_55B3_6B4C[4];
extern PortableWholeAudioVoiceSlot fd_55B3_6B4E[33];
extern uint16_t fd_55B3_6B9E;

#endif
