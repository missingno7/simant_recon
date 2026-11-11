/*
 * Defines the selected barrier and terrain set words. Tile loading, terrain generation and
 * editing read these values.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Both definitions are uninitialized; no initial value is inferred.
 */

int far Barrier;
int far TERRAINset;
