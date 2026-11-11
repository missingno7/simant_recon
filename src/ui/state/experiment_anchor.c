/*
 * Defines the coordinate pair used by experiment editing. processExp reads and updates the pair
 * while applying a tool gesture.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The source-owned allocation does not establish historical object order,
 * absolute placement or original initialization values.
 */

int far ExpLastPnt[2];
