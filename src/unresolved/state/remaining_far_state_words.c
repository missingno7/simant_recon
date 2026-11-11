/*
 * Bundles view row and column counts with three address named words. Their uses span startup,
 * yard simulation and view bounds.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far fd_50F6_04C0;
int far GlobalKey;
int far vScrollMax;
int far EditColumns;
int far EditRows;
