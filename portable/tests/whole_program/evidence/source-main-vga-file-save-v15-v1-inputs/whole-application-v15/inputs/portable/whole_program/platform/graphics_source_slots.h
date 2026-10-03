#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_SOURCE_SLOTS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_SOURCE_SLOTS_H

#include <stdint.h>

struct Rect;
typedef char **SimSourceHandle;

#ifdef __cplusplus
extern "C" {
#endif

/* Source root:m205F selects these four callback cells for S00/EGA/VGA.
 * The signatures follow the source consumers in m0250/m2662 and the exact
 * selected ASM leaves in S00/m35A6. */
typedef void (*SimSourceRectCopyCallback)(void *source_rect,
                                           void *source,
                                           void *clip_rect,
                                           void *destination);
typedef void (*SimSourceRasterCallback)(void *image, void *buffer,
                                         int16_t x_shift,
                                         int16_t y_flag);
typedef void (*SimSourcePatternTransferCallback)(void *destination,
                                                  int16_t pixel_width);

extern SimSourceRectCopyCallback fd_50F6_37EE;
extern SimSourceRasterCallback fd_50F6_37EA;
extern SimSourceRasterCallback fd_50F6_3B58;
extern SimSourcePatternTransferCallback fd_50F6_37E6;

/* Shared source storage used by the selected callbacks and raster setup.
 * fd_37DE and the animation-set cells are native handle identities, not
 * serialized DOS far-pointer words. */
extern struct Rect fd_50F6_37D6;
extern SimSourceHandle fd_50F6_37DE;
extern SimSourceHandle fd_50F6_37F2;
extern SimSourceHandle fd_50F6_37F6;
extern int16_t fd_50F6_37FC;
/* fd_50F6_37FA remains in source_state_owners.c as the existing word owner. */
extern int16_t fd_50F6_37FA;

#ifdef __cplusplus
}
#endif
#endif
