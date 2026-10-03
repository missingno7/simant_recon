#include "graphics_tile_upload.h"

#include "graphics_bitmap_source.h"
#include "graphics_cursor_hooks.h"
#include "graphics_source_clip.h"
#include "graphics.h"
#include "m1b73_mouse_state.h"
#include "portable/whole_program/state/asm_display_data_v1.h"

#include <stdlib.h>
#include <string.h>

/* S00 reads and writes a 64 KiB planar aperture at source segment g_3DB0=A000h.
 * It uses A000h..BFFFh for four 8 KiB tile-map planes and C000h..DFFFh for four
 * 8 KiB tile pages. Keeping the full per-plane aperture makes those source
 * offsets ordinary bounded native indices; the displayed framebuffer remains
 * the one owned by SimGraphicsDriver. */
static uint8_t s_planes[SIM_GRAPHICS_PLANAR_PLANE_COUNT]
                       [SIM_GRAPHICS_PLANAR_APERTURE_BYTES];
static SimGraphicsDriver *s_graphics_owner;
static SimGraphicsTileUploadStatus s_status = SIM_GRAPHICS_TILE_UPLOAD_NOT_BOUND;
uint16_t g_3DD4;
SimGraphicsTileBlitCallback g_917C;
SimGraphicsTileMapUploadCallback g_9180;

typedef enum TileCompositorKind {
    TILE_COMPOSITOR_2B1A,
    TILE_COMPOSITOR_1B7D,
    TILE_COMPOSITOR_303F
} TileCompositorKind;

static SimGraphicsTileUploadStatus require_owner(void)
{
    if (s_graphics_owner == NULL)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_NOT_BOUND;
    if (sim_graphics_source_owner() != s_graphics_owner ||
        s_graphics_owner->pixel_storage == NULL ||
        (s_graphics_owner->video_mode != SIM_GRAPHICS_MODE_EGA_640X350 &&
         s_graphics_owner->video_mode != SIM_GRAPHICS_MODE_VGA_640X480))
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_WRONG_VIDEO_OWNER;
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static void screen_lock_enter(void)
{
    uint8_t *low = (uint8_t *)&g_3DD4;
    low[0] = (uint8_t)(low[0] + 1u);
}

static void screen_lock_leave(void)
{
    uint8_t *low = (uint8_t *)&g_3DD4;
    low[0] = (uint8_t)(low[0] - 1u);
}

SimGraphicsTileUploadStatus sim_graphics_tile_upload_bind(SimGraphicsDriver *graphics_owner)
{
    SimGraphicsDriver *owner;
    if (graphics_owner == NULL)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    owner = sim_graphics_source_owner();
    if (owner != graphics_owner ||
        owner->pixel_storage == NULL ||
        (owner->video_mode != SIM_GRAPHICS_MODE_EGA_640X350 &&
         owner->video_mode != SIM_GRAPHICS_MODE_VGA_640X480)) {
        s_graphics_owner = NULL;
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_WRONG_VIDEO_OWNER;
    }
    s_graphics_owner = graphics_owner;
    memset(s_planes, 0, sizeof(s_planes));
    g_917C = o00_31AD_0647;
    g_9180 = o00_31AD_18BA;
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

void sim_graphics_tile_upload_unbind(void)
{
    s_graphics_owner = NULL;
    s_status = SIM_GRAPHICS_TILE_UPLOAD_NOT_BOUND;
    g_917C = NULL;
    g_9180 = NULL;
}

SimGraphicsCursorHooksStatus sim_graphics_tile_cursor_bind(
    const SimGraphicsCursorHooks *hooks)
{
    return sim_graphics_cursor_hooks_bind(hooks);
}

void sim_graphics_tile_cursor_unbind(void)
{
    sim_graphics_cursor_hooks_unbind();
}

SimGraphicsTileUploadStatus sim_graphics_tile_upload_status(void)
{
    return s_status;
}

const uint8_t *sim_graphics_tile_upload_plane(unsigned plane, size_t *size_out)
{
    if (size_out != NULL)
        *size_out = SIM_GRAPHICS_PLANAR_APERTURE_BYTES;
    if (plane >= SIM_GRAPHICS_PLANAR_PLANE_COUNT ||
        require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK) {
        if (size_out != NULL)
            *size_out = 0;
        return NULL;
    }
    return s_planes[plane];
}

SimGraphicsTileUploadStatus sim_graphics_tile_upload_read_plane(
    unsigned plane, uint16_t offset, uint8_t *destination, size_t byte_count)
{
    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK)
        return s_status;
    if (plane >= SIM_GRAPHICS_PLANAR_PLANE_COUNT ||
        (destination == NULL && byte_count != 0))
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    if (byte_count > SIM_GRAPHICS_PLANAR_APERTURE_BYTES - (size_t)offset)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;
    if (byte_count != 0)
        memcpy(destination, &s_planes[plane][offset], byte_count);
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static int16_t add_word_15(int16_t value)
{
    return (int16_t)((uint16_t)value + UINT16_C(15));
}

static int source_cursor_intersects_tile(int16_t x, int16_t y)
{
    int16_t right = add_word_15(x);
    int16_t bottom = add_word_15(y);
    return x <= (int16_t)g_4346 && right >= (int16_t)g_4340 &&
           y <= (int16_t)g_4344 && bottom >= (int16_t)g_4342;
}

static SimGraphicsTileUploadStatus source_cursor_before_tile(int16_t x,
                                                              int16_t y)
{
    if (!sim_graphics_cursor_hooks_is_bound())
        return SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_UNBOUND;
    if (g_4333 == 0 && source_cursor_intersects_tile(x, y) &&
        !sim_graphics_cursor_hooks_hide())
        return SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_FAILED;
    return SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static SimGraphicsTileUploadStatus source_cursor_after_tile(void)
{
    if (g_4333 != 0)
        return SIM_GRAPHICS_TILE_UPLOAD_OK;
    if (g_4365 != 0 && g_4331 != 0) {
        if (!sim_graphics_cursor_hooks_redraw_if_shown())
            return SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_FAILED;
    } else if (g_4365 == 0 && g_4366 == 0) {
        if (!sim_graphics_cursor_hooks_update())
            return SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_FAILED;
    }
    return SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static SimGraphicsTileUploadStatus upload_interleaved_rows(
    const uint8_t *source, size_t source_size, uint16_t destination_offset,
    uint16_t row_count)
{
    size_t needed;
    size_t row;
    unsigned plane;
    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK)
        return s_status;
    if (source == NULL || row_count == 0)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    if (destination_offset != SIM_GRAPHICS_TILE_MAP_OFFSET ||
        row_count != 0x100u)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;
    needed = (size_t)row_count * 128u;
    if (source_size != needed ||
        (size_t)destination_offset + (size_t)row_count * 32u >
            SIM_GRAPHICS_PLANAR_APERTURE_BYTES)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;

    screen_lock_enter();
    for (row = 0; row < row_count; ++row) {
        const uint8_t *row_source = source + row * 128u;
        size_t out_byte;
        for (plane = 0; plane < SIM_GRAPHICS_PLANAR_PLANE_COUNT; ++plane) {
            uint8_t *row_destination =
                &s_planes[plane][destination_offset + row * 32u];
            for (out_byte = 0; out_byte < 32u; ++out_byte) {
                /* S00 18BA selects planes 0..3 and copies one word from
                 * each 8-byte source group into consecutive aperture bytes. */
                row_destination[out_byte] = row_source[
                    (out_byte / 2u) * 8u + plane * 2u + (out_byte & 1u)];
            }
        }
    }
    screen_lock_leave();
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static SimGraphicsTileUploadStatus upload_plane_bytes(
    const uint8_t *source, size_t source_size, uint16_t destination_offset,
    unsigned plane, size_t byte_count)
{
    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK)
        return s_status;
    if (source == NULL || plane >= SIM_GRAPHICS_PLANAR_PLANE_COUNT)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    if (destination_offset != SIM_GRAPHICS_TILE_PAGE_OFFSET ||
        byte_count != SIM_GRAPHICS_TILE_UPLOAD_BYTES || source_size != byte_count ||
        (size_t)destination_offset + byte_count > SIM_GRAPHICS_PLANAR_APERTURE_BYTES)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;

    screen_lock_enter();
    memcpy(&s_planes[plane][destination_offset], source, byte_count);
    screen_lock_leave();
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

SimGraphicsTileUploadStatus sim_graphics_tile_cache_blit(
    int16_t x, int16_t y, uint16_t offset)
{
    uint8_t tile[SIM_GRAPHICS_CACHED_TILE_BYTES * 4u];
    uint16_t source_offset;
    int32_t draw_x;
    unsigned row, plane, byte;
    SimGraphicsBitmapCallback callback;
    int clipped;
    SimGraphicsTileUploadStatus cursor_status;

    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK)
        return s_status;
    if ((size_t)offset + SIM_GRAPHICS_CACHED_TILE_BYTES >
                      SIM_GRAPHICS_PLANAR_APERTURE_BYTES ||
        (offset % SIM_GRAPHICS_CACHED_TILE_BYTES) != 0 ||
        y < 0 || y >= s_graphics_owner->framebuffer.height)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;
    /* The source's first branch sends every unaligned x through 0CF9,
     * even when there is no active clipping list. */
    clipped = sim_graphics_source_clip_active() || (((uint16_t)x & 7u) != 0);
    if ((clipped ? g_914C : g_9150) == NULL)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_DRAW_UNBOUND;
    if (!sim_graphics_cursor_hooks_is_bound())
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_CURSOR_SERVICE_UNBOUND;

    /* Both source 0647 paths load SI directly from the third argument.
     * root:m0250 supplies A000h + tile*32 via 16-bit arithmetic; root:m208F
     * likewise supplies its absolute g_62BE cache address. VGA read
     * latches expose two bytes from each of the four planes per row; its
     * clipped path copies those same bytes into a 128-byte row-interleaved
     * planar bitmap before dispatching g914C/o00_31AD_0CF9. */
    source_offset = offset;
    screen_lock_enter();
    for (row = 0; row < 16u; ++row) {
        for (plane = 0; plane < SIM_GRAPHICS_PLANAR_PLANE_COUNT; ++plane) {
            const uint8_t *source = &s_planes[plane][source_offset + row * 2u];
            size_t output = row * 8u + plane * 2u;
            for (byte = 0; byte < 2u; ++byte)
                tile[output + byte] = source[byte];
        }
    }
    if (clipped)
        screen_lock_leave();
    else {
        cursor_status = source_cursor_before_tile(x, y);
        if (cursor_status != SIM_GRAPHICS_TILE_UPLOAD_OK) {
            screen_lock_leave();
            return s_status = cursor_status;
        }
    }

    /* Only the direct aperture path shifts x to a byte address. 0CF9
     * receives the original coordinate, including its low three bits. */
    draw_x = clipped ? x : (int32_t)((uint16_t)x >> 3) * 8;
    callback = clipped ? g_914C : g_9150;
    s_graphics_owner->last_status = SIM_GRAPHICS_OK;
    callback((int16_t)draw_x, y, (char *)tile, 16, 16);
    if (s_graphics_owner->last_status != SIM_GRAPHICS_OK) {
        if (!clipped)
            screen_lock_leave();
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_DRAW_FAILED;
    }
    if (!clipped) {
        cursor_status = source_cursor_after_tile();
        screen_lock_leave();
        if (cursor_status != SIM_GRAPHICS_TILE_UPLOAD_OK)
            return s_status = cursor_status;
    }
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

void o00_31AD_18BA(char *source, uint16_t destination_offset, int16_t row_count)
{
    if (upload_interleaved_rows((const uint8_t *)source,
                                (size_t)(uint16_t)row_count * 128u,
                                destination_offset,
                                (uint16_t)row_count) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_186A(char *source, uint16_t destination_offset,
                   int16_t plane, uint16_t byte_count)
{
    if (upload_plane_bytes((const uint8_t *)source, byte_count,
                           destination_offset, (unsigned)(uint16_t)plane,
                           byte_count) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_0647(int16_t x, int16_t y, uint16_t offset)
{
    if (sim_graphics_tile_cache_blit(x, y, offset) !=
        SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

static uint16_t read_le_word(const uint8_t *bytes)
{
    return (uint16_t)(bytes[0] | ((uint16_t)bytes[1] << 8));
}

static SimGraphicsTileUploadStatus compose_record(
    int16_t cache_offset, int16_t plane, const char *record,
    int16_t mask_mode, TileCompositorKind kind)
{
    const uint8_t *source = (const uint8_t *)record;
    size_t record_stride = kind == TILE_COMPOSITOR_2B1A ? 10u : 12u;
    size_t color_offset = kind == TILE_COMPOSITOR_2B1A ? 2u : 4u;
    uint16_t cache_base = (uint16_t)cache_offset;
    unsigned row, word;

    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK)
        return s_status;
    if (source == NULL || plane < 0 || plane >= SIM_GRAPHICS_PLANAR_PLANE_COUNT ||
        (kind != TILE_COMPOSITOR_2B1A &&
         mask_mode != 0 && mask_mode != 1 && mask_mode != 3) ||
        (size_t)cache_base + 0x80u > SIM_GRAPHICS_PLANAR_APERTURE_BYTES)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;

    /* The assembly selects one source plane in the EGA read-map register,
     * then consumes four words per scanline. Its source record is 16 rows of
     * either 5 words (2B1A) or 6 words (1B7D/303F); output is the existing
     * 128-byte g3D20 row-interleaved planar bitmap. */
    screen_lock_enter();
    for (row = 0; row < 16u; ++row) {
        const uint8_t *record_row = source + row * record_stride;
        uint16_t transparency = read_le_word(record_row);
        uint16_t prefix = kind == TILE_COMPOSITOR_2B1A ? 0 :
                          read_le_word(record_row + 2u);
        for (word = 0; word < 4u; ++word) {
            uint16_t background = read_le_word(
                &s_planes[(unsigned)plane][cache_base + row * 8u + word * 2u]);
            uint16_t foreground = read_le_word(
                record_row + color_offset + word * 2u);
            uint16_t result = (uint16_t)(background ^
                ((foreground ^ background) & transparency));
            int apply_prefix = 0;
            if (kind == TILE_COMPOSITOR_1B7D) {
                apply_prefix = (mask_mode == 0 && (word == 1u || word == 2u)) ||
                               (mask_mode == 3 && (word == 1u || word == 3u));
            } else if (kind == TILE_COMPOSITOR_303F) {
                apply_prefix = (mask_mode == 0) ||
                               (mask_mode == 3 && word == 1u);
            }
            if (apply_prefix)
                result ^= prefix;
            sim_asm_g3d20.bytes[row * 8u + word * 2u] = (uint8_t)result;
            sim_asm_g3d20.bytes[row * 8u + word * 2u + 1u] =
                (uint8_t)(result >> 8);
        }
    }
    screen_lock_leave();
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static SimGraphicsTileUploadStatus draw_composed_record(
    int16_t x, int16_t y, int16_t cache_offset, int16_t plane,
    char *record, int16_t mask_mode, TileCompositorKind kind)
{
    SimGraphicsTileUploadStatus status = compose_record(
        cache_offset, plane, record, mask_mode, kind);
    if (status != SIM_GRAPHICS_TILE_UPLOAD_OK)
        return status;
    if (g_914C == NULL)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_DRAW_UNBOUND;
    s_graphics_owner->last_status = SIM_GRAPHICS_OK;
    g_914C(x, y, (char *)sim_asm_g3d20.bytes, 16, 16);
    if (s_graphics_owner->last_status != SIM_GRAPHICS_OK)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_DRAW_FAILED;
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

void o00_31AD_2B1A(int16_t cache_offset, int16_t plane, char *record)
{
    if (compose_record(cache_offset, plane, record, 0,
                       TILE_COMPOSITOR_2B1A) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_2FDA(int16_t x, int16_t y, int16_t cache_offset,
                   int16_t plane, char *record)
{
    if (draw_composed_record(x, y, cache_offset, plane, record, 0,
                             TILE_COMPOSITOR_2B1A) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_1B7D(int16_t cache_offset, int16_t plane, char *record,
                   int16_t mask_mode)
{
    if (compose_record(cache_offset, plane, record, mask_mode,
                       TILE_COMPOSITOR_1B7D) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_1B49(int16_t x, int16_t y, int16_t cache_offset,
                   int16_t plane, char *record, int16_t mask_mode)
{
    if (draw_composed_record(x, y, cache_offset, plane, record, mask_mode,
                             TILE_COMPOSITOR_1B7D) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_303F(int16_t cache_offset, int16_t plane, char *record,
                   int16_t mask_mode)
{
    if (compose_record(cache_offset, plane, record, mask_mode,
                       TILE_COMPOSITOR_303F) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}

void o00_31AD_300B(int16_t x, int16_t y, int16_t cache_offset,
                   int16_t plane, char *record, int16_t mask_mode)
{
    if (draw_composed_record(x, y, cache_offset, plane, record, mask_mode,
                             TILE_COMPOSITOR_303F) != SIM_GRAPHICS_TILE_UPLOAD_OK)
        abort();
}
