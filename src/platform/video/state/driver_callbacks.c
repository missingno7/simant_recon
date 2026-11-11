/*
 * Defines the functional near table of far callback pointers used for display driver dispatch.
 * The assembly screen and raster entry points are selected through this table.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: original segment and resident/overlay assignment are unknown. Source-owned storage;
 * original placement, owning file and completeness are unproven. Some storage addresses remain
 * unregistered.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

void (far * near driver_callback_table[25])();
