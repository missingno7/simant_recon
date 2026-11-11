/*
 * Defines the current lengths of the surface, black nest and red nest ant lists. The simulation
 * and load initialization routines update these three counts.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far ListIndexA;
int far ListIndexB;
int far ListIndexR;
