/*
 * Defines far pointer and counter storage used by the allocator and EMS database cache. The
 * fields remain independent objects in this mixed modern bundle.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The definitions are five independent far commons.
 */

unsigned far fd_50F6_394C;
unsigned far fd_50F6_394E;
unsigned far fd_50F6_3950;
/* Both the pointer object and its pointee type are far; the object itself is FAR_BSS. */
char far * far fd_50F6_3948;
char far * far fd_50F6_3B48;
