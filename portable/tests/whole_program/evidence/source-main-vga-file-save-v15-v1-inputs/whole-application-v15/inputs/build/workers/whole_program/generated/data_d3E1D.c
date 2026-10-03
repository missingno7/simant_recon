#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Data-only translation unit (hypothesis): colony maps and ant lists.  MSC 6 closes the
 * far data segment at 0xF89F bytes and opens a second one for PherMapRT (frame 4DA7). */

uint8_t  fd_3E1D_0000[384] = { 0 };
uint8_t  MapA[8192] = { 0 };
uint8_t  MapB[4096] = { 0 };
uint8_t  MapR[4096] = { 0 };
uint8_t  ExitMapB[4096] = { 0 };
uint8_t  ExitMapR[4096] = { 0 };
uint8_t  LifeA[8192] = { 0 };
uint8_t  LifeB[4096] = { 0 };
uint8_t  LifeR[4096] = { 0 };
uint8_t  AlistX[1001] = { 0 };
uint8_t  AlistY[1001] = { 0 };
uint8_t  AlistM[1001] = { 0 };
uint8_t  AlistT[1001] = { 0 };
uint8_t  AlistS[1001] = { 0 };
uint8_t  BlistX[501] = { 0 };
uint8_t  BlistY[501] = { 0 };
uint8_t  BlistM[501] = { 0 };
uint8_t  BlistT[501] = { 0 };
uint8_t  BlistS[501] = { 0 };
uint8_t  RlistX[501] = { 0 };
uint8_t  RlistY[501] = { 0 };
uint8_t  RlistM[501] = { 0 };
uint8_t  RlistT[501] = { 0 };
uint8_t  RlistS[501] = { 0 };
uint8_t  fd_3E1D_C89F[2048] = { 0 };
uint8_t  PherMapA[2048] = { 0 };
uint8_t  fd_3E1D_D89F[2048] = { 0 };
uint8_t  PherMapBN[2048] = { 0 };
uint8_t  PherMapBT[2048] = { 0 };
uint8_t  PherMapRN[2048] = { 0 };
uint8_t  PherMapRT[0x800] = { 0 };
char  fd_4DA7_0800[256] = "pSimAnt\252 Saved Game";

#pragma pack(pop)
