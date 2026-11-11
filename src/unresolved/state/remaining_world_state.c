/*
 * Bundles tutorial and music timing, animal state, pause flags, view state and the dead ant ring
 * index. Several fields are still address named.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

long far TimeTemp;
int far BirdGoalX;
int far BirdGoalY;
int far EatCountB;
long far LastThemeTime;
int far EatCountR;
int far CatDir;
int far OldMapPlane;
int far MigrateX;
int far MigrateY;
int far DdPtr;
int far GamePaused;
int far LastMowX;
int far SaveGamePaused;
int far LastMowY;
int far MeBase;
int far RedTask;
