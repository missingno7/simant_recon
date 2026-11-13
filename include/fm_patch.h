/* Packed OPL instrument record. Include under #pragma pack(1).
 * Static instrument definitions write it; opl2_voices sends register bytes and
 * applies the octave/volume metadata. Organisation and field names are ours.
 */
#ifndef FM_PATCH_H
#define FM_PATCH_H
struct FMPatch {
    unsigned char reg[11]; /* +00 OPL operator/feedback values; write_instrument establishes order. */
    int octave; /* +0B signed octave transpose, multiplied by 12 semitones by note-level setup. */
    int volume; /* +0D signed velocity adjustment, added before clipping to 0..127. */
};
#endif
