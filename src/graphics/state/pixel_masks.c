/*
 * Reviewed candidate for functional SOURCE_ONLY_DOS graphics tables.
 *
 * These three typed near arrays are derived from consumer algorithms, not
 * copied executable bytes and not a historical TU or address-ownership claim.
 * `_g_2100` is source-spelled by two consumers.  The other two names describe
 * the SS-indexed roles at 68AC and 68B4; those physical names/owners are not
 * recovered.  All three are isolated in _DATA and have the bounds implied by
 * their indexes: 8 horizontal phases, 8 one-bit tail residues, 2 packed
 * nibble parities.
 *
 * This candidate remains inadmissible as original storage while indirect
 * writes/aliases are unclosed.  The companion probe checks only test-owned
 * source, OMF layout/fixups and DOS runtime semantics.
 */

#define PLANE_BIT(phase) \
    ((unsigned char)(0x80u >> (phase)))

unsigned char near g_2100[8] = {
    PLANE_BIT(0), PLANE_BIT(1), PLANE_BIT(2), PLANE_BIT(3),
    PLANE_BIT(4), PLANE_BIT(5), PLANE_BIT(6), PLANE_BIT(7)
};

#define BYTE_TAIL_MASK(residue) \
    ((unsigned char)((residue) == 0 ? 0xFFu : \
        ((0xFFu << (8 - (residue))) & 0xFFu)))

unsigned char near mono_tail_masks[8] = {
    BYTE_TAIL_MASK(0), BYTE_TAIL_MASK(1),
    BYTE_TAIL_MASK(2), BYTE_TAIL_MASK(3),
    BYTE_TAIL_MASK(4), BYTE_TAIL_MASK(5),
    BYTE_TAIL_MASK(6), BYTE_TAIL_MASK(7)
};

#define PACKED_TAIL_MASK(is_odd) \
    ((unsigned char)((is_odd) ? (0xFFu & ~0x0Fu) : 0xFFu))

unsigned char near packed_tail_masks[2] = {
    PACKED_TAIL_MASK(0), PACKED_TAIL_MASK(1)
};
