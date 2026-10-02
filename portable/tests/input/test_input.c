#include "../../ui_model/input/input.h"

#include <assert.h>
#include <stdio.h>

static void assert_effect(const PortableInputEffects *effects, size_t index,
                          PortableInputEffectKind kind, int value)
{
    assert(index < effects->count);
    assert(effects->items[index].kind == kind);
    assert(effects->items[index].value == value);
}

static void test_bios_key_decoder(void)
{
    static const uint8_t modifiers[] = {0x1d, 0x2a, 0x36, 0x38};
    int16_t key;
    size_t i;
    assert(portable_input_decode_bios_key(0x1e61, &key) == PORTABLE_INPUT_OK);
    assert(key == 'a');
    assert(portable_input_decode_bios_key(0x2a41, &key) == PORTABLE_INPUT_OK);
    assert(key == 'A');
    assert(portable_input_decode_bios_key(0x1e01, &key) == PORTABLE_INPUT_OK);
    assert(key == 1); /* Ctrl-A remains the BIOS control code. */
    assert(portable_input_decode_bios_key(0x0e7f, &key) == PORTABLE_INPUT_OK);
    assert(key == 0x7f);
    assert(portable_input_decode_bios_key(0x12e0, &key) == PORTABLE_INPUT_OK);
    assert(key == -32); /* CBW sign extension for high ASCII. */
    assert(portable_input_decode_bios_key(0x2100, &key) == PORTABLE_INPUT_OK);
    assert(key == 0x0821);
    assert(portable_input_decode_bios_key(0x4800, &key) == PORTABLE_INPUT_OK);
    assert(key == 0x0848);
    assert(portable_input_decode_bios_key(0, &key) == PORTABLE_INPUT_NO_KEY);
    for (i = 0; i < sizeof(modifiers); ++i) {
        uint16_t word = (uint16_t)((uint16_t)modifiers[i] << 8);
        assert(portable_input_decode_bios_key(word, &key) ==
               PORTABLE_INPUT_MODIFIER_ONLY);
    }
    /* A printable key remains a key even when its physical scan is Shift. */
    assert(portable_input_decode_bios_key(0x2a21, &key) == PORTABLE_INPUT_OK);
    assert(key == '!');
    assert(portable_input_decode_bios_key(0, NULL) == PORTABLE_INPUT_BAD_ARGUMENT);
}

static void test_shortcut_translation(void)
{
    PortableInputEffects effects;
    unsigned i;
    for (i = 0; i < 4; ++i) {
        const uint16_t keys[4] = {0x21, 0x40, 0x23, 0x24};
        assert(portable_input_key(keys[i], 0, 1, 0, 0, &effects) == PORTABLE_INPUT_OK);
        assert(effects.count == 1);
        assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_SPEED, (int)i);
    }
    assert(portable_input_key(0x29, 0, 0, 0, 0, &effects) == PORTABLE_INPUT_OK);
    assert(effects.count == 1);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_PAUSED, 1);
    assert(portable_input_key(0x821, 0, 0, 0, 0, &effects) ==
           PORTABLE_INPUT_UNSUPPORTED_ACTION);
    assert(portable_input_key(0x777, 0, 0, 0, 0, &effects) == PORTABLE_INPUT_UNBOUND);
    assert(portable_input_key(0x05, 0, 0, 0, 0, &effects) == PORTABLE_INPUT_OK);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_OPEN_EDIT, 0);
    assert(portable_input_key(0x0d, 0, 0, 0, 0, &effects) == PORTABLE_INPUT_OK);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_OPEN_MAP_YARD, 0);
}

static void test_menu_and_object_intents(void)
{
    PortableInputEffects effects;
    assert(portable_input_menu_item(0x22, 0, 3, 0, 0, &effects) == PORTABLE_INPUT_OK);
    assert(effects.count == 3);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_YARD_MODE, 1);
    assert_effect(&effects, 1, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE, 0);
    assert_effect(&effects, 2, PORTABLE_INPUT_EFFECT_ENSURE_YARD_VIEW, 0);
    assert(portable_input_menu_item(0x24, 0, 0, 3, 1, &effects) == PORTABLE_INPUT_OK);
    assert(effects.count == 0);
    assert(portable_input_menu_item(0x28, 0, 1, 1, 1, &effects) == PORTABLE_INPUT_OK);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE, 3);
    assert(portable_input_menu_item(0x03, 0, 1, 1, 1, &effects) ==
           PORTABLE_INPUT_UNSUPPORTED_ACTION);
    assert(portable_input_edit_event(8, 0, &effects) == PORTABLE_INPUT_OK);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE, 1);
    assert(portable_input_edit_event(15, 1, &effects) == PORTABLE_INPUT_OK);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_PAUSED, 0);
    assert(portable_input_edit_event(4, 0, &effects) ==
           PORTABLE_INPUT_UNSUPPORTED_ACTION);
    assert(portable_input_map_event(0x108, &effects) == PORTABLE_INPUT_OK);
    assert_effect(&effects, 0, PORTABLE_INPUT_EFFECT_SET_MAP_PLANE, 3);
    assert(portable_input_map_event(0x102, &effects) ==
           PORTABLE_INPUT_UNSUPPORTED_ACTION);
}

static void test_keypad_camera_movement(void)
{
    const uint16_t diagonal[] = {0x47, 0x4d};
    const uint16_t cancelling[] = {0x47, 0x51, 0x48};
    int16_t dx, dy, x, y;
    assert(portable_input_camera_delta(0, diagonal, 2, &dx, &dy) == PORTABLE_INPUT_OK);
    assert(dx == 0 && dy == 0);
    assert(portable_input_camera_delta(1, diagonal, 2, &dx, &dy) == PORTABLE_INPUT_OK);
    assert(dx == 0 && dy == -1);
    assert(portable_input_camera_delta(1, cancelling, 3, &dx, &dy) == PORTABLE_INPUT_OK);
    assert(dx == 0 && dy == -1);
    assert(portable_input_mouse_edge_delta(0, 1, 0, 640, 480, &dx, &dy) == PORTABLE_INPUT_OK);
    assert(dx == -1 && dy == -1);
    assert(portable_input_mouse_edge_delta(0, 636, 476, 640, 480, &dx, &dy) == PORTABLE_INPUT_OK);
    assert(dx == 1 && dy == 1);
    assert(portable_input_mouse_edge_delta(1, 1, 0, 640, 480, &dx, &dy) == PORTABLE_INPUT_OK);
    assert(dx == 0 && dy == 0);
    assert(portable_input_pan_camera(0, 40, 20, 20, 10, 1, 1, &x, &y) == PORTABLE_INPUT_OK);
    assert(x == 41 && y == 21);
    assert(portable_input_pan_camera(0, 0, 0, 20, 10, -3, -2, &x, &y) == PORTABLE_INPUT_OK);
    assert(x == 0 && y == 0);
    assert(portable_input_pan_camera(2, 50, 55, 20, 10, 4, 4, &x, &y) == PORTABLE_INPUT_OK);
    assert(x == 44 && y == 54);
    assert(portable_input_pan_camera(2, 0, 0, 65, 10, 1, 1, &x, &y) ==
           PORTABLE_INPUT_INVALID_PAN);
}

int main(void)
{
    test_bios_key_decoder();
    test_shortcut_translation();
    test_menu_and_object_intents();
    test_keypad_camera_movement();
    puts("source-backed input model tests passed");
    return 0;
}
