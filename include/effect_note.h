/* Eight-byte configured sound effect entry. midi_voices called this Song;
 * instruments called it SfxNote. snd_start_configured_effect proves field interpretation.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef EFFECT_NOTE_H
#define EFFECT_NOTE_H

struct EffectNote {
    int note; /* Requested MIDI-style semitone number; static instrument data writes it. */
    int priority; /* Voice allocation priority argument (not instrument kind). */
    int instrument; /* Instrument descriptor index passed to snd_start_instrument_note. */
    int volume; /* Requested note velocity before device/driver scaling. */
};

#endif
