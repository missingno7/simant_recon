/*
 * Bundles MIDI scheduler state with font pointers, an animation object pointer and a window
 * geometry point. These independent fields have no established historical grouping.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Pt { int x; int y; };
struct AnimObj;
struct Pt far fd_50F6_47DA;
void far * far fd_50F6_4A1A[4];
struct AnimObj far * far fd_50F6_4A42;
char far * far * far fd_50F6_4B28;
int far fd_50F6_4B2C;
int far fd_50F6_4B2E;
long far fd_50F6_4B8A;
int far fd_50F6_4B8E[14];
int far fd_50F6_4BAA[14];
