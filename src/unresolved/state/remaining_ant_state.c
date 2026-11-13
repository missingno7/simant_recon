/*
 * Bundles balloon points and planes, yellow ant modes, game time and several opaque words. The
 * consumers span rendering, editing and simulation without a sufficiently established common
 * file purpose.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef struct { int x; int y; } Pnt;
typedef union { long signed_view; unsigned long unsigned_view; } CountViews;
Pnt far LastQueenPnt;
Pnt far CurQueenPnt;
Pnt far LastRestPnt;
Pnt far CurRestPnt;
int far MeMode;
/*
 * Simulation phase, wrapped to six bits by the main loop.
 */
int far main_cycle_phase;
int far fd_50F6_0AA6;
int far LastEggPlane;
int far CurEggPlane;
int far LastFightPlane;
int far CurFightPlane;
int far LastQueenPlane;
int far CurQueenPlane;
int far LastRestPlane;
int far MeCrazyCnt;
int far WantSpiderBalloon;
int far CurEditMode;
CountViews far GameTime;
