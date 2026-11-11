/*
 * Defines the delay word used by a window helper that waits for a deadline or keypress. One
 * function sets the delay and another tests it against the elapsed tick count.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far fd_50F6_46D0;
