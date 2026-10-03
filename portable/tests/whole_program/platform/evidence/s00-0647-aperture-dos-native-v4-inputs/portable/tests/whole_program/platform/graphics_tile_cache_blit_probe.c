#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/platform/graphics_bitmap_source.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"
#include "portable/whole_program/platform/graphics_cursor_hooks.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"
#include "portable/whole_program/state/asm_display_data_v1.h"

#include <stdint.h>
#include <string.h>

static int s_callback_kind;
static int16_t s_callback_x, s_callback_y, s_callback_width, s_callback_height;
static uint8_t s_callback_payload[128];

/* Other graphics leaves are not reached by the controlled bitmap call. */
char *g_3DA8;
SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *g)
{ (void)g; return SIM_GRAPHICS_FONT_UNBOUND; }
void f_1D8E_07F6(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{ (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height; }
void f_1D8E_070E(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{ f_1D8E_07F6(port, x, y, bits, width, height); }
void f_1D8E_0384(SimGraphicsPatternRectCallback callback,
                 int16_t a, int16_t b, int16_t l, int16_t t,
                 int16_t r, int16_t bottom, int16_t pattern)
{ (void)callback; (void)a; (void)b; (void)l; (void)t; (void)r;
  (void)bottom; (void)pattern; }

static int cursor_noop(void *context) { (void)context; return 1; }

static void capture_callback(int kind, int16_t x, int16_t y, char *bits,
                             int16_t width, int16_t height)
{
    s_callback_kind = kind;
    s_callback_x = x;
    s_callback_y = y;
    s_callback_width = width;
    s_callback_height = height;
    if (bits == NULL || width != 16 || height != 16)
        return;
    memcpy(s_callback_payload, bits, sizeof(s_callback_payload));
}

static void clipped_callback(int16_t x, int16_t y, char *bits,
                             int16_t width, int16_t height)
{ capture_callback(2, x, y, bits, width, height); }

static void store_planar_tile(uint16_t offset, const uint8_t rows[32])
{
    if (offset >= SIM_GRAPHICS_TILE_MAP_OFFSET &&
        offset < SIM_GRAPHICS_TILE_PAGE_OFFSET) {
        uint8_t source[SIM_GRAPHICS_TILE_MAP_UPLOAD_BYTES];
        size_t relative = (size_t)offset - SIM_GRAPHICS_TILE_MAP_OFFSET;
        size_t tile_row = relative / 32u;
        unsigned row, plane, byte;
        memset(source, 0, sizeof(source));
        for (row = 0; row < 16u; ++row) {
            for (plane = 0; plane < 4u; ++plane) {
                for (byte = 0; byte < 2u; ++byte) {
                    size_t page_byte = row * 2u + byte;
                    size_t source_offset = tile_row * 128u +
                        (page_byte / 2u) * 8u + plane * 2u + (page_byte & 1u);
                    source[source_offset] = rows[page_byte];
                }
            }
        }
        o00_31AD_18BA((char *)source, SIM_GRAPHICS_TILE_MAP_OFFSET, 256);
    } else {
        uint8_t page[SIM_GRAPHICS_TILE_UPLOAD_BYTES];
        size_t relative = (size_t)offset - SIM_GRAPHICS_TILE_PAGE_OFFSET;
        unsigned plane;
        memset(page, 0, sizeof(page));
        memcpy(page + relative, rows, 32u);
        for (plane = 0; plane < 4u; ++plane)
            o00_31AD_186A((char *)page, SIM_GRAPHICS_TILE_PAGE_OFFSET,
                          (int16_t)plane, SIM_GRAPHICS_TILE_UPLOAD_BYTES);
    }
}

/* `rows` is the 32-byte source span read by 0647 at offset+2*row. All four
 * source planes receive the same bytes so the original flat Unicorn aperture
 * has a valid normalized comparison without pretending it models EGA latches. */
int sim_tile0647_native_probe(int16_t x, int16_t y, uint16_t offset,
                              int active_clip, const uint8_t rows[32],
                              uint8_t *pixels, size_t pixel_capacity,
                              uint8_t *callback_bytes, size_t callback_capacity,
                              int32_t meta[8])
{
    SimGraphicsDriver graphics;
    SimGraphicsCursorHooks hooks = { NULL, cursor_noop, cursor_noop, cursor_noop };
    struct Rect clip = { 0, 0, 640, 480 };
    size_t index;
    int result = -1;
    if (rows == NULL || pixels == NULL || pixel_capacity < 256u ||
        callback_bytes == NULL || callback_capacity < sizeof(s_callback_payload) ||
        meta == NULL)
        return -2;
    memset(&graphics, 0, sizeof(graphics));
    memset(meta, 0, 8u * sizeof(meta[0]));
    memset(pixels, 0, 256u);
    memset(callback_bytes, 0, sizeof(s_callback_payload));
    memset(s_callback_payload, 0, sizeof(s_callback_payload));
    s_callback_kind = 0;
    s_callback_x = s_callback_y = s_callback_width = s_callback_height = 0;
    if (sim_graphics_init(&graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_set_mode(&graphics, 0x12) != SIM_GRAPHICS_OK ||
        sim_graphics_bind_source_abi(&graphics, &g_5AAC) != SIM_GRAPHICS_OK ||
        sim_graphics_source_bitmap_bind(&graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_tile_upload_bind(&graphics) != SIM_GRAPHICS_TILE_UPLOAD_OK ||
        sim_graphics_cursor_hooks_bind(&hooks) != SIM_GRAPHICS_CURSOR_HOOKS_OK)
        goto done;

    store_planar_tile(offset, rows);
    if (active_clip) {
        clip.left = (int16_t)(x + 4);
        clip.top = (int16_t)(y + 4);
        clip.right = (int16_t)(x + 11);
        clip.bottom = (int16_t)(y + 11);
        g_5AAC = &clip;
        g_914C = clipped_callback;
    } else {
        g_5AAC = NULL;
    }
    /* Suppress only cursor services; the test is the 0647 draw boundary. */
    g_4333 = 1;
    g_4365 = 0;
    g_4366 = 1;
    g_3DD4 = 0;
    if (sim_graphics_tile_cache_blit(x, y, offset) !=
        SIM_GRAPHICS_TILE_UPLOAD_OK)
        goto done;
    for (index = 0; index < 16u; ++index) {
        unsigned col;
        for (col = 0; col < 16u; ++col) {
            int32_t px = (int32_t)x + (int32_t)col;
            int32_t py = (int32_t)y + (int32_t)index;
            pixels[index * 16u + col] = graphics.pixel_storage[
                (size_t)py * graphics.framebuffer.stride + (size_t)px];
        }
    }
    memcpy(callback_bytes, s_callback_payload, sizeof(s_callback_payload));
    meta[0] = (int32_t)sim_graphics_tile_upload_status();
    meta[1] = s_callback_kind;
    meta[2] = s_callback_x;
    meta[3] = s_callback_y;
    meta[4] = s_callback_width;
    meta[5] = s_callback_height;
    meta[6] = g_3DD4;
    meta[7] = graphics.last_status;
    result = 0;
done:
    if (meta[0] == 0 && result != 0)
        meta[0] = (int32_t)sim_graphics_tile_upload_status();
    sim_graphics_cursor_hooks_unbind();
    sim_graphics_tile_upload_unbind();
    sim_graphics_source_bitmap_unbind();
    sim_graphics_bind_source_abi(NULL, NULL);
    sim_graphics_destroy(&graphics);
    return result;
}
