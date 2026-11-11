/*
 * Defines the twenty four byte leading view of monochrome pattern storage. LoadMonoPats fills
 * this registered prefix.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

unsigned char near g_8EC0[24];
