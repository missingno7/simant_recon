/*
 * Defines six player and colony state words. They cover fuzzy location, yellow ant health,
 * automatic mode, black colony strategy and the red digging count.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far FuzLocX;
int far FuzLocY;
int far MeHealth;
int far ModeAuto;
int far StrategicModeB;
int far TilesDugR;
