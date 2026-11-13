/*
 * Defines the signed byte consulted by the DOS critical error handler. Its computed alias and
 * larger historical storage view remain unresolved.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Mutable minimum signed-byte view; computed alias gate remains open.
 */

char near dos_critical_error_selector;
