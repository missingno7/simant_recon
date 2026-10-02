#include "../../platform/sdl3/menu_modal.h"
#include "../../platform/host.h"

#include <SDL3/SDL.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int forwarded_event(void *context, PortableMenuInput *out)
{
    int *sent = (int *)context;
    if (*sent) return 0;
    *sent = 1;
    memset(out, 0, sizeof(*out));
    out->kind = PORTABLE_MENU_INPUT_WINDOW_EVENT;
    out->event_code = 0xfe01;
    out->event_xe = 0x1234;
    out->event_h = 211;
    out->event_v = 97;
    return 1;
}

static SDL_WindowID test_window_id;

static void push_key(uint32_t type, SDL_Keycode key, SDL_Keymod mod)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = type;
    event.key.windowID = test_window_id;
    event.key.key = key;
    event.key.mod = mod;
    assert(SDL_PushEvent(&event));
}

static void push_mouse(uint32_t type, int x, int y)
{
    SDL_Event event;
    memset(&event, 0, sizeof(event));
    event.type = type;
    event.button.windowID = test_window_id;
    event.button.button = SDL_BUTTON_LEFT;
    /* Test window is 2x the 640x350 renderer. SDL converts this window point
     * through the active logical-presentation transform in host_poll_event. */
    event.button.x = (float)(x * 2);
    event.button.y = (float)(y * 2);
    assert(SDL_PushEvent(&event));
}

static void assert_restored(const uint8_t *pixels, const uint8_t *before,
                            size_t size)
{
    assert(memcmp(pixels, before, size) == 0);
}

int main(int argc, char **argv)
{
    PortableDatabase shared = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand bar_commands[20];
    PortableMenuModalRequest request;
    PortableMenuModalResult result;
    PortableFramebuffer framebuffer;
    PortableBiosFontBitmap font;
    HostPalette palette;
    Host *host;
    uint8_t *pixels, *before, glyphs[256 * 14];
    size_t command_count = 0, bytes = 640u * 350u;
    int i, event_sent = 0, window_count = 0, scan_down;
    SDL_Window **windows;
    HostInputState input_state;
    int32_t click_x, click_y;
    if (argc != 2) {
        fprintf(stderr, "usage: menu-modal-test path-to-SHARED\n");
        return 2;
    }
    assert(portable_db_open(&shared, argv[1]) == PORTABLE_DB_OK);
    portable_menu_init(&menu);
    assert(portable_menu_load(&menu, &shared, 640) == PORTABLE_MENU_OK);
    assert(menu.resource_id == 0 && menu.menu_count == 5);
    assert(portable_menu_build_draw_plan(&menu, 1,
        (PortableMenuRect){0, 0, 640, 350}, 640, 8, 14, 14,
        &layout, bar_commands, 20, &command_count) == PORTABLE_MENU_OK);
    assert(layout.title_count == 5 && menu.items[4].count >= 3);

    pixels = malloc(bytes);
    before = malloc(bytes);
    assert(pixels != NULL && before != NULL);
    memset(pixels, 6, bytes);
    memcpy(before, pixels, bytes);
    memset(glyphs, 0xff, sizeof(glyphs));
    assert(portable_framebuffer_init(&framebuffer, 640, 350, 640, pixels) ==
           PORTABLE_RENDER_OK);
    memset(&font, 0, sizeof(font));
    font.glyph_rows = glyphs;
    font.glyph_rows_size = sizeof(glyphs);
    font.glyph_width = 8;
    font.glyph_height = 14;
    font.provider_id = "test-reference-font";
    for (i = 0; i < 16; ++i) {
        palette.rgb[i][0] = (uint8_t)(i * 17);
        palette.rgb[i][1] = (uint8_t)((15 - i) * 17);
        palette.rgb[i][2] = (uint8_t)(i * 9);
    }
    host = host_create("SDL menu modal test", 1);
    assert(host != NULL);
    windows = SDL_GetWindows(&window_count);
    assert(windows != NULL && window_count > 0);
    assert(SDL_SetWindowSize(windows[0], 1280, 700));
    test_window_id = SDL_GetWindowID(windows[0]);
    SDL_free(windows);
    assert(host_warp_pointer(host, 320, 175));
    SDL_PumpEvents();
    assert(host_get_input_state(host, &input_state));
    assert(abs((int)input_state.x - 320) <= 1 &&
           abs((int)input_state.y - 175) <= 1);
    SDL_SetModState(SDL_KMOD_LSHIFT);
    assert(host_get_input_state(host, &input_state));
    assert(input_state.dos_modifiers == 2);
    SDL_SetModState(SDL_KMOD_NONE);
    assert(host_get_input_state(host, &input_state));
    assert(input_state.dos_modifiers == 0);
    while (1) {
        HostEvent event;
        int status = host_poll_event(host, &event);
        if (status <= 0) break;
    }
    memset(&request, 0, sizeof(request));
    request.menu = &menu;
    request.layout = &layout;
    request.framebuffer = &framebuffer;
    request.font = &font;
    request.host_palette = &palette;
    request.screen_width = 640;
    request.screen_height = 350;
    request.line_height = 14;
    request.char_width = 8;
    request.source_g5fea = 0x0101;
    request.source_g5fec = 0x0b0b;
    request.source_g5fee = 0x0f0f;
    request.menu_index = 4;

    /* Real SDL key queue: source '+' chooses first enabled row and Enter
     * returns its original command id. Popup pixels must be fully restored. */
    push_key(SDL_EVENT_KEY_DOWN, SDLK_LSHIFT, SDL_KMOD_LSHIFT);
    push_key(SDL_EVENT_KEY_UP, SDLK_LSHIFT, SDL_KMOD_NONE);
    push_key(SDL_EVENT_KEY_DOWN, SDLK_EQUALS, SDL_KMOD_LSHIFT);
    push_key(SDL_EVENT_KEY_DOWN, SDLK_RETURN, SDL_KMOD_NONE);
    assert(portable_menu_modal_run(host, &request, &result) ==
           PORTABLE_MENU_MODAL_COMMAND);
    assert(result.returned && result.selection_written && result.selection == 1);
    assert(result.command_id == (int16_t)((4 << 4) - 0x2ff));
    assert(result.input_state_valid && !result.left_button_down &&
           result.observed_dos_modifiers == 0);
    assert(host_is_dos_scan_down(host, 0x2a, &scan_down) && !scan_down);
    assert(result.pointer_x >= 0 && result.pointer_x < 640 &&
           result.pointer_y >= 0 && result.pointer_y < 350);
    assert_restored(pixels, before, bytes);

    /* Real SDL pointer-down/up over the third source item, below the separator. */
    {
        PortableMenuInteraction geometry;
        assert(portable_menu_interaction_init_from_bar(&geometry, &menu, &layout,
            4, 640, 350, 14, 8, 0) == PORTABLE_MENU_INTERACTION_RUNNING);
        click_x = geometry.saved_rect.left + 17;
        click_y = geometry.saved_rect.top + 3 + 2 * 14 + 1;
    }
    push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN, click_x, click_y);
    push_mouse(SDL_EVENT_MOUSE_BUTTON_UP, click_x, click_y);
    assert(portable_menu_modal_run(host, &request, &result) ==
           PORTABLE_MENU_MODAL_COMMAND);
    assert(result.returned && result.selection_written && result.selection == 3);
    assert(result.command_id == (int16_t)((4 << 4) + 2 - 0x2ff));
    assert_restored(pixels, before, bytes);

    /* A source-normalized FE event retains all caller-supplied words; xE is
     * intentionally provided by the source event owner, not SDL synthesis. */
    request.poll_source_event = forwarded_event;
    request.source_event_context = &event_sent;
    assert(portable_menu_modal_run(host, &request, &result) ==
           PORTABLE_MENU_MODAL_FORWARDED_SOURCE_EVENT);
    assert(result.forwarded_event && result.forwarded_event_words[0] == 0xfe01 &&
           result.forwarded_event_words[1] == 0x1234 &&
           result.forwarded_event_words[2] == 211 &&
           result.forwarded_event_words[3] == 97);
    assert_restored(pixels, before, bytes);

    /* Physical click on another actual title is returned for source event
     * translation instead of manufacturing the unproved xE event field. */
    request.poll_source_event = NULL;
    request.source_event_context = NULL;
    push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN,
        (layout.title_rects[1].left + layout.title_rects[1].right) / 2, 5);
    assert(portable_menu_modal_run(host, &request, &result) ==
           PORTABLE_MENU_MODAL_PHYSICAL_TITLE_EVENT);
    assert(result.physical_title_index_valid && result.physical_title_index == 1);
    assert_restored(pixels, before, bytes);

    host_destroy(host);
    portable_menu_release(&menu);
    portable_db_close(&shared);
    free(before);
    free(pixels);
    puts("actual SHARED menu: SDL key, pointer, title handoff, source event forwarding, scaled warp, physical-state reconciliation, and popup restoration PASS");
    return 0;
}
