/*
 * Defines four persistent swarm byte buffers. Yard swarm code and the saved game schema use the
 * fifty byte views.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * No game code or inferred padding is defined here.
 */

unsigned char far SwarmXB[50];
unsigned char far SwarmYB[50];
unsigned char far SwarmXR[50];
unsigned char far SwarmYR[50];
