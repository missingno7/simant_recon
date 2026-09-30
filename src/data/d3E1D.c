/* Data-only translation unit (hypothesis): colony maps and ant lists.  MSC 6 closes the
 * far data segment at 0xF89F bytes and opens a second one for PherMapRT (frame 4DA7). */

unsigned char far fd_3E1D_0000[384] = { 0 };
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
unsigned char far fd_3E1D_C89F[2048] = { 0 };
unsigned char far PherMapA[2048] = { 0 };
unsigned char far fd_3E1D_D89F[2048] = { 0 };
unsigned char far PherMapBN[2048] = { 0 };
unsigned char far PherMapBT[2048] = { 0 };
unsigned char far PherMapRN[2048] = { 0 };
unsigned char far PherMapRT[0x800] = { 0 };
char far fd_4DA7_0800[256] = "pSimAnt\252 Saved Game";
