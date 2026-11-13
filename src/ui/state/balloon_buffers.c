/*
 * Defines six message balloon buffers and their positions and attributes. AddMsgBalloon fills
 * these tables for later rendering.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef struct Pnt { int x; int y; } Pnt;
char far * far CurBalloonMsgs[6];
Pnt far CurBalloonPnts[6];
int far CurBalloonFlags[6];
int far CurBalloonPlane[6];
