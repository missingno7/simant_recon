#include "portable/whole_program/platform/native_video_profile.h"

#include <stdio.h>
#include <string.h>

char g_5A97; /* Narrow test has no window-source globals translation unit. */

/* This legacy provider-contract test does not invoke bitmap callbacks. The
 * source-backed f_205F integration harness covers the real bitmap binder. */
SimGraphicsStatus sim_graphics_source_bitmap_bind(SimGraphicsDriver *graphics)
{
    return graphics != NULL ? SIM_GRAPHICS_OK : SIM_GRAPHICS_INVALID_ARGUMENT;
}
void sim_graphics_source_bitmap_unbind(void) { }

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #x); \
    return 1; \
} } while (0)

static int mode_changes;
static SimGraphicsStatus mode_changed(void *context, int32_t width, int32_t height)
{
    (void)context;
    if (width != SIM_GRAPHICS_SOURCE_WIDTH ||
        (height != SIM_GRAPHICS_SOURCE_EGA_HEIGHT &&
         height != SIM_GRAPHICS_SOURCE_VGA_HEIGHT))
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    ++mode_changes;
    return SIM_GRAPHICS_OK;
}

int main(void)
{
    SimNativeVideoProfileInfo info;
    SimGraphicsDriver graphics;
    uint8_t bios_font[256u * 14u] = {0};
    int16_t profile;

    memset(&info, 0x5a, sizeof(info));
    CHECK(sim_native_video_profile_info(0, &info) == SIM_NATIVE_VIDEO_OK);
    CHECK(info.profile == SIM_NATIVE_VIDEO_EGA_PROFILE_0);
    CHECK(info.source_bios_descriptor == 0x0303);
    CHECK(info.source_mode == 0x10);
    CHECK(strcmp(info.database_prefix, "hcega") == 0);

    CHECK(sim_native_video_profile_info(8, &info) == SIM_NATIVE_VIDEO_OK);
    CHECK(info.profile == SIM_NATIVE_VIDEO_VGA_PROFILE_8);
    CHECK(info.source_bios_descriptor == 0x0305);
    CHECK(info.source_mode == 0x12);
    CHECK(strcmp(info.database_prefix, "hcega") == 0);

    for (profile = 1; profile < 8; ++profile) {
        SimNativeVideoProfileInfo unchanged;
        memset(&unchanged, 0xa5, sizeof(unchanged));
        info = unchanged;
        CHECK(sim_native_video_profile_info(profile, &info) ==
              SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE);
        CHECK(memcmp(&info, &unchanged, sizeof(info)) == 0);
    }
    CHECK(sim_native_video_profile_info(9, &info) ==
          SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE);

    CHECK(sim_native_video_startup_bind(0, NULL) ==
          SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY);
    CHECK(sim_native_video_startup_bind(1, &graphics) ==
          SIM_NATIVE_VIDEO_UNSUPPORTED_PROFILE);

    CHECK(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK);
    sim_graphics_set_mode_changed_callback(&graphics, mode_changed, NULL);
    CHECK(sim_native_video_startup_bind(0, &graphics) ==
          SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY);
    CHECK(sim_graphics_set_bios_font_sources(&graphics, NULL, 0,
                                              bios_font, sizeof(bios_font)) ==
          SIM_GRAPHICS_OK);
    CHECK(sim_native_video_startup_bind(0, &graphics) ==
          SIM_NATIVE_VIDEO_OK);
    CHECK((uint16_t)o21_39C7_0000() == 0x0303);
    f_1B4E_0025();
    CHECK(g_9128 == NULL && g_9130 == NULL);
    o00_31AD_2AB4();
    CHECK(sim_native_video_startup_status() == SIM_NATIVE_VIDEO_OK);
    CHECK(graphics.video_mode == SIM_GRAPHICS_MODE_EGA_640X350);
    CHECK(graphics.g_3DB2 == 640 && graphics.g_3DB4 == 350 && graphics.g_3DB6 == 80);
    CHECK(g_9128 != NULL && g_9130 != NULL);
    g_9130();
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(mode_changes == 1);

    sim_native_video_startup_unbind();
    CHECK(g_9128 == NULL && g_9130 == NULL);
    CHECK(sim_native_video_startup_status() == SIM_NATIVE_VIDEO_NOT_BOUND);

    CHECK(sim_native_video_startup_bind(8, &graphics) ==
          SIM_NATIVE_VIDEO_OK);
    CHECK((uint16_t)o21_39C7_0000() == 0x0305);
    f_1B4E_0025();
    o00_31AD_2AE5();
    CHECK(sim_native_video_startup_status() == SIM_NATIVE_VIDEO_OK);
    CHECK(graphics.video_mode == SIM_GRAPHICS_MODE_VGA_640X480);
    CHECK(graphics.g_3DB2 == 640 && graphics.g_3DB4 == 480 && graphics.g_3DB6 == 80);
    CHECK(mode_changes == 2);

    sim_native_video_startup_unbind();
    sim_graphics_destroy(&graphics);
    puts("native video profile contract: PASS (host intent only; no BIOS emulation)");
    return 0;
}
