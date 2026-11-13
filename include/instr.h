/* Six-byte sound instrument descriptor. Static per-device tables feed snd_copy_instrument_table.
 * p is intentionally untyped: the backend establishes the pointed-to record kind.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef INSTR_H
#define INSTR_H

struct Instr {
    int kind; /* Backend dispatch index: 1 sample, 2 OPL, 3/4/5 PSG, 6 melodic MIDI, 7 drum. */
    void far *p; /* Backend-dependent pointer: Sample, packed FM patch, or three-word MIDI mapping. */
};

#endif
