/*
 * Defines history position, colony outcome counters and overall score. It also stores ant deaths
 * and black colony egg totals used by scoring and history displays.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The fields are independent scalars, not a history struct.
 */

int far HistStart;
int far BColoniesStarted;
int far BColoniesKilled;
int far RColoniesStarted;
int far RColoniesKilled;
long far OverallScore;
long far BAntsKilled;
long far BAntsExpired;
long far RAntsKilled;
long far RAntsExpired;
long far TotalEggsLaidB;
long far TotalEggsDiedB;
