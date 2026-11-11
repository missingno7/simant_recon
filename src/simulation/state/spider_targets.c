/*
 * Defines spider mode, user coordinates and target state. Spider commands and hunting logic
 * update these six control words.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far ChaseSpid;
int far SMode;
int far SuserX;
int far SuserY;
int far Starg;
int far StargLife;
