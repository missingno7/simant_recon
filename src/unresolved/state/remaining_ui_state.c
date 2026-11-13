/*
 * Bundles balloon, tutorial, bird, strategy and tile view state. Several resource handles and
 * dimensions are still identified only by address.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef char far * far *Handle;
int far WantQueenBalloon;
int far WantRFightBalloon;
unsigned char far fd_50F6_106C;
int far LessonTemp;
int far WantRestBalloon;
int far fd_50F6_1092;
int far StrategicModeR;
int far BirdX;
int far TutHowLong;
int far BirdY;
Handle far fd_50F6_10CC;
int far fd_50F6_10D0;
Handle far yardAnimHandle;
int far fd_50F6_10DE;
int far fd_50F6_10E0;
char far * far * far fd_50F6_10E2;
Handle far fd_50F6_10E6;
Handle far fd_50F6_10EA;
Handle far fd_50F6_10EE;
int far fd_50F6_1102;
