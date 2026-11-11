/*
 * Defines the window master handle array used by the shipped interface. Loading, locking and
 * bitmap assignment resolve window storage through these handles.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Shipped window master handles; process-long, startup-zeroed storage.
 * Supported functional footprint, not historical allocation or placement.
 */

char far * far * near win_handles[34];
