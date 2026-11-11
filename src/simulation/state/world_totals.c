/*
 * Defines world food, water, queen and digging totals together with colony outcome flags. The
 * same bundle includes the editor message delay value.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far TileMassXR;
int far TileMassYR;
int far TilesDugB;
int far WaterTable;
int far BlkQueens;
int far RedQueens;
/* The source graph declares both long views; all four observed stores write zero. */
typedef union { long signed_view; unsigned long unsigned_view; } FAR_LONG_VIEWS;
FAR_LONG_VIEWS far EditMsgDelay;
int far BlackLost;
int far RedLost;
int far FoodA;
long far TileTotXB;
long far TileTotYB;
long far TileTotXR;
long far TileTotYR;
int far TileMassXB;
int far TileMassYB;
