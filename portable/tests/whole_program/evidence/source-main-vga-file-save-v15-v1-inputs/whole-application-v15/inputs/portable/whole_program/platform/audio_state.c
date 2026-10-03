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
PortableWholeAudioInstrumentEntry fd_50F6_0000[56];
PortableWholeAudioSample *fd_50F6_0150[39];
int16_t fd_50F6_01F0[7];

PortableWholeAudioRuntimeChannel fd_50F6_4A4E[33];

char **fd_50F6_4B28;
uint8_t fd_50F6_4B30[18];
int32_t fd_50F6_4B42[18];
int16_t fd_50F6_4B8E[14];
int16_t fd_50F6_4BAA[14];

int16_t fd_55B3_6B42;
PortableWholeAudioRuntimeSample fd_55B3_6B4C[4];
PortableWholeAudioVoiceSlot fd_55B3_6B4E[33];
uint16_t fd_55B3_6B9E;
