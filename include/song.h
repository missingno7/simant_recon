/* 60-byte song resource descriptor, distinct from the former midi_voices struct Song.
 * theme_song supplies the static channel maps; resource_loading manages data.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef SONG_H
#define SONG_H

struct Song {
    int priority[14]; /* Per-channel voice priority; midi_player copies into midi_channel_priorities. */
    unsigned instrument[14]; /* Per-channel instrument-table index; loader pins samples, player copies it. */
    char far * far *data; /* Sequencer resource handle; loader owns allocation/release and player locks it. */
};

#endif
