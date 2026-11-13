/*
 * Defines the current DOS display mode selector. The driver selector sets it and drawing code
 * uses it to choose pixel and font formats.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 * The initial value -1 is the original file byte and the sentinel the driver selector tests.
 */

/* -1 means "not configured": the driver selector auto-detects the display only while the
 * byte is still -1 (driver_select.c); the original file holds FF here (55B3:5A97). */
/*
 * Display-driver mode used to choose raster and tile formats.
 */
char near gfx_display_mode = -1;
