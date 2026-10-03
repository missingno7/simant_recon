#include "graphics_source_slots.h"
#include "portable/whole_program/window_source_rects.h"

/* One native owner for source-root graphics callback and associated working
 * state. Each callback is filled by the original source m205F selection path. */
SimSourceRectCopyCallback fd_50F6_37EE;
SimSourceRasterCallback fd_50F6_37EA;
SimSourceRasterCallback fd_50F6_3B58;
SimSourcePatternTransferCallback fd_50F6_37E6;

struct Rect fd_50F6_37D6;
SimSourceHandle fd_50F6_37DE;
SimSourceHandle fd_50F6_37F2;
SimSourceHandle fd_50F6_37F6;
int16_t fd_50F6_37FC;
