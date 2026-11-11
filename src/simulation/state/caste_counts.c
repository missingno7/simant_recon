/*
 * Defines the black and red colony caste population work vectors. The simulation, caste display
 * and saved game code read these independently saved arrays.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The two caste vectors are saved independently.
 */

int far CastePopB[6];
int far CastePopR[6];
