/*
 * Defines black and red colony mode population vectors and additional mode work counts. The
 * simulation clears and tallies these arrays before strategy and control drawing use them.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far ModePopB[6];
int far ModePopR[6];
int far TemBModePop[20];
int far TemRModePop[20];
