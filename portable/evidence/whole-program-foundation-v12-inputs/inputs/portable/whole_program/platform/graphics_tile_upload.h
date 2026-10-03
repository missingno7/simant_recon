#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_TILE_UPLOAD_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_TILE_UPLOAD_H

#include <stddef.h>
#include <stdint.h>

#include "graphics.h"
#include "graphics_cursor_hooks.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    SIM_GRAPHICS_PLANAR_PLANE_COUNT = 4,
    SIM_GRAPHICS_PLANAR_APERTURE_BYTES = 0x10000,
    SIM_GRAPHICS_TILE_MAP_UPLOAD_BYTES = 0x8000,
    SIM_GRAPHICS_TILE_UPLOAD_BYTES = 0x2000,
    SIM_GRAPHICS_CACHED_TILE_BYTES = 0x20,
    SIM_GRAPHICS_CACHED_TILE_COUNT = 0x100,
    SIM_GRAPHICS_TILE_MAP_OFFSET = 0xA000,
    SIM_GRAPHICS_TILE_PAGE_OFFSET = 0xC000
};

typedef enum SimGraphicsTileUploadStatus {
    SIM_GRAPHICS_TILE_UPLOAD_OK = 0,
    SIM_GRAPHICS_TILE_UPLOAD_NOT_BOUND,
    SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT,
    SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE,
    SIM_GRAPHICS_TILE_UPLOAD_WRONG_VIDEO_OWNER,
    SIM_GRAPHICS_TILE_UPLOAD_DRAW_UNBOUND,
    SIM_GRAPHICS_TILE_UPLOAD_DRAW_FAILED,
    SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_UNBOUND,
    SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_FAILED
} SimGraphicsTileUploadStatus;

/* Canonical source word at DGROUP:3DD4, updated as byte low-order lock depth. */
extern uint16_t g_3DD4;
typedef void (*SimGraphicsTileBlitCallback)(int16_t x, int16_t y,
                                            uint16_t cache_offset);
typedef void (*SimGraphicsTileMapUploadCallback)(char *source,
                                                 uint16_t destination_offset,
                                                 int16_t row_count);
extern SimGraphicsTileBlitCallback g_917C;
extern SimGraphicsTileMapUploadCallback g_9180;

/* Bind the four source planes to the current native graphics owner. These are
 * offscreen planar aperture bytes, not another displayed framebuffer. */
SimGraphicsTileUploadStatus sim_graphics_tile_upload_bind(SimGraphicsDriver *graphics_owner);
void sim_graphics_tile_upload_unbind(void);
SimGraphicsTileUploadStatus sim_graphics_tile_upload_status(void);
/* The full app binds these to the active m1B73 mouse runtime before any tile
 * drawing. All three callbacks are mandatory even when current cursor state
 * does not require a transition; absence fails closed. */
SimGraphicsCursorHooksStatus sim_graphics_tile_cursor_bind(
    const SimGraphicsCursorHooks *hooks);
void sim_graphics_tile_cursor_unbind(void);

/* Bounded owner view used by source read-plane providers and tests. The only
 * exposed size is the actual 64 KiB source aperture per plane. */
const uint8_t *sim_graphics_tile_upload_plane(unsigned plane, size_t *size_out);
SimGraphicsTileUploadStatus sim_graphics_tile_upload_read_plane(
    unsigned plane, uint16_t offset, uint8_t *destination, size_t byte_count);

/* Source ABI entries reached by root:m0250 f_0250_0256 / LoadTiles. In the
 * first routine, the source's second argument is a destination offset (despite
 * the old C declaration's `seg` name); in the second, the third argument is the
 * sequencer plane index. The global source video segment remains A000h. The
 * first source object is 0x8000 bytes, deinterleaved into four 0x2000 planes. */
void o00_31AD_18BA(char *source, uint16_t destination_offset, int16_t row_count);
void o00_31AD_186A(char *source, uint16_t destination_offset,
                   int16_t plane, uint16_t byte_count);

/* Source driver dispatch slot g917C, S00 o00_31AD_0647. `offset` is the
 * byte offset of one 16x16 tile in the four-plane C000h cache. */
SimGraphicsTileUploadStatus sim_graphics_tile_cache_blit(
    int16_t x, int16_t y, uint16_t offset);
void o00_31AD_0647(int16_t x, int16_t y, uint16_t offset);

/* Source terrain/life compositors. The 0xA0 record has a 10-byte row
 * (mask word + four pixel words); 0xC0 records have a 12-byte row (mask,
 * source color/prefix, and four pixel words). */
void o00_31AD_2B1A(int16_t cache_offset, int16_t plane, char *record);
void o00_31AD_2FDA(int16_t x, int16_t y, int16_t cache_offset,
                   int16_t plane, char *record);
void o00_31AD_1B7D(int16_t cache_offset, int16_t plane, char *record,
                   int16_t mask_mode);
void o00_31AD_1B49(int16_t x, int16_t y, int16_t cache_offset,
                   int16_t plane, char *record, int16_t mask_mode);
void o00_31AD_303F(int16_t cache_offset, int16_t plane, char *record,
                   int16_t mask_mode);
void o00_31AD_300B(int16_t x, int16_t y, int16_t cache_offset,
                   int16_t plane, char *record, int16_t mask_mode);

#ifdef __cplusplus
}
#endif
#endif
