/* Six-byte voice assignment; device_channels initializes, midi_voices allocates/reaps.
 * Unsigned bytes preserve the existing allocator view, including its recorded folded test.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef CHAN_H
#define CHAN_H

struct Chan {
    unsigned char type; /* Device/backend dispatch index; device setup writes it; 0 terminates scan. */
    unsigned char num; /* Backend hardware voice/channel index, assigned during device setup. */
    unsigned char priority; /* Allocator priority; start writes request, stop/reap writes 0. */
    unsigned char instrument; /* Assigned instrument index; reset stores 0xFF (unassigned). */
    unsigned char note; /* Last note passed to backend; start writes it, stop clears it. */
    unsigned char age; /* Allocation scan counter, wraps at 256; reset/stop 15, start 0. */
};

#endif
