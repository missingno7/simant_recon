#include "../../ui_model/menus/dropdown_render.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    static const uint8_t alpha[] = " Alpha";
    static const uint8_t separator[] = " -";
    static const uint8_t disabled[] = {0xc2, 'e', 't', 'a'};
    static const uint8_t gamma[] = " Gamma";
    const PortableMenuItemSpan items[] = {
        {alpha, sizeof(alpha) - 1},
        {separator, sizeof(separator) - 1},
        {disabled, sizeof(disabled)},
        {gamma, sizeof(gamma) - 1}
    };
    PortableMenuInteraction interaction;
    PortableMenuDropdownDrawCommand commands[64];
    uint8_t storage[128];
    uint8_t glyphs[256 * 14], pixels[128 * 100], before[128 * 100];
    PortableBiosFontBitmap font;
    PortableFramebuffer framebuffer;
    size_t count, used, i, primitive_count = 0, text_count = 0, mode_count = 0;
    int16_t mode_pen[4];
    int saw_separator = 0, saw_disabled = 0;

    memset(&interaction, 0, sizeof(interaction));
    memcpy(interaction.items, items, sizeof(items));
    interaction.item_count = 4;
    interaction.menu_index = 0;
    interaction.current_item = -1;
    interaction.saved_rect = (PortableMenuDropdownRect){20, 15, 92, 77};
    interaction.inner_rect = (PortableMenuDropdownRect){28, 18, 84, 74};
    interaction.line_height = 14;
    interaction.char_width = 8;
    portable_menu_dropdown_source_pen_colors(0x0101, 0x0b0b, 0x0f0f, mode_pen);
    assert(mode_pen[0] == 0x0b && mode_pen[1] == 0x01 &&
           mode_pen[2] == 0x0f && mode_pen[3] == 0x0f);
    assert(portable_menu_dropdown_build_open_plan(&interaction, -1,
        0x0101, 0x0b0b, 0x0f0f, mode_pen,
        commands, 64, storage, sizeof(storage), &count, &used) ==
        PORTABLE_DROPDOWN_RENDER_OK);
    assert(count == 3 + 8 + 2 * 4);
    assert(used == 7 * 4);
    for (i = 0; i < count; ++i) {
        const PortableMenuDropdownDrawCommand *command = &commands[i];
        if (command->kind == PORTABLE_DROPDOWN_SET_MODE) {
            ++mode_count;
            assert(command->attribute_foreground ==
                (command->mode == 0 ? 0x0b0b : command->mode == 1 ? 0x0101 : 0x0f0f));
            assert(command->attribute_background ==
                (command->mode == 0 || command->mode == 2 ? 0x0101 : 0x0b0b));
        } else if (command->kind == PORTABLE_DROPDOWN_FILL_PRIMITIVE) {
            ++primitive_count;
            assert(command->rect.left >= interaction.saved_rect.left);
            assert(command->rect.top >= interaction.saved_rect.top);
            assert(command->rect.right <= interaction.saved_rect.right);
            assert(command->rect.bottom <= interaction.saved_rect.bottom);
        } else if (command->kind == PORTABLE_DROPDOWN_TEXT) {
            ++text_count;
            assert(command->x >= interaction.saved_rect.left);
            assert(command->y >= interaction.saved_rect.top);
            assert(command->text_length == 6);
            if (command->text[1] == '-' && command->text[0] == ' ')
                saw_separator = 1;
            if ((command->text[0] & 0x80u) != 0 && command->clear_first_high_bit &&
                command->mode == 3)
                saw_disabled = 1;
            assert(command->x + (int32_t)command->text_length * 8 <=
                   interaction.saved_rect.right);
        }
    }
    assert(mode_count == 7 && primitive_count == 8 && text_count == 4);
    assert(saw_separator && saw_disabled);

    memset(glyphs, 0, sizeof(glyphs));
    glyphs[(size_t)'A' * 14] = 0x80;
    font = (PortableBiosFontBitmap){glyphs, sizeof(glyphs), 8, 14,
                                    "controlled-reference-font"};
    memset(pixels, 5, sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer, 128, 100, 128, pixels) ==
           PORTABLE_RENDER_OK);
    memcpy(before, pixels, sizeof(before));
    assert(portable_menu_dropdown_rasterize(&framebuffer, &font,
        interaction.saved_rect, commands, count) == PORTABLE_DROPDOWN_RENDER_OK);
    assert(framebuffer.clip.left == 0 && framebuffer.clip.right == 128 &&
           framebuffer.clip.top == 0 && framebuffer.clip.bottom == 100);
    assert(pixels[15 * 128 + 27] == 1); /* Source mode-1 outline pen. */
    assert(pixels[18 * 128 + 28] == 11); /* Space glyph background. */
    assert(pixels[18 * 128 + 36] == 1); /* MSB-first A glyph foreground. */
    assert(pixels[10 * 128 + 10] == 5 && pixels[80 * 128 + 100] == 5);
    assert(portable_menu_dropdown_build_highlight_plan(&interaction, -1, 0,
        0x0101, 0x0b0b, 0x0f0f, mode_pen,
        commands, 64, storage, sizeof(storage), &count, &used) ==
        PORTABLE_DROPDOWN_RENDER_OK);
    assert(portable_menu_dropdown_rasterize(&framebuffer, &font,
        interaction.saved_rect, commands, count) == PORTABLE_DROPDOWN_RENDER_OK);
    assert(pixels[18 * 128 + 28] == 1);  /* Inverse-mode space background. */
    assert(pixels[18 * 128 + 36] == 11); /* Inverse-mode A foreground. */
    {
        int32_t y, x;
        for (y = interaction.saved_rect.top; y < interaction.saved_rect.bottom; ++y)
            for (x = interaction.saved_rect.left; x < interaction.saved_rect.right; ++x)
                pixels[(size_t)y * 128 + (size_t)x] =
                    before[(size_t)y * 128 + (size_t)x];
    }
    assert(memcmp(pixels, before, sizeof(before)) == 0);

    assert(portable_menu_dropdown_build_highlight_plan(&interaction, 0, 3,
        0x0101, 0x0b0b, 0x0f0f, mode_pen,
        commands, 64, storage, sizeof(storage), &count, &used) ==
        PORTABLE_DROPDOWN_RENDER_OK);
    assert(count == 4 && used == 14);
    assert(commands[0].kind == PORTABLE_DROPDOWN_SET_MODE && commands[0].mode == 1);
    assert(commands[1].kind == PORTABLE_DROPDOWN_TEXT && commands[1].text[1] == 'A');
    assert(commands[2].kind == PORTABLE_DROPDOWN_SET_MODE && commands[2].mode == 0);
    assert(commands[3].kind == PORTABLE_DROPDOWN_TEXT && commands[3].text[1] == 'G');
    assert(portable_menu_dropdown_build_highlight_plan(&interaction, 2, 2,
        0x0101, 0x0b0b, 0x0f0f, mode_pen,
        commands, 64, storage, sizeof(storage), &count, &used) ==
        PORTABLE_DROPDOWN_RENDER_OK);
    assert(count == 0 && used == 0);
    assert(portable_menu_dropdown_build_open_plan(&interaction, -1,
        0x0101, 0x0b0b, 0x0f0f, mode_pen,
        commands, 4, storage, sizeof(storage), &count, &used) ==
        PORTABLE_DROPDOWN_RENDER_OUTPUT_TOO_SMALL);
    {
        int16_t unrelated_pen[4] = {0, 0, 0, 0};
        assert(portable_menu_dropdown_build_open_plan(&interaction, -1,
            0x0101, 0x0b0b, 0x0f0f, unrelated_pen,
            commands, 64, storage, sizeof(storage), &count, &used) ==
            PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT);
    }
    puts("dropdown source-command plan tests passed");
    return 0;
}
