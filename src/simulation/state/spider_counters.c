/*
 * Defines spider feeding, corpse, cycle and reaction counters. Initialization and prey handling
 * update them while drawing reads the animation state.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far DeathCnt;
int far EatCnt;
int far SCorpseBase;
int far Scycle;
int far Scycle2;
int far SpidBurpCnt;
int far SpidRevenge;
