#include "audio_state.h"

#include <stddef.h>

_Static_assert(offsetof(PortableWholeAudioInstrumentEntry, payload) == 2,
               "source audio table pointer payload follows its word tag");
_Static_assert(sizeof(PortableWholeAudioInstrumentEntry) ==
                   2 + sizeof(void *),
               "shared audio instrument table has a native pointer payload");
_Static_assert(sizeof(PortableWholeAudioRuntimeChannel) == 6,
               "source allocator channel records remain six bytes");
_Static_assert(sizeof(PortableWholeAudioSample) == sizeof(void *) + 27,
               "shared sample view keeps source member order with a native handle");
_Static_assert(offsetof(PortableWholeAudioSample, data) == 0 &&
                   offsetof(PortableWholeAudioSample, len) == sizeof(void *) &&
                   offsetof(PortableWholeAudioSample, name) == sizeof(void *) + 10 &&
                   offsetof(PortableWholeAudioSample, object) == sizeof(void *) + 25,
               "shared sample fields use the common source-derived view");

/* This TU owns the native pointer-rich shared audio globals declared here.
 * The generated source-state owner remains the sole owner of established
 * scalar symbols (including 4A48/4A4C/4B2C/4B2E/4B8A). Generated code uses
 * this one canonical object for shared pointer-bearing table views.
 */
extern PortableWholeAudioInstrumentEntry snd_instrument_descriptors[56];
extern int16_t snd_driver_capabilities[7];

extern PortableWholeAudioRuntimeChannel snd_voice_slots[33];

extern char **midi_song_data_handle;
/* Track status/time are owned by canonical src/sound/state/midi_tracks.c. */
extern int16_t midi_channel_instruments[14];
extern int16_t midi_channel_priorities[14];

extern int16_t midi_service_countdown;
extern PortableWholeAudioRuntimeSample snd_sample_channel_records[4];
extern uint16_t snd_volume_table_offset;
