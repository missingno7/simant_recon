#include "../../ui_model/menus/menu.h"
#include "../../ui_model/menus/render.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void check_source_color_profiles(void)
{
    PortableMenuRasterColors colors;
    assert(portable_menu_raster_colors_for_width(320, &colors) == PORTABLE_RENDER_OK);
    assert(colors.normal_foreground == 8 && colors.background == 11 &&
           colors.highlighted_foreground == 0);
    assert(portable_menu_raster_colors_for_width(640, &colors) == PORTABLE_RENDER_OK);
    assert(colors.normal_foreground == 7 && colors.background == 14 &&
           colors.highlighted_foreground == 12);
    assert(portable_menu_raster_colors_for_width(0, &colors) ==
           PORTABLE_RENDER_INVALID_ARGUMENT);
}

static void check_draw_plan(const char *assets)
{
    PortableDatabase shared = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[20];
    PortableMenuRasterColors colors;
    PortableBiosFontBitmap font;
    PortableFramebuffer framebuffer;
    uint8_t glyphs[256 * 14];
    uint8_t pixels[640 * 20];
    size_t command_count = 0;
    char root[1024];
    assert(snprintf(root, sizeof(root), "%s/SHARED", assets) < (int)sizeof(root));
    assert(portable_db_open(&shared, root) == PORTABLE_DB_OK);
    portable_menu_init(&menu);
    assert(portable_menu_load(&menu, &shared, 640) == PORTABLE_MENU_OK);
    assert(menu.resource_id == 0 && menu.titles.count == 5);
    assert(portable_menu_set_highlight_by_id(&menu, 0, 1) == PORTABLE_MENU_OK);
    assert(portable_menu_build_draw_plan(&menu, 1,
               (PortableMenuRect){0, 0, 640, 350}, 640, 8, 14, 3,
               &layout, commands, 20, &command_count) == PORTABLE_MENU_OK);
    assert(command_count == 7 && commands[0].kind == PORTABLE_MENU_DRAW_SET_COLOR_MODE);
    assert(commands[2].kind == PORTABLE_MENU_DRAW_TEXT &&
           commands[2].source_color_mode == 3 && commands[2].clear_first_high_bit);
    assert(commands[3].kind == PORTABLE_MENU_DRAW_TEXT &&
           commands[3].source_color_mode == 1 && !commands[3].clear_first_high_bit);

    /* Controlled reference glyph makes the high-bit-cleared and raw glyph
     * visibly different; all other glyphs are blank. */
    memset(glyphs, 0, sizeof(glyphs));
    glyphs[0x20u * 14u] = 0x80;
    glyphs[0xa0u * 14u] = 0x40;
    font = (PortableBiosFontBitmap){glyphs, sizeof(glyphs), 8, 14,
                                    "controlled-test-reference"};
    memset(pixels, 9, sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer, 640, 20, 640, pixels) ==
           PORTABLE_RENDER_OK);
    assert(portable_menu_raster_colors_for_width(640, &colors) == PORTABLE_RENDER_OK);
    assert(portable_menu_render_draw_plan(&framebuffer, &font, &colors,
                                          commands, command_count) ==
           PORTABLE_RENDER_OK);

    /* Source fill spans the menu bar; title glyphs use the selected normal or
     * highlight palette tuple and the leading state bit is removed privately. */
    assert(pixels[0] == 3 && pixels[16 * 640] == 3 && pixels[17 * 640] == 9);
    assert(pixels[1 * 640] == 12 && pixels[1 * 640 + 1] == 14);
    assert(pixels[1 * 640 + 64] == 7 && pixels[1 * 640 + 65] == 14);

    commands[2].source_color_mode = 0;
    assert(portable_menu_render_draw_plan(&framebuffer, &font, &colors,
                                          commands, command_count) ==
           PORTABLE_RENDER_UNSUPPORTED_MODE);
    puts("actual_resource=fallback-id0 kind6 titles=5 drawplan=7 commands\n"
         "screen=640x20 fill=source-index-3 normal=7/14 highlight=12/14 "
         "MSB-first=pass high-bit-private-clear=pass unsupported-mode=fail-closed");
    portable_menu_release(&menu);
    portable_db_close(&shared);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    check_source_color_profiles();
    check_draw_plan(argv[1]);
    return 0;
}
