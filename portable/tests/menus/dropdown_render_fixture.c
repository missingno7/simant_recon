#include "../../ui_model/menus/dropdown_render.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

static void print_hex(const uint8_t *bytes, size_t length)
{
    size_t i;
    for (i = 0; i < length; ++i) printf("%02x", bytes[i]);
}

int main(int argc, char **argv)
{
    static const uint8_t alpha[] = " Alpha";
    static const uint8_t separator[] = " -";
    static const uint8_t disabled[] = {0xc2, 'e', 't', 'a'};
    static const uint8_t gamma[] = " Gamma";
    const PortableMenuItemSpan items[] = {
        {alpha, sizeof(alpha) - 1}, {separator, sizeof(separator) - 1},
        {disabled, sizeof(disabled)}, {gamma, sizeof(gamma) - 1}
    };
    const int16_t mode_pen[] = {11, 1, 15, 15};
    PortableMenuInteraction interaction;
    PortableMenuDropdownDrawCommand commands[64];
    uint8_t storage[128];
    size_t count, used, i;
    long title_x, title_length;
    if (argc != 3) return 2;
    title_x = strtol(argv[1], NULL, 10);
    title_length = strtol(argv[2], NULL, 10);
    if (title_x < -32768 || title_x > 32767 ||
        title_length < 0 || title_length > 32767) return 2;
    if (portable_menu_interaction_init(&interaction, items, 4, 0,
            (int32_t)title_x, (size_t)title_length, 640, 400, 12, 8, 1) !=
        PORTABLE_MENU_INTERACTION_RUNNING) return 3;
    if (portable_menu_dropdown_build_open_plan(&interaction, -1,
            0x0101, 0x0b0b, 0x0f0f, mode_pen,
            commands, 64, storage, sizeof(storage), &count, &used) !=
        PORTABLE_DROPDOWN_RENDER_OK) return 4;
    printf("{\"saved_rect\":[%d,%d,%d,%d],\"commands\":[",
        interaction.saved_rect.left, interaction.saved_rect.top,
        interaction.saved_rect.right, interaction.saved_rect.bottom);
    for (i = 0; i < count; ++i) {
        const PortableMenuDropdownDrawCommand *c = &commands[i];
        if (i) putchar(',');
        if (c->kind == PORTABLE_DROPDOWN_SET_MODE) {
            printf("{\"kind\":\"mode\",\"mode\":%d,\"attrs\":[%d,%d,%d]}",
                c->mode, c->attribute_foreground, c->attribute_background,
                c->attribute_pattern);
        } else if (c->kind == PORTABLE_DROPDOWN_FILL_PRIMITIVE) {
            printf("{\"kind\":\"rect\",\"rect\":[%d,%d,%d,%d],\"color\":%d}",
                c->rect.left, c->rect.top, c->rect.right, c->rect.bottom,
                c->primitive_color);
        } else if (c->kind == PORTABLE_DROPDOWN_TEXT) {
            printf("{\"kind\":\"text\",\"x\":%d,\"y\":%d,\"text_hex\":\"",
                c->x, c->y);
            print_hex(c->text, c->text_length);
            printf("\",\"mode\":%d,\"clear\":%u}", c->mode,
                c->clear_first_high_bit);
        } else return 5;
    }
    printf("]}\n");
    return 0;
}
