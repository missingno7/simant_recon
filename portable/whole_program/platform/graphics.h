#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_H

#include "portable/render/primitives.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SIM_GRAPHICS_SOURCE_WIDTH 640
#define SIM_GRAPHICS_SOURCE_EGA_HEIGHT 350
#define SIM_GRAPHICS_SOURCE_VGA_HEIGHT 480
#define SIM_GRAPHICS_SOURCE_HEIGHT SIM_GRAPHICS_SOURCE_EGA_HEIGHT
#define SIM_GRAPHICS_CLIP_DEPTH 16
#define SIM_GRAPHICS_DRIVER_ENTRY_COUNT 25

typedef enum SimGraphicsStatus {
    SIM_GRAPHICS_OK = 0,
    SIM_GRAPHICS_INVALID_ARGUMENT,
    SIM_GRAPHICS_NO_MEMORY,
    SIM_GRAPHICS_CLIP_STACK_OVERFLOW,
    SIM_GRAPHICS_CLIP_STACK_UNDERFLOW,
    SIM_GRAPHICS_FONT_UNBOUND,
    SIM_GRAPHICS_FONT_SPAN_INVALID,
    SIM_GRAPHICS_UNSUPPORTED_GLYPH_FOLD,
    SIM_GRAPHICS_UNSUPPORTED_MODE,
    SIM_GRAPHICS_PATTERN_SOURCE_UNBOUND
} SimGraphicsStatus;

typedef enum SimGraphicsVideoMode {
    SIM_GRAPHICS_MODE_EGA_640X350 = 0x10,
    SIM_GRAPHICS_MODE_VGA_640X480 = 0x12
} SimGraphicsVideoMode;

typedef SimGraphicsStatus (*SimGraphicsModeChangedCallback)(void *context,
                                                            int32_t logical_width,
                                                            int32_t logical_height);

typedef enum SimGraphicsDriverEntry {
    SIM_GFX_ENTRY_G9128 = 0,
    SIM_GFX_ENTRY_G912C,
    SIM_GFX_ENTRY_G9130,
    SIM_GFX_ENTRY_G9134,
    SIM_GFX_ENTRY_G9138,
    SIM_GFX_ENTRY_G913C,
    SIM_GFX_ENTRY_G9140,
    SIM_GFX_ENTRY_G9144,
    SIM_GFX_ENTRY_G9148,
    SIM_GFX_ENTRY_G914C,
    SIM_GFX_ENTRY_G9150,
    SIM_GFX_ENTRY_G9154,
    SIM_GFX_ENTRY_G9158,
    SIM_GFX_ENTRY_G915C,
    SIM_GFX_ENTRY_G9160,
    SIM_GFX_ENTRY_G9164,
    SIM_GFX_ENTRY_G9168,
    SIM_GFX_ENTRY_G916C,
    SIM_GFX_ENTRY_G9170,
    SIM_GFX_ENTRY_G9174,
    SIM_GFX_ENTRY_G9178,
    SIM_GFX_ENTRY_G917C,
    SIM_GFX_ENTRY_G9180,
    SIM_GFX_ENTRY_G9184,
    SIM_GFX_ENTRY_G9188
} SimGraphicsDriverEntry;

typedef struct SimGraphicsSlotInfo {
    SimGraphicsDriverEntry entry;
    const char *source_target;
    uint8_t provided;
} SimGraphicsSlotInfo;

typedef struct SimGraphicsDriver {
    /* This is the one indexed framebuffer owner for whole-program rendering. */
    PortableFramebuffer framebuffer;
    uint8_t *pixel_storage;
    size_t pixel_storage_size;
    SimGraphicsVideoMode video_mode;
    SimGraphicsModeChangedCallback mode_changed;
    void *mode_changed_context;
    uint8_t overscan_color; /* pending source INT 10h AX=1001h color */
    SimGraphicsStatus last_status; /* result of void source ABI callbacks */

    /* Native owners corresponding to m1B4E source DATA, in DOS widths. */
    int16_t g_3DA0; /* text pen x */
    int16_t g_3DA2; /* text pen y */
    int16_t g_3DB2; /* logical screen width; source default 640 */
    int16_t g_3DB4; /* logical screen height; source default 350 */
    int16_t g_3DB6; /* DOS planar bytes per scanline; source default 80 */
    int16_t g_3DD2; /* source VGA logic-operation word; only zero mode admitted */
    int16_t g_3DDA; /* source glyph-index stride, used by 6-pixel fold branch */
    int16_t g_3DDC; /* active glyph cell height */
    int16_t g_3DDE; /* text advance/glyph width; source default 8 */
    uint8_t g_3DE0; /* source pen/foreground */
    uint8_t g_3DE2; /* source background/fill */
    uint8_t g_3DE4; /* source pattern selection, retained but not inferred by g9128 */
    uint8_t color_map[16]; /* m1B4E g_41C0 */

    const uint8_t *glyph_source;
    size_t glyph_source_size;
    uint16_t glyph_bytes_per_character;
    uint8_t glyph_width;
    uint8_t glyph_height;
    const uint8_t *pattern_source; /* caller-owned view of source g_41D0 pattern data */
    size_t pattern_source_size;
    const uint8_t *custom_font_source; /* caller-owned g_3DA8:g_3DAA font view */
    size_t custom_font_source_size;
    const uint8_t *bios_8x8_source; /* host service result for INT 10h AX=1130h/BH=03h */
    size_t bios_8x8_source_size;
    const uint8_t *bios_8x14_source; /* host service result for INT 10h AX=1130h/BH=02h */
    size_t bios_8x14_source_size;
    uint8_t custom_font_present;
    uint8_t font_is_bound;
    uint8_t clip_depth;
    PortableRect clip_stack[SIM_GRAPHICS_CLIP_DEPTH];
} SimGraphicsDriver;

/* Default source startup profile is EGA mode 10h (640x350); mode 12h selects
 * VGA 640x480. g_3DB6 remains the DOS planar stride (80) in both modes; host
 * indexed stride equals the logical pixel width. */
SimGraphicsStatus sim_graphics_init(SimGraphicsDriver *graphics);
SimGraphicsStatus sim_graphics_set_mode(SimGraphicsDriver *graphics, int16_t mode);
void sim_graphics_set_mode_changed_callback(SimGraphicsDriver *graphics,
                                            SimGraphicsModeChangedCallback callback,
                                            void *context);
void sim_graphics_destroy(SimGraphicsDriver *graphics);
uint8_t *sim_graphics_pixels(SimGraphicsDriver *graphics, size_t *size_out);

/* Bind the single application-owned graphics state and the existing source
 * g_5AAE word used by S00's g9154 wrapper branch. Null unbinds the source ABI. */
SimGraphicsStatus sim_graphics_bind_source_abi(SimGraphicsDriver *graphics,
                                               const uint16_t *source_g_5AAE);
/* S00 o00_31AD_1AE7 overrides table slots after the initial 25-entry copy. */
SimGraphicsStatus sim_graphics_s00_apply_cga_font_overrides(SimGraphicsDriver *graphics);
SimGraphicsDriver *sim_graphics_source_owner(void);
SimGraphicsStatus sim_graphics_source_last_status(void);

/* Native equivalents of public source f_1B4E entry points. The void signatures
 * mirror the source far procedures; status is read via source_last_status. */
void f_1B4E_015B(int16_t mode);
int16_t f_1B4E_000D(int16_t color);
void f_1B4E_0228(int16_t color);

/* Selected DOS table globals, initialized only while a graphics owner is
 * bound. Unselected driver entries have no fabricated callback. */
typedef void (*SimGraphicsAttrCallback)(int16_t foreground,
                                        int16_t background,
                                        int16_t pattern_word);
typedef void (*SimGraphicsRectCallback)(int16_t left, int16_t top,
                                        int16_t right, int16_t bottom,
                                        int16_t color);
typedef void (*SimGraphicsBitmapCallback)(int16_t x, int16_t y,
                                          char *bitmap,
                                          int16_t width, int16_t height);
typedef void (*SimGraphicsLineCallback)(int16_t x0, int16_t y0,
                                        int16_t x1, int16_t y1,
                                        int16_t color);
typedef void (*SimGraphicsFontCallback)(void);
typedef void (*SimGraphicsPatternRectCallback)(int16_t left, int16_t top,
                                               int16_t right, int16_t bottom,
                                               int16_t pattern_word);
typedef void (*SimGraphicsRectOperationCallback)(int16_t left, int16_t top,
                                                 int16_t right, int16_t bottom);
extern SimGraphicsAttrCallback g_9128;
extern SimGraphicsFontCallback g_912C;
extern SimGraphicsFontCallback g_9130;
extern SimGraphicsRectCallback g_9134;
extern SimGraphicsPatternRectCallback g_9138;
extern SimGraphicsRectOperationCallback g_913C;
extern SimGraphicsBitmapCallback g_9154;
extern SimGraphicsBitmapCallback g_9158;
extern SimGraphicsLineCallback g_9170;

/* Window clipping is host framebuffer state, not a second copy of window/UI state. */
SimGraphicsStatus sim_graphics_clip_push(SimGraphicsDriver *graphics);
SimGraphicsStatus sim_graphics_clip_set(SimGraphicsDriver *graphics, PortableRect clip);
SimGraphicsStatus sim_graphics_clip_pop(SimGraphicsDriver *graphics);

/* Source entry f_1B4E_000D(int color): preserves high color bits and maps its
 * low nibble through the initialized g_41C0 palette map. */
int16_t sim_graphics_f_1B4E_000D(SimGraphicsDriver *graphics, int16_t color);

/* Logical driver entries, matching the source call-site word widths. g9128's
 * S00 target stores only fore/back; the third source word is deliberately
 * ignored because o00_31AD_1659 reads only [bp+6] and [bp+8]. */
SimGraphicsStatus sim_graphics_g9128(SimGraphicsDriver *graphics,
                                     int16_t foreground,
                                     int16_t background,
                                     int16_t source_pattern_word);
SimGraphicsStatus sim_graphics_g9134(SimGraphicsDriver *graphics,
                                     int16_t left, int16_t top,
                                     int16_t right, int16_t bottom,
                                     int16_t color);
/* S00 `_013A` uses a caller-owned view of the original 256-byte g_41D0
 * pattern region. The view is not copied into the platform source. */
SimGraphicsStatus sim_graphics_set_pattern_source(SimGraphicsDriver *graphics,
                                                  const uint8_t *bytes,
                                                  size_t size);
SimGraphicsStatus sim_graphics_g9138_pattern_rect(SimGraphicsDriver *graphics,
                                                   int16_t left, int16_t top,
                                                   int16_t right, int16_t bottom,
                                                   int16_t pattern_word);
/* S00 `_0394` selects XOR and VGA set/reset color 0x0f over a half-open rect. */
SimGraphicsStatus sim_graphics_g913C_xor_rect(SimGraphicsDriver *graphics,
                                               int16_t left, int16_t top,
                                               int16_t right, int16_t bottom);
SimGraphicsStatus sim_graphics_g912C_select_custom_font(SimGraphicsDriver *graphics);
SimGraphicsStatus sim_graphics_g9130_select_bios_8x8(SimGraphicsDriver *graphics);
SimGraphicsStatus sim_graphics_g9130_select_bios_8x14(SimGraphicsDriver *graphics);
SimGraphicsStatus sim_graphics_set_custom_font_source(SimGraphicsDriver *graphics,
                                                      const uint8_t *bytes,
                                                      size_t size);
SimGraphicsStatus sim_graphics_set_bios_font_sources(SimGraphicsDriver *graphics,
                                                     const uint8_t *font_8x8,
                                                     size_t font_8x8_size,
                                                     const uint8_t *font_8x14,
                                                     size_t font_8x14_size);
/* S00 slot g9170/o00_31AD_1499; source-derived 640x480-domain walk and the
 * reviewed indexed logic operations in g_3DD2 are supported. */
SimGraphicsStatus sim_graphics_g9170_line(SimGraphicsDriver *graphics,
                                          int16_t x0, int16_t y0,
                                          int16_t x1, int16_t y1,
                                          int16_t color);
/* S00 slot g9154/o00_31AD_1206: bounded MSB-first one-bit bitmap transfer,
 * with foreground/background supplied by the current source pen attributes. */
SimGraphicsStatus sim_graphics_g9154(SimGraphicsDriver *graphics,
                                     int16_t x, int16_t y,
                                     const uint8_t *bitmap, size_t bitmap_size,
                                     uint16_t width, uint16_t height);

/* Install a caller-owned, bounds-described 1bpp BIOS-font image. Each glyph
 * starts glyph_bytes_per_character bytes after the previous glyph (source
 * g_3DDA); raster rows are MSB-first per m1B4E f_1B4E_0110's g9154 boundary. */
SimGraphicsStatus sim_graphics_set_glyph_source(SimGraphicsDriver *graphics,
                                                const uint8_t *bytes,
                                                size_t size,
                                                uint16_t glyph_bytes_per_character,
                                                uint8_t width,
                                                uint8_t height);

/* Source entries f_1B4E_0110(int x,int y,int character) and
 * f_1B4E_0081(int x,int y,char far *text), expressed with explicit native
 * state ownership. Text stops at NUL and returns final pen state in g_3DA0/2. */
SimGraphicsStatus sim_graphics_f_1B4E_0110(SimGraphicsDriver *graphics,
                                           int16_t x, int16_t y,
                                           int16_t character);
SimGraphicsStatus sim_graphics_f_1B4E_0081(SimGraphicsDriver *graphics,
                                           int16_t x, int16_t y,
                                           const char *text);

const SimGraphicsSlotInfo *sim_graphics_driver_slots(size_t *count_out);
/* S01 is the hardware-bound MDA/Hercules table; its symbols are inventory only. */
const char *const *sim_graphics_s01_source_targets(size_t *count_out);
int sim_graphics_driver_entry_is_provided(SimGraphicsDriverEntry entry);

#ifdef __cplusplus
}
#endif
#endif
