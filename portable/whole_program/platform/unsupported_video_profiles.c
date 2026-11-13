#include "unsupported_video_profiles.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static _Noreturn void unsupported_video_profile_entry(const char *symbol)
{
    (void)fprintf(stderr, "unsupported native video profile entry: %s\n", symbol);
    (void)fflush(stderr);
    _Exit(70);
}

#define REJECT_NOARGS(symbol) \
    void symbol(void) { unsupported_video_profile_entry(#symbol); }

REJECT_NOARGS(gfx_mono_init_banked_640x400)
REJECT_NOARGS(gfx_mono_init_ega480_mono)
REJECT_NOARGS(gfx_mono_init_ega350_mono)
REJECT_NOARGS(gfx_mono_init_hercules)
void gfx_mono_draw_life_tile(int16_t x, int16_t y, char *tile, char *life, int16_t n)
{
    (void)x; (void)y; (void)tile; (void)life; (void)n;
    unsupported_video_profile_entry("gfx_mono_draw_life_tile");
}
void gfx_mono_compose_life_tile(char *tile, char *life, int16_t n)
{
    (void)tile; (void)life; (void)n;
    unsupported_video_profile_entry("gfx_mono_compose_life_tile");
}

REJECT_NOARGS(WindowsMono_MakeTable4x4a)
REJECT_NOARGS(WindowsMono_MakeTable4x4b)
void WindowsMono_MakeTable2x2a(char *src, char *dst, int16_t y)
{
    (void)src; (void)dst; (void)y;
    unsupported_video_profile_entry("WindowsMono_MakeTable2x2a");
}
void WindowsMono_MakeTable2x2b(char *src, char *dst, int16_t y)
{
    (void)src; (void)dst; (void)y;
    unsupported_video_profile_entry("WindowsMono_MakeTable2x2b");
}

REJECT_NOARGS(gfx_mono_buffer_noop)
void gfx_mono_mask_bitmap_to_buffer(char *image, char *buffer, int16_t shift, int16_t flag)
{
    (void)image; (void)buffer; (void)shift; (void)flag;
    unsupported_video_profile_entry("gfx_mono_mask_bitmap_to_buffer");
}
REJECT_NOARGS(gfx_mono_copy_bitmap_to_buffer)
REJECT_NOARGS(gfx_mono_buffer_intersection)
REJECT_NOARGS(gfx_mono_scratch_to_buffer)

REJECT_NOARGS(gfx_vga8_init_vga256)
REJECT_NOARGS(gfx_tandy_init_tandy)

REJECT_NOARGS(gfx_tandy_map_duplicate_rows)
void Windows_MakeTable1x1(char *src, char *dst, int16_t mult)
{
    (void)src; (void)dst; (void)mult;
    unsupported_video_profile_entry("Windows_MakeTable1x1");
}

REJECT_NOARGS(gfx_tandy_buffer_noop)
void gfx_tandy_mask_to_buffer(char *image, char *buffer, int16_t shift, int16_t flag)
{
    (void)image; (void)buffer; (void)shift; (void)flag;
    unsupported_video_profile_entry("gfx_tandy_mask_to_buffer");
}
REJECT_NOARGS(gfx_tandy_copy_to_buffer)
REJECT_NOARGS(gfx_tandy_buffer_intersection)
void gfx_tandy_draw_life_tile(int16_t x, int16_t y, char *tile, char *life, int16_t mask)
{
    (void)x; (void)y; (void)tile; (void)life; (void)mask;
    unsupported_video_profile_entry("gfx_tandy_draw_life_tile");
}
void gfx_tandy_compose_life_tile(char *tile, char *life, int16_t mask)
{
    (void)tile; (void)life; (void)mask;
    unsupported_video_profile_entry("gfx_tandy_compose_life_tile");
}
REJECT_NOARGS(gfx_tandy_scratch_to_buffer)

#undef REJECT_NOARGS
