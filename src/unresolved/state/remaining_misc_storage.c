/*
 * Bundles yard and balloon positions with pointers, a byte buffer and a tile invalidation array.
 * The file crosses several unrelated functional roles.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Pnt { int x; int y; };
struct Pnt far CurYardPnt;
struct Pnt far LastEggPnt;
struct Pnt far CurEggPnt;
struct Pnt far LastFightPnt;
struct Pnt far CurFightPnt;
char far fd_50F6_0B0A[4];
char far * far fd_50F6_0B22;
unsigned char far fd_50F6_1114[1200];
int far fd_50F6_15C4[30][40];
