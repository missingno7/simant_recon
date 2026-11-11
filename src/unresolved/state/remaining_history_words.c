/*
 * Bundles game type, balloon counts, spider and rebirth coordinates and scroll limits. These
 * fields serve several simulation and view tasks.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far CurGameType;
int far fd_50F6_0EB4;
int far EggBalloonCnt;
int far MeCrazyDir;
int far MeCrazyRot;
int far FightBalloonCnt;
int far SpidOn;
int far RebornX;
int far QueenBalloonCnt;
int far SpidX;
int far RebornY;
int far RestBalloonCnt;
int far SpidY;
int far hScrollMax;
int far fd_50F6_0F3C;
int far YellowDied;
int far fd_50F6_0F7A;
int far fd_50F6_0FC0;
