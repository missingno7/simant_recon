/*
 * Defines the seven word sound driver state saved by the game. Sound initialization and the
 * resource layer read this array.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

/*
 * Driver mode followed by configured channel counts.
 */
int far snd_driver_capabilities[7];
