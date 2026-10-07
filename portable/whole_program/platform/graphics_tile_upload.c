extern void (*driver_callback_table[25])();
#include "graphics_tile_upload.h"

#include "graphics_bitmap_source.h"
#include "graphics_cursor_hooks.h"
#include "graphics_source_clip.h"
#include "graphics.h"
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/window_source_globals.h"
#include "m1b73_mouse_state.h"
#include "portable/whole_program/state/asm_display_data_v1.h"

#include <stdlib.h>
#include <string.h>

/* The screen and cache addresses are views of the same VGA CPU aperture. */
#define s_planes (s_graphics_owner->vga.planes)
static SimGraphicsDriver *s_graphics_owner;
static SimGraphicsTileUploadStatus s_status = SIM_GRAPHICS_TILE_UPLOAD_NOT_BOUND;
extern uint16_t g_3DD4;
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
    (*( SimGraphicsTileBlitCallback *)(void *)&driver_callback_table[21]) = o00_31AD_0647;
    (*( SimGraphicsTileMapUploadCallback *)(void *)&driver_callback_table[22]) = o00_31AD_18BA;
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

void sim_graphics_tile_upload_unbind(void)
{
    s_graphics_owner = NULL;
    s_status = SIM_GRAPHICS_TILE_UPLOAD_NOT_BOUND;
    (*( SimGraphicsTileBlitCallback *)(void *)&driver_callback_table[21]) = NULL;
    (*( SimGraphicsTileMapUploadCallback *)(void *)&driver_callback_table[22]) = NULL;
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
    if (destination == NULL && byte_count != 0)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    if (byte_count > SIM_GRAPHICS_PLANAR_APERTURE_BYTES)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_RANGE;
    /* Read-map selection masks to two bits in the hardware; REP MOVSW
     * advances a word-sized SI through the entire CPU aperture. */
    sim_vga_out(&s_graphics_owner->vga,0x3ce,4);
    sim_vga_out(&s_graphics_owner->vga,0x3cf,(uint8_t)plane);
    for (size_t byte=0;byte<byte_count;++byte)
        destination[byte]=sim_vga_read(&s_graphics_owner->vga,(uint16_t)(offset+byte));
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
    unsigned row, plane, byte;
    SimVga *vga;
    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK) return s_status;
    if (!source || source_size < (size_t)row_count*128u)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    vga = &s_graphics_owner->vga;
    screen_lock_enter();
    /* m31AD:18BA selects each map-mask plane, then copies one source word
     * per 8-byte group. Both SI and DI are 16-bit offsets. */
    /* Its 142B prologue selects mode 0 and clears logical rotation; 18BA
     * then disables set/reset before transferring the CPU color bytes. */
    sim_vga_out(vga,0x3ce,5); sim_vga_out(vga,0x3cf,0);
    sim_vga_out(vga,0x3ce,1); sim_vga_out(vga,0x3cf,0);
    sim_vga_out(vga,0x3ce,3); sim_vga_out(vga,0x3cf,0);
    sim_vga_out(vga,0x3ce,8); sim_vga_out(vga,0x3cf,255);
    for (plane = 0; plane < 4; ++plane) {
        sim_vga_out(vga,0x3c4,2); sim_vga_out(vga,0x3c5,(uint8_t)(1u<<plane));
        for (row = 0; row < row_count; ++row) for (byte = 0; byte < 32; ++byte) {
            uint16_t di = (uint16_t)(destination_offset+row*32u+byte);
            uint16_t si = (uint16_t)(row*128u+(byte/2u)*8u+plane*2u+(byte&1u));
            sim_vga_write(vga,di,source[si]);
        }
    }
    sim_vga_out(vga,0x3ce,5); sim_vga_out(vga,0x3cf,0);
    screen_lock_leave();
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

static SimGraphicsTileUploadStatus upload_plane_bytes(
    const uint8_t *source, size_t source_size, uint16_t destination_offset,
    unsigned plane, size_t byte_count)
{
    size_t byte;
    SimVga *vga;
    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK) return s_status;
    if (!source || source_size < byte_count) return s_status = SIM_GRAPHICS_TILE_UPLOAD_BAD_ARGUMENT;
    vga = &s_graphics_owner->vga;
    screen_lock_enter();
    /* m31AD:186A: SHL AL,CL produces a map mask, not a plane-range test. */
    sim_vga_out(vga,0x3ce,8); sim_vga_out(vga,0x3cf,255);
    sim_vga_out(vga,0x3c4,2);
    sim_vga_out(vga,0x3c5, (plane & 31u) < 8u ? (uint8_t)(1u << (plane & 31u)) : 0);
    /* L18A8's JCXZ after SHR intentionally drops the remaining lone byte.
     * Preserve that historical small-count case instead of a generic memcpy. */
    if ((destination_offset & 1u) && byte_count == 2u) byte_count = 1u;
    else if (!(destination_offset & 1u) && byte_count == 1u) byte_count = 0;
    for (byte = 0; byte < byte_count; ++byte)
        sim_vga_write(vga,(uint16_t)(destination_offset+byte),source[(uint16_t)byte]);
    screen_lock_leave();
    return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
}

SimGraphicsTileUploadStatus sim_graphics_tile_cache_blit(
    int16_t x, int16_t y, uint16_t offset)
{
    SimVga *vga;
    uint16_t si = offset, di;
    uint8_t tile[128];
    unsigned row, plane, byte;
    int clipped = ((uint16_t)x & 7u) != 0;
    SimGraphicsTileUploadStatus cursor_status;
    if (require_owner() != SIM_GRAPHICS_TILE_UPLOAD_OK) return s_status;
    vga = &s_graphics_owner->vga;
    /* m31AD:L066F..L0707. No intersecting clip returns without reading the
     * aperture. A containing clip uses the direct latch-copy path. */
    if (!clipped && sim_graphics_source_clip_active()) {
        const struct Rect *r = g_5AAC;
        int16_t right = add_word_15(x), bottom = add_word_15(y);
        while (r->top != INT16_MIN) {
            if (r->bottom >= y && r->right >= x && r->left <= right && r->top <= bottom) break;
            ++r;
        }
        if (r->top == INT16_MIN) return s_status = SIM_GRAPHICS_TILE_UPLOAD_OK;
        clipped = r->bottom < bottom || r->top > y || r->left > x || r->right <= right;
    }
    if (clipped) {
        SimGraphicsBitmapCallback callback = (*(SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9]);
        if (!callback) return s_status = SIM_GRAPHICS_TILE_UPLOAD_DRAW_UNBOUND;
        screen_lock_enter();
        /* L06C8/L06CB: read-map selection and MOVSW from each of four planes. */
        for (row = 0; row < 16; ++row) {
            for (plane = 0; plane < 4; ++plane) {
                sim_vga_out(vga,0x3ce,4); sim_vga_out(vga,0x3cf,(uint8_t)plane);
                for (byte = 0; byte < 2; ++byte)
                    tile[row*8u+plane*2u+byte] = sim_vga_read(vga,(uint16_t)(si+byte));
            }
            si = (uint16_t)(si+2u);
        }
        screen_lock_leave();
        s_graphics_owner->last_status = SIM_GRAPHICS_OK;
        callback(x,y,(char *)tile,16,16);
        return s_status = s_graphics_owner->last_status == SIM_GRAPHICS_OK ?
            SIM_GRAPHICS_TILE_UPLOAD_OK : SIM_GRAPHICS_TILE_UPLOAD_DRAW_FAILED;
    }
    screen_lock_enter();
    cursor_status = source_cursor_before_tile(x,y);
    if (cursor_status != SIM_GRAPHICS_TILE_UPLOAD_OK) { screen_lock_leave(); return s_status = cursor_status; }
    /* L0740..L0800: map-mask=0F, write-mode=1, two MOVSB per scanline.
     * The CPU byte is ignored in mode 1; every plane copies its read latch. */
    sim_vga_out(vga,0x3c4,2); sim_vga_out(vga,0x3c5,15);
    sim_vga_out(vga,0x3ce,5); sim_vga_out(vga,0x3cf,1);
    di = (uint16_t)((uint16_t)y*(uint16_t)g_3DB6+((uint16_t)x>>3));
    for (row = 0; row < 16; ++row) {
        for (byte = 0; byte < 2; ++byte) {
            uint8_t cpu = sim_vga_read(vga,si++);
            sim_vga_write(vga,di++,cpu);
        }
        di = (uint16_t)(di+(uint16_t)g_3DB6-2u);
    }
    sim_vga_out(vga,0x3ce,5); sim_vga_out(vga,0x3cf,0);
    cursor_status = source_cursor_after_tile();
    screen_lock_leave();
    return s_status = cursor_status;
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
    if (source == NULL)
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
            uint16_t address = (uint16_t)(cache_base + row * 8u + word * 2u);
            uint16_t background = (uint16_t)(s_planes[(unsigned)plane & 3u][address] |
                ((uint16_t)s_planes[(unsigned)plane & 3u][(uint16_t)(address+1u)] << 8));
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
            g_3D20[row * 8u + word * 2u] = (uint8_t)result;
            g_3D20[row * 8u + word * 2u + 1u] =
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
    if ((*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9]) == NULL)
        return s_status = SIM_GRAPHICS_TILE_UPLOAD_DRAW_UNBOUND;
    s_graphics_owner->last_status = SIM_GRAPHICS_OK;
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9])(x, y, (char *)g_3D20, 16, 16);
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
