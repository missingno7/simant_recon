#ifndef SIMANT_ENHANCED_OVERLAYS_H
#define SIMANT_ENHANCED_OVERLAYS_H
#include "snapshot.h"
/* Passive source output taps: bracket completed edit draws, retain source
 * choices. They do not create artwork from canonical raster buffers. */
void enhanced_overlay_push(void);
void enhanced_overlay_pop(void);
void enhanced_overlay_rect(int16_t x0,int16_t y0,int16_t x1,int16_t y1,int16_t color);
void enhanced_overlay_copy(EnhancedWorldSnapshot *world);
void enhanced_yard_copy(EnhancedOverviewSnapshot *yard);
#endif
