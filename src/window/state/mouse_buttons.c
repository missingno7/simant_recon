/*
 * Defines mouse position and button tracking words used by the interface. GetMousePos, StillDown
 * and window resizing consume these values.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * These are three independent tentative near-word definitions, not an
 * aggregate; original COMDEF-producing file and allocation order are unproven.
 */

int near g_9120;
int near g_9122;
int near g_9124;
