#include "portable/whole_program/platform/native_video_profile.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/platform/graphics_bitmap_source.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #x); \
    return 1; \
} } while (0)

extern void f_205F_0004(char *dbname);
extern void f_1B28_0006(void);
extern int16_t g_3D0C;
extern char g_5A97;
extern int16_t fd_55B3_6262;
extern void (*fd_50F6_37EE)(void);
extern void (*fd_50F6_37EA)(void);
extern void (*fd_50F6_3B58)(void);
extern void (*fd_50F6_37E6)(void);

static SimGraphicsDriver s_graphics;
static uint8_t s_framebuffer[640u * SIM_GRAPHICS_SOURCE_VGA_HEIGHT];
static uint8_t s_font8[256u * 8u];
static uint8_t s_font14[256u * 14u];
static char *s_object_data[6][2];
static unsigned s_events[32];
static unsigned s_event_count;
static char s_database[128];
static int16_t s_profile;

static void event(unsigned value)
{
    if (s_event_count < sizeof(s_events) / sizeof(s_events[0]))
        s_events[s_event_count++] = value;
}

void db_SetDataBase(char *name)
{
    (void)snprintf(s_database, sizeof(s_database), "%s", name);
    event(100);
}

char **db_LoadObject(int16_t object, int16_t kind)
{
    unsigned kind_index = kind == 8 ? 0u : 1u;
    event(1u + (unsigned)object * 2u + kind_index);
    return (object >= 0 && object < 6 && (kind == 8 || kind == 7))
        ? &s_object_data[object][kind_index] : NULL;
}

void db_UnhookObject(int16_t object, int16_t kind)
{
    event(20u + (unsigned)object * 2u + (kind == 8 ? 0u : 1u));
}

int16_t dos_sprintf(char *buffer, const char *format, ...)
{
    int result;
    va_list args;
    va_start(args, format);
    result = vsnprintf(buffer, 100, format, args);
    va_end(args);
    return (int16_t)result;
}

int16_t dos_printf(const char *format, ...)
{
    (void)format;
    abort(); /* Unsupported source error branch must not masquerade as success. */
}

void Punt(char *message, ...)
{
    (void)message;
    abort();
}

/* Fail-closed symbols satisfy branches excluded by the selected source profile. */
#define UNSUPPORTED(name) void name(void) { abort(); }
UNSUPPORTED(o01_3126_0000)
UNSUPPORTED(o20_39C7_0160)
UNSUPPORTED(o20_39C7_0003)
UNSUPPORTED(o03_3126_0140)
UNSUPPORTED(o20_39C7_0069)
UNSUPPORTED(o20_39C7_0001)
UNSUPPORTED(o01_3126_010A)
UNSUPPORTED(o20_39C7_0008)
UNSUPPORTED(o20_39C7_0000)
UNSUPPORTED(o00_31AD_1AE7)
UNSUPPORTED(o20_39C7_01C1)
UNSUPPORTED(o20_39C7_0004)
UNSUPPORTED(o01_3126_007D)
UNSUPPORTED(o02_3126_0000)
UNSUPPORTED(o20_39C7_0212)
UNSUPPORTED(o20_39C7_0006)
UNSUPPORTED(o01_3126_0068)
UNSUPPORTED(o20_39C7_00FF)
UNSUPPORTED(o20_39C7_0002)
UNSUPPORTED(o01_32B5_000E)
UNSUPPORTED(o01_32B5_0152)
UNSUPPORTED(o01_32B5_000F)
UNSUPPORTED(o01_32B5_00AA)
UNSUPPORTED(o01_32B5_024F)
UNSUPPORTED(o03_3258_040C)
UNSUPPORTED(o03_3258_05A7)
UNSUPPORTED(o03_3258_040D)
UNSUPPORTED(o03_3258_04CE)
UNSUPPORTED(o03_3258_175F)
UNSUPPORTED(o00_35A6_02FD)
UNSUPPORTED(o00_35A6_0007)
UNSUPPORTED(o00_35A6_0177)
UNSUPPORTED(o00_35A6_0406)
#undef UNSUPPORTED

/* This source assembly entry is literally RETF; this is its exact native
 * empty body. The other S00 operations remain fail-closed above. */
void o00_35A6_0006(void) { }

/* Source DATA globals not owned by the graphics state object in this narrow
 * harness. The selected f_205F path writes four callback slots. */
char g_5A97;
void (*fd_50F6_37EE)(void);
void (*fd_50F6_37EA)(void);
void (*fd_50F6_3B58)(void);
void (*fd_50F6_37E6)(void);

void f_1B73_01E1(char *image, char *mask)
{ (void)image; (void)mask; abort(); }
void f_1B73_00D9(void) { abort(); }
void f_171C_13E4(char **handle) { (void)handle; abort(); }

/* The non-null clipping callback is outside this startup-only case and traps. */
void f_1D8E_07F6(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height;
    abort();
}

static SimGraphicsStatus mode_changed(void *context, int32_t width, int32_t height)
{
    (void)context;
    if (width != 640 || (height != 350 && height != 480))
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    event(height == 350 ? 201 : 202);
    return SIM_GRAPHICS_OK;
}

int main(int argc, char **argv)
{
    unsigned i;
    unsigned j;
    int16_t expected_mode;
    int16_t expected_height;
    const unsigned load_sequence[24] = {
        1, 2, 20, 21, 3, 4, 22, 23, 5, 6, 24, 25,
        7, 8, 26, 27, 9, 10, 28, 29, 11, 12, 30, 31
    };

    if (argc != 2) return 2;
    s_profile = (int16_t)atoi(argv[1]);
    expected_mode = s_profile == 0 ? 0x10 : 0x12;
    expected_height = s_profile == 0 ? 350 : 480;
    memset(s_framebuffer, 0, sizeof(s_framebuffer));
    memset(s_font8, 0x55, sizeof(s_font8));
    memset(s_font14, 0xaa, sizeof(s_font14));
    for (i = 0; i < 6; ++i) for (j = 0; j < 2; ++j)
        s_object_data[i][j] = (char *)&s_framebuffer[(i * 2u + j) * 8u];

    CHECK(sim_graphics_init(&s_graphics) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_set_bios_font_sources(&s_graphics,
          s_font8, sizeof(s_font8), s_font14, sizeof(s_font14)) == SIM_GRAPHICS_OK);
    sim_graphics_set_mode_changed_callback(&s_graphics, mode_changed, NULL);
    CHECK(sim_native_video_startup_bind(s_profile, &s_graphics) == SIM_NATIVE_VIDEO_OK);

    /* The source entry auto-selects the adapter profile from a startup -1. */
    g_5A97 = -1;
    s_event_count = 0;
    f_205F_0004("SC");

    CHECK(strcmp(s_database, "hcegaSC") == 0);
    CHECK(g_5A97 == s_profile);
    CHECK(s_graphics.video_mode == (SimGraphicsVideoMode)expected_mode);
    CHECK(s_graphics.g_3DB2 == 640 && s_graphics.g_3DB4 == expected_height &&
          s_graphics.g_3DB6 == 80);
    CHECK(g_5A9C.left == 0 && g_5A9C.top == 0 &&
          g_5A9C.right == 640 && g_5A9C.bottom == expected_height);
    CHECK(fd_55B3_6262 == 1);
    CHECK(g_9130 != NULL && g_914C != NULL && g_9150 != NULL);
    CHECK(fd_50F6_37EE != NULL && fd_50F6_37EA != NULL &&
          fd_50F6_3B58 != NULL && fd_50F6_37E6 != NULL);
    CHECK(g_5AAC == NULL); /* Source clipping-list pointer remains absent. */
    CHECK(s_event_count == 26);
    CHECK(s_events[0] == 100);
    for (i = 0; i < 24; ++i) CHECK(s_events[i + 1] == load_sequence[i]);
    CHECK(s_events[25] == (s_profile == 0 ? 201u : 202u));
    CHECK(sim_native_video_startup_status() == SIM_NATIVE_VIDEO_OK);

    sim_native_video_startup_unbind();
    CHECK(g_9130 == NULL && g_914C == NULL && g_9150 == NULL);
    sim_graphics_destroy(&s_graphics);
    puts("generated f_205F selected-profile startup: PASS");
    return 0;
}
