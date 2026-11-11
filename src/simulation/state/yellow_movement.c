/*
 * Defines yellow ant direction, scent, appearance and target state. It also stores the previous
 * position, movement goal and alarm or fight flags.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far MeDir;
int far MeType;
int far MeScent;
int far MeColor;
int far MeTargIndex;
int far MeTargLife;
int far MeTargLifePlane;
int far MeTargLifeX;
int far MeTargLifeY;
int far MeLastX;
int far MeLastY;
int far MeGoalX;
int far MeGoalY;
int far MeGoalPlane;
int far MeDropAlarm;
int far MeStartedFight;
