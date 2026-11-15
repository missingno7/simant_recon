#ifndef SIMANT_ENHANCED_WORLD_H
#define SIMANT_ENHANCED_WORLD_H
#include "snapshot.h"
#include "portable/whole_program/modern/world_view.h"
void enhanced_world_cell(const EnhancedWorldSnapshot *w,int plane,int x,int y,ModernCell *cell);
/* Return painted world bounds (exclusive right/bottom); empty if none. */
EnhancedRect enhanced_world_draw(const EnhancedWorldSnapshot *w,uint8_t *pixels,int width,int height,int stride);
void enhanced_yard_draw(const EnhancedOverviewSnapshot *y,uint8_t *pixels,int width,int height,int stride);
#endif
