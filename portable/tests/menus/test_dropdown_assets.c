#include "../../ui_model/menus/dropdown_render.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { SCREEN_W = 640, SCREEN_H = 350, MAX_COMMANDS = 256, MAX_TEXT = 4000 };

static void read_font(const char *directory, const char *name,
                      uint8_t *destination, size_t expected_size)
{
    char path[1024];
    FILE *file;
    assert(snprintf(path, sizeof(path), "%s/%s", directory, name) <
           (int)sizeof(path));
    file = fopen(path, "rb");
    assert(file != NULL);
    assert(fread(destination, 1, expected_size, file) == expected_size);
    assert(fgetc(file) == EOF);
    assert(fclose(file) == 0);
}

static void save_rect(const uint8_t *pixels, size_t stride,
                      PortableMenuDropdownRect rect, uint8_t *saved)
{
    int32_t y;
    size_t width = (size_t)(rect.right - rect.left);
    for (y = rect.top; y < rect.bottom; ++y)
        memcpy(saved + (size_t)(y - rect.top) * width,
               pixels + (size_t)y * stride + (size_t)rect.left, width);
}

static void restore_rect(uint8_t *pixels, size_t stride,
                         PortableMenuDropdownRect rect, const uint8_t *saved)
{
    int32_t y;
    size_t width = (size_t)(rect.right - rect.left);
    for (y = rect.top; y < rect.bottom; ++y)
        memcpy(pixels + (size_t)y * stride + (size_t)rect.left,
               saved + (size_t)(y - rect.top) * width, width);
}

int main(int argc, char **argv)
{
    PortableDatabase shared = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand bar_commands[32];
    PortableMenuInteraction interaction;
    PortableMenuDropdownDrawCommand commands[MAX_COMMANDS];
    PortableMenuDropdownDrawCommand highlight_commands[8];
    PortableBiosFontBitmap font_8x14;
    uint8_t glyphs[256 * 14];
    PortableFramebuffer framebuffer;
    uint8_t *pixels, *initial, *saved;
    uint8_t text_storage[MAX_TEXT], highlight_storage[MAX_TEXT];
    int16_t mode_pen[4];
    size_t count, used, i, enabled_rows = 0;
    int32_t color;
    int rendered = 0;
    char shared_root[1024];
    if (argc != 3) {
        fprintf(stderr, "usage: test-dropdown-assets asset-directory bios-font-directory\n");
        return 2;
    }
    assert(snprintf(shared_root, sizeof(shared_root), "%s/SHARED", argv[1]) <
           (int)sizeof(shared_root));
    assert(portable_db_open(&shared, shared_root) == PORTABLE_DB_OK);
    portable_menu_init(&menu);
    assert(portable_menu_load(&menu, &shared, SCREEN_W) == PORTABLE_MENU_OK);
    assert(menu.resource_id == 0 && menu.menu_count == 5);
    assert(portable_menu_build_draw_plan(&menu, 1,
        (PortableMenuRect){0, 0, SCREEN_W, SCREEN_H}, SCREEN_W, 8, 14, 0,
        &layout, bar_commands, 32, &count) == PORTABLE_MENU_OK);
    read_font(argv[2], "font-8x14.bin", glyphs, sizeof(glyphs));
    font_8x14 = (PortableBiosFontBitmap){glyphs, sizeof(glyphs), 8, 14,
        "DOSBox Staging/v0.83.0/7b40053b7ac580843d0461eba8c36a47a990e66c"};
    portable_menu_dropdown_source_pen_colors(0x0101, 0x0b0b, 0x0f0f, mode_pen);
    pixels = (uint8_t *)calloc((size_t)SCREEN_W * SCREEN_H, 1);
    initial = (uint8_t *)calloc((size_t)SCREEN_W * SCREEN_H, 1);
    assert(pixels != NULL && initial != NULL);
    assert(portable_framebuffer_init(&framebuffer, SCREEN_W, SCREEN_H,
        SCREEN_W, pixels) == PORTABLE_RENDER_OK);

    for (i = 0; i < menu.menu_count; ++i) {
        PortableMenuInteractionStatus interaction_status;
        size_t row;
        interaction_status = portable_menu_interaction_init_from_bar(
            &interaction, &menu, &layout, i, SCREEN_W, SCREEN_H, 14, 8, 1);
        if (interaction_status == PORTABLE_MENU_INTERACTION_DISABLED_TITLE)
            continue;
        assert(interaction_status == PORTABLE_MENU_INTERACTION_RUNNING);
        assert(portable_menu_dropdown_build_open_plan(&interaction, -1,
            0x0101, 0x0b0b, 0x0f0f, mode_pen,
            commands, MAX_COMMANDS, text_storage, sizeof(text_storage),
            &count, &used) == PORTABLE_DROPDOWN_RENDER_OK);
        memset(pixels, 0, (size_t)SCREEN_W * SCREEN_H);
        memcpy(initial, pixels, (size_t)SCREEN_W * SCREEN_H);
        saved = (uint8_t *)malloc((size_t)(interaction.saved_rect.right -
            interaction.saved_rect.left) * (size_t)(interaction.saved_rect.bottom -
            interaction.saved_rect.top));
        assert(saved != NULL);
        save_rect(pixels, SCREEN_W, interaction.saved_rect, saved);
        assert(portable_menu_dropdown_rasterize(&framebuffer,
            &font_8x14, interaction.saved_rect,
            commands, count) == PORTABLE_DROPDOWN_RENDER_OK);
        for (color = 0; color < SCREEN_W * SCREEN_H; ++color)
            if (pixels[color] != initial[color]) break;
        assert(color < SCREEN_W * SCREEN_H);
        for (row = 0; row < interaction.item_count; ++row)
            if (interaction.row_enabled[row]) break;
        if (row < interaction.item_count) {
            assert(portable_menu_dropdown_build_highlight_plan(&interaction,
                -1, (int)row, 0x0101, 0x0b0b, 0x0f0f, mode_pen,
                highlight_commands, 8, highlight_storage,
                sizeof(highlight_storage), &count, &used) ==
                PORTABLE_DROPDOWN_RENDER_OK);
            assert(portable_menu_dropdown_rasterize(&framebuffer,
                &font_8x14, interaction.saved_rect,
                highlight_commands, count) == PORTABLE_DROPDOWN_RENDER_OK);
            ++enabled_rows;
        }
        restore_rect(pixels, SCREEN_W, interaction.saved_rect, saved);
        assert(memcmp(pixels, initial, (size_t)SCREEN_W * SCREEN_H) == 0);
        free(saved);
        ++rendered;
    }
    assert(rendered > 0 && enabled_rows > 0);
    printf("actual SHARED menu id 0: %d enabled title menus rasterized with %s; %zu highlight rows and exact saved-rect restoration passed\n",
           rendered, font_8x14.provider_id, enabled_rows);
    free(pixels);
    free(initial);
    portable_menu_release(&menu);
    portable_db_close(&shared);
    return 0;
}
