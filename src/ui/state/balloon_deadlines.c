/*
 * Defines four long deadlines checked while drawing current speech balloons. The display code
 * compares them with TickCount to manage message timing.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

long far fd_50F6_050C;
long far fd_50F6_059A;
long far fd_50F6_0732;
long far fd_50F6_07C4;
