#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_S00_RASTER_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_S00_RASTER_SOURCE_H

#include <stddef.h>
#include <stdint.h>
#include "portable/whole_program/window_source_rects.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct Rect SimS00SourceRect;

/* Native semantic helpers for the S00 fallback callback leaves. Buffers use
 * the source four-byte little-endian [width,height] header followed by the
 * source planar row data. Sizes are explicit at this helper boundary. */
typedef enum SimS00RasterStatus {
    SIM_S00_RASTER_OK = 0,
    SIM_S00_RASTER_INVALID_ARGUMENT,
    SIM_S00_RASTER_BUFFER_TOO_SMALL = 3
} SimS00RasterStatus;

SimS00RasterStatus sim_s00_raster_copy_rect(
    const SimS00SourceRect *source_rect, const uint8_t *source,
    size_t source_size, const SimS00SourceRect *clip_rect,
    uint8_t *destination, size_t destination_size);

SimS00RasterStatus sim_s00_raster_masked_blit(
    const uint8_t *image, size_t image_size, uint8_t *buffer,
    size_t buffer_size, int16_t shift, int16_t row_offset);

SimS00RasterStatus sim_s00_raster_opaque_blit(
    const uint8_t *image, size_t image_size, uint8_t *buffer,
    size_t buffer_size, int16_t shift, int16_t row_offset);

SimS00RasterStatus sim_s00_raster_pattern_transfer(
    const uint8_t pattern[128], uint8_t *destination,
    size_t destination_size, uint16_t width);

/* Source-compatible S00 selected callback targets. They share the existing
 * graphics state and source g_3D20 pattern owner; none owns a framebuffer. */
void o00_35A6_02FD(void *source_rect, void *source,
                    void *clip_rect, void *destination);
void o00_35A6_0007(void *image, void *buffer, int16_t shift, int16_t row_offset);
void o00_35A6_0177(void *image, void *buffer, int16_t shift, int16_t row_offset);
void o00_35A6_0406(void *destination, int16_t width);

#ifdef __cplusplus
}
#endif
#endif
