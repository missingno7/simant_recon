/*
 * Defines ant lion list fields, pill bug map state and moving surface creature positions. The
 * corresponding creature initialization and movement routines share these arrays and scalars.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

unsigned char far LionListM[10];
unsigned char far LionListS[10];
unsigned char far LionListT[10];
unsigned char far LionListX[10];
unsigned char far LionListY[10];
int far PillDir;
int far PillarSeg;
int far PillarMap[6];
int far SowDir[3];
int far SowSave[3];
int far SowX[3];
int far SowY[3];
