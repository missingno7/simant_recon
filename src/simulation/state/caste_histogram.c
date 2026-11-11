/*
 * Defines the 32 entry scratch histogram updated by CountAnts. It supplies working storage for
 * class counting rather than an independently established historical data object.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * No historical COMDEF-producing file, absolute placement, initialization
 * state or adjacency is established by this functional scratch allocation.
 */

int far fd_50F6_0EB6[32];
