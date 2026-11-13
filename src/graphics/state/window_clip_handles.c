/*
 * Defines the per-window clip list handles. clip_SetWin uses the functional forty five entry
 * array.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef char far * far *Handle;
Handle far clip_window_list_handles[45];
