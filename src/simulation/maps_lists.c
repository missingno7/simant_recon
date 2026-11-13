/*
 * Defines the large colony maps, life and pheromone arrays and ant lists, along with a saved
 * game header string. The compiler emits two far data segments from this one file.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident data extension, section 27; segments 3E1D:0000, 4DA7:0000. Data contributions
 * are exact; original translation unit completeness is unproven.
 * Windows: unknown; this storage file has no functions to pair.
 *
 * The data-only file grouping is a hypothesis. MSC closes the first far data
 * segment at 0xF89F bytes and opens frame 4DA7 for PherMapRT (FARSEG-1).
 */

/*
 * World-generation seeds indexed by yard row and column.
 */
unsigned char far YMapSeeds[384] = { 0 };
unsigned char far MapA[8192] = { 0 };
unsigned char far MapB[4096] = { 0 };
unsigned char far MapR[4096] = { 0 };
unsigned char far ExitMapB[4096] = { 0 };
unsigned char far ExitMapR[4096] = { 0 };
unsigned char far LifeA[8192] = { 0 };
unsigned char far LifeB[4096] = { 0 };
unsigned char far LifeR[4096] = { 0 };
unsigned char far AlistX[1001] = { 0 };
unsigned char far AlistY[1001] = { 0 };
unsigned char far AlistM[1001] = { 0 };
unsigned char far AlistT[1001] = { 0 };
unsigned char far AlistS[1001] = { 0 };
unsigned char far BlistX[501] = { 0 };
unsigned char far BlistY[501] = { 0 };
unsigned char far BlistM[501] = { 0 };
unsigned char far BlistT[501] = { 0 };
unsigned char far BlistS[501] = { 0 };
unsigned char far RlistX[501] = { 0 };
unsigned char far RlistY[501] = { 0 };
unsigned char far RlistM[501] = { 0 };
unsigned char far RlistT[501] = { 0 };
unsigned char far RlistS[501] = { 0 };
/*
 * Snapshot of PherMapA used while averaging neighboring cells.
 */
unsigned char far pheromone_diffusion_snapshot[2048] = { 0 };
unsigned char far PherMapA[2048] = { 0 };
unsigned char far PherMapF[2048] = { 0 };
unsigned char far PherMapBN[2048] = { 0 };
unsigned char far PherMapBT[2048] = { 0 };
unsigned char far PherMapRN[2048] = { 0 };
unsigned char far PherMapRT[0x800] = { 0 };
char far fd_4DA7_0800[256] = "pSimAnt\252 Saved Game";
