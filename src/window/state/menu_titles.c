/*
 * Defines the two menu title geometry arrays. Menu initialization and tracking use the five
 * functional title slots.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Supported five-title shipped menu geometry, with static storage duration.
 * Functional source ownership; no historical producer or capacity claim.
 */

int far fd_50F6_46A8[5];
int far fd_50F6_46BC[5];
