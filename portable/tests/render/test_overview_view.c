#include "../../ui_model/windows/overview_view.h"
#include "../../game/resources/database.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int32_t rect_width(PortableWindowRect rect)
{
    return (int32_t)rect.right - rect.left;
}

static int32_t rect_height(PortableWindowRect rect)
{
    return (int32_t)rect.bottom - rect.top;
}

static int is_cursor_outline_pixel(const PortableOverviewView *view,
                                   int32_t x, int32_t y)
{
    const PortableWindowRect r = view->cursor_rect;
    const int32_t width = view->cursor_outline_width;
    return (x >= r.left && x < r.left + width &&
            y >= r.top && y < r.bottom) ||
           (x >= r.right - width && x < r.right &&
            y >= r.top && y < r.bottom) ||
           (x >= r.left + width && x < r.right - width &&
            y >= r.top && y < r.top + width) ||
           (x >= r.left + width && x < r.right - width &&
            y >= r.bottom - width && y < r.bottom);
}

static void test_map_window_projection(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    SimGameWorld world;
    PortableOverviewViewInput input = {0};
    PortableOverviewView view;
    PortableWindowRect expected_map, expected_edit;
    PortableFramebuffer framebuffer;
    uint8_t pixels[640u * 400u];
    PortableRect saved_clip = {0, 0, 640, 400};
    PortableRect narrow_clip = {115, 40, 260, 60};
    PortableRect cursor_clip = {132, 60, 137, 65};
    int32_t margin, map_pixel_x, map_pixel_y;

    memset(&world, 0, sizeof world);
    world.map_view_x = 3;
    world.map_view_y = 4;
    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    input.world = &world;
    input.map_mode = 1;
    input.hardware_profile = 0;
    input.map_window_open = 1;
    assert(portable_overview_view_prepare(&registry, &input, &view) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    assert(portable_window_registry_get_object_rect(&registry, 0x0102,
                                                    &expected_map) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_get_object_rect(&registry, 0x0004,
                                                    &expected_edit) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(memcmp(&view.image_rect, &expected_map, sizeof expected_map) == 0);
    assert(memcmp(&view.edit_viewport_rect, &expected_edit,
                  sizeof expected_edit) == 0);
    assert(view.image.width == 128 && view.image.height == 64 &&
           view.image.scale_x == 4 && view.image.left_margin == 0);
    assert(view.cursor_rect_valid && view.cursor_outline_width == 2);
    assert(rect_width(view.cursor_rect) ==
           rect_width(expected_edit) / 16 * 4);
    assert(rect_height(view.cursor_rect) ==
           (rect_height(expected_edit) / 16 + 1) * 4);
    assert(view.cursor_rect.left == expected_map.left + world.map_view_x * 4);
    assert(view.cursor_rect.top == expected_map.top + world.map_view_y * 4);

    memset(pixels, 0x35, sizeof pixels);
    assert(portable_framebuffer_init(&framebuffer, 640, 400, 640, pixels) ==
           PORTABLE_RENDER_OK);
    portable_framebuffer_set_clip(&framebuffer, cursor_clip);
    assert(portable_overview_view_render_cursor(&view, &framebuffer) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    assert(memcmp(&framebuffer.clip, &cursor_clip, sizeof cursor_clip) == 0);
    for (int32_t y = 0; y < 400; ++y) {
        for (int32_t x = 0; x < 640; ++x) {
            uint8_t expected = 0x35;
            if (x >= cursor_clip.left && x < cursor_clip.right &&
                y >= cursor_clip.top && y < cursor_clip.bottom &&
                is_cursor_outline_pixel(&view, x, y))
                expected ^= 0x0f;
            assert(pixels[(size_t)y * 640u + (size_t)x] == expected);
        }
    }
    assert(portable_overview_view_render_cursor(&view, &framebuffer) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    for (size_t i = 0; i < sizeof pixels; ++i)
        assert(pixels[i] == 0x35);

    memset(pixels, 0xa5, sizeof pixels);
    assert(portable_framebuffer_init(&framebuffer, 640, 400, 640, pixels) ==
           PORTABLE_RENDER_OK);
    portable_framebuffer_set_clip(&framebuffer, saved_clip);
    input.map_mode = 2;
    assert(portable_overview_view_prepare(&registry, &input, &view) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    margin = view.image.left_margin;
    assert(margin == 128);
    portable_framebuffer_set_clip(&framebuffer, narrow_clip);
    assert(portable_overview_view_render(&view, &framebuffer) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    assert(memcmp(&framebuffer.clip, &narrow_clip, sizeof narrow_clip) == 0);
    map_pixel_x = view.image_rect.left + margin;
    map_pixel_y = view.image_rect.top;
    assert(map_pixel_x == 248 && map_pixel_y == 44);
    /* Selector 0x0c is black in the top two rows of its source 4x4 tile. */
    assert(pixels[(size_t)map_pixel_y * 640u + (size_t)map_pixel_x] == 0);
    assert(pixels[(size_t)view.image_rect.top * 640u +
                  (size_t)view.image_rect.left] == 15);
    assert(pixels[39u * 640u + 120u] == 0xa5);
    assert(pixels[44u * 640u + 110u] == 0xa5);
    portable_framebuffer_set_clip(&framebuffer, saved_clip);

    input.map_mode = 0;
    assert(portable_overview_view_prepare(&registry, &input, &view) ==
           PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_MODE);
    input.map_mode = 1;
    input.map_window_open = 0;
    assert(portable_overview_view_prepare(&registry, &input, &view) ==
           PORTABLE_OVERVIEW_VIEW_WINDOW_CLOSED);
    input.map_window_open = 1;
    input.hardware_profile = 8;
    assert(portable_overview_view_prepare(&registry, &input, &view) ==
           PORTABLE_OVERVIEW_VIEW_PROFILE_MISMATCH);

    portable_window_registry_destroy(&registry);

    memset(&registry, 0, sizeof registry);
    assert(portable_window_registry_init(&registry, &database, 8) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    input.map_mode = 3;
    assert(portable_overview_view_prepare(&registry, &input, &view) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    assert(view.image.mode == 3 && view.image.width == 64 &&
           view.image.height == 64 && view.image.scale_x == 4 &&
           view.image.left_margin == 128);
    assert(portable_overview_view_render(&view, &framebuffer) ==
           PORTABLE_OVERVIEW_VIEW_OK);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

int main(void)
{
    test_map_window_projection();
    puts("overview window projection tests passed");
    return 0;
}
