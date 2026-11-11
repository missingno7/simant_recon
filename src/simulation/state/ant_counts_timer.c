/*
 * Defines the two eaten ant counters and one long timer used by balloon drawing. The counter and
 * display timer storage remain bundled in this modern file.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

long far BAntsEaten;
long far RAntsEaten;
long far fd_50F6_0620;
