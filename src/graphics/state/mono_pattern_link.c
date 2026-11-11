/*
 * Defines a minimal monochrome pattern linkage symbol for the supported VGA build. The current
 * functional domain performs no data access through it.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Minimal linkage owner; the supported VGA8 domain performs no data access.
 */

unsigned char near g_8ED8[1];
