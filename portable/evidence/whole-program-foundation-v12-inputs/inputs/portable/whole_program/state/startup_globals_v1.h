#ifndef SIMANT_STARTUP_GLOBALS_V1_H
#define SIMANT_STARTUP_GLOBALS_V1_H

#include <stdint.h>
#include "yard_cache_globals_v1.h"

/* Original resident startup values observed in fresh DOS process state.
 * This is a native logical owner, not a DOS DGROUP/far-pointer layout claim. */
typedef struct SimStartupPointV1 { int16_t x; int16_t y; } SimStartupPointV1;
extern char fd_50F6_0B0A[4];
extern int16_t fd_50F6_0F7A;
extern uint8_t fd_50F6_106C;
extern char g_8CCB;

#endif
