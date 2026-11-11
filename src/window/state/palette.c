/*
 * Defines the functional window colour records. Window loading and drawing select colours from
 * the sixteen record palette.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Shipped window palette: sixteen six-byte color records.
 * Functional footprint only; no historical allocation or placement claim.
 */

char far win_colors[16][6];
