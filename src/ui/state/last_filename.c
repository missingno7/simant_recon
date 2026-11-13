/*
 * Defines the saved file selector filename pointer. The load and save file selection path uses
 * it to retain the last chosen name.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

/*
 * Most recent save/load pathname; original buffer extent remains uncertain.
 */
char far save_last_filename[100];
