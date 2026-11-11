/*
 * Defines cat, rain and foot state together with the two colony totals. Yard simulation, drawing
 * and save loading share these eight scalar objects.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Consumers use signed 16-bit scalars; SaveRec stores one two-byte view
 * at each registered base. Original owner, order and values remain unproven.
 */

int far CatOn;
int far CatX;
int far CatY;
int far RainOn;
int far RainCnt;
int far FootX;
int far ColonyTotalBlack;
int far ColonyTotalRed;
