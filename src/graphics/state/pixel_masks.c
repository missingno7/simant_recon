/*
 * Defines bit phase and tail masks for monochrome and packed pixel operations. The values are
 * expressed as formulas derived from the consumer indexing rules.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The three near arrays derive from consumer algorithms. Only _g_2100 is
 * source-spelled by its two consumers; the SS-indexed 68AC/68B4 roles have
 * no recovered physical names or owners. _DATA bounds follow the indexes:
 * eight horizontal phases, eight one-bit tail residues, two nibble parities.
 * Indirect writes and aliases remain open; probes establish functional
 * OMF layout, fixups and DOS semantics, not original storage.
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
