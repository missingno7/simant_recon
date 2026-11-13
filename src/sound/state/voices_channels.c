/*
 * Defines the functional voice and channel record arrays. Sound loading, backend selection and
 * MIDI allocation share their fields.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

union VoicePayload {
    long offset;
    char far *sample;
};

struct Voice {
    int kind;
    union VoicePayload payload;
};

struct Chan {
    char type;
    char num;
    char c2;
    char c3;
    char c4;
    char c5;
};

struct Voice far snd_instrument_descriptors[56];
struct Chan far snd_voice_slots[33];
