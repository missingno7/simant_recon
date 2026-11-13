/*
 * Defines the handle cell used by the window icon helper. The source keeps this as a single
 * handle view.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Minimum mutable Handle slot; referent and physical-alias gates remain open.
 */

char far * far * far ui_icon_bitmap_handle;
