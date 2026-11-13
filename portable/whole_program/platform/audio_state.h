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
 * snd_instrument_descriptors at DOS address 50F6:0000 with different semantic declarations:
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
    uint8_t priority;
    uint8_t instrument;
    uint8_t note;
    uint8_t age;
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

/* Source bounds: snd_instrument_descriptors has 56 table entries (the nine DATA instrument
 * tables each contain 56 entries); canonical source owns snd_sample_release_list as the
 * 39-entry sample free list used by snd_queue_sample_release; snd_driver_capabilities's seven words
 * are addressed directly by snd_reset_channel_tables/0000. Native views are independent
 * symbols because pointer widening makes original DOS byte offsets unsuitable
 * as host offsets.
 */
extern PortableWholeAudioInstrumentEntry snd_instrument_descriptors[56];
extern PortableWholeAudioSample *snd_sample_release_list[39];
extern int16_t snd_driver_capabilities[7];

/* Source m277E initializes/scans 0x21 six-byte channel records. The native
 * bytes are unsigned as read by m295C; m277E's -1 initializer is stored as
 * 0xff and is not normalized to a signed host value. Audio mode 1
 * uses two; four-slot mode can use four. The remaining entries are the source
 * zero-type sentinel/available rows consumed by m295C's original scan.
 */
extern PortableWholeAudioRuntimeChannel snd_voice_slots[33];
extern int16_t fd_50F6_4A46;
extern int16_t snd_sample_channel_count;
extern int16_t fd_50F6_4A4A;
extern int16_t snd_voice_build_index;
extern int16_t snd_device_io_base;
extern int16_t snd_opl_volume_bias;

/* MIDI parser state: 18 source tracks and 14 source channel instrument maps. */
extern char **midi_song_data_handle;
extern int16_t midi_song_data_bytes;
extern int16_t midi_header_division;
extern uint8_t midi_track_status[];
extern int32_t midi_track_event_ticks[];
extern int32_t midi_tick_delay_scale;
extern int16_t midi_channel_instruments[14];
extern int16_t midi_channel_priorities[14];

/* Audio device configuration scalars remain owned by the generated state
 * aliases/source modules. These declarations centralize their shared ABI;
 * this header deliberately provides no storage for them. */
extern int16_t snd_dac_io_base;
extern int16_t snd_sample_output_routine;
extern int16_t snd_sb_dsp_write_port;
extern int16_t snd_speaker_output_pointer;
extern int16_t snd_adlib_output_pointer;
extern int16_t snd_lpt_output_pointer;
extern int16_t snd_port200_output_pointer;
extern int16_t snd_sb_output_pointer;
extern int16_t snd_port222_output_pointer;
extern int16_t snd_based_dac_output_pointer;
extern int16_t snd_sample_volume_bias;
extern uint16_t snd_sb_io_base;
extern int16_t (*snd_driver_probe_table[9])(void);
extern uint8_t snd_opl_volume_curve[255];

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
extern int16_t midi_service_countdown;
extern PortableWholeAudioRuntimeSample snd_sample_channel_records[4];

extern uint16_t snd_volume_table_offset;

#endif
