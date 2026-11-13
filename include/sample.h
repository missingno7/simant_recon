/* Packed 31-byte sample descriptor; INCLUDE UNDER #pragma pack(1).
 * resource_loading writes data/len/loaded; sample_voices consumes through +0C.
 * Its old char* data view was unused; the owning instrument tables prove the handle/tail.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef SAMPLE_H
#define SAMPLE_H

struct Sample {
    char far * far *data; /* +00 resource handle; loader sets it, release queue clears it. */
    unsigned len; /* +04 decoded sample bytes from mem_Size, truncated to DOS word. */
    unsigned loop; /* +06 loop offset in sample bytes; playback starts loop at this value +2. */
    char looped; /* +08 nonzero enables mixer looping (channel flag 0x80); static descriptors write it. */
    unsigned char octave; /* +09 reference octave for semitone step conversion; static descriptor. */
    int tune; /* +0A signed semitone adjustment added to the requested note. */
    int loaded; /* +0C loader/releaser state: 0 absent, 1 releasable, 2 pinned by song. */
    char name[15]; /* +0E static descriptor label; runtime meaning beyond label unproven. */
    int object; /* +1D kind-5 database object number passed by snd_load_sample_resource. */
};

#endif
