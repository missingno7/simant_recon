/*
 * Defines arrays used for yard animation and drawing. The yard update and Draw_SimYard routines
 * index these work tables.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far fd_50F6_0334[12];
int far fd_50F6_38CA[15];
int far fd_50F6_38E8[17];
int far fd_50F6_390A[17];
