#include "../../platform/sdl3/picture_modal.h"
#include "../../game/resources/bios_fonts.h"
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct TestClock { volatile uint32_t tick; } TestClock;
typedef enum InjectKind {
    INJECT_KEY, INJECT_MODIFIER, INJECT_MOUSE, INJECT_QUIT, INJECT_CLOCK
} InjectKind;
typedef struct InjectEvent {
    InjectKind kind;
    int x, y;
    uint32_t delay_ms, clock_value;
    TestClock *clock;
    volatile int fired;
} InjectEvent;

static uint32_t read_test_clock(void *context)
{
    return ((TestClock *)context)->tick;
}

static Uint32 push_later(void *context, Uint32 interval, Uint32 missed)
{
    InjectEvent *spec = (InjectEvent *)context;
    SDL_Event event;
    (void)interval;
    (void)missed;
    memset(&event, 0, sizeof(event));
    if (spec->kind == INJECT_KEY) {
        event.type = SDL_EVENT_KEY_DOWN;
        event.key.key = SDLK_ESCAPE;
    } else if (spec->kind == INJECT_MODIFIER) {
        event.type = SDL_EVENT_KEY_DOWN;
        event.key.key = SDLK_LCTRL;
    } else if (spec->kind == INJECT_MOUSE) {
        event.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
        event.button.button = SDL_BUTTON_LEFT;
        event.button.x = (float)spec->x;
        event.button.y = (float)spec->y;
    } else if (spec->kind == INJECT_QUIT) {
        event.type = SDL_EVENT_QUIT;
    } else {
        spec->clock->tick = spec->clock_value;
        spec->fired = 1;
        return 0;
    }
    spec->fired = 1;
    (void)SDL_PushEvent(&event);
    return 0;
}

static void schedule(InjectEvent *event)
{
    if (SDL_AddTimer(event->delay_ms, push_later, (void *)event) == 0) {
        fprintf(stderr, "SDL_AddTimer failed: %s\n", SDL_GetError());
        exit(2);
    }
}

static int same_bytes(const uint8_t *a, const uint8_t *b, size_t count)
{
    return memcmp(a, b, count) == 0;
}

static int run_case(Host *host, const PortablePalette *palette,
                    const PortableFontSet *fonts,
                    const PortableWindowRenderer *renderer,
                    PortableDatabase *shared, PortableDatabase *windows,
                    const uint8_t *before, size_t byte_count,
                    InjectEvent *events, size_t event_count,
                    TestClock *clock,
                    PortablePictureModalStatus expected, int expect_quit)
{
    PortablePictureDialogRequest request = {0, 11000, 1, 0,
                                            HOST_LOGICAL_WIDTH,
                                            HOST_LOGICAL_HEIGHT};
    volatile int quit_flag = 0;
    size_t i;
    PortablePictureModalStatus status;
    HostEvent drained;
    while (host_poll_event(host, &drained) > 0) {}
    for (i = 0; i < event_count; ++i)
        schedule(&events[i]);
    status = portable_picture_modal_run_clocked(
        host, palette, fonts, renderer, shared, windows, request,
        read_test_clock, clock, &quit_flag);
    for (i = 0; i < event_count; ++i) {
        if (!events[i].fired) {
            fprintf(stderr, "modal returned before scheduled event %zu\n", i);
            return 0;
        }
    }
    if (status != expected || (!!quit_flag) != (!!expect_quit) ||
        !same_bytes(renderer->framebuffer->pixels, before, byte_count)) {
        fprintf(stderr, "modal returned %s, expected %s; quit=%d; restored=%d\n",
                portable_picture_modal_status_string(status),
                portable_picture_modal_status_string(expected), quit_flag,
                same_bytes(renderer->framebuffer->pixels, before, byte_count));
        return 0;
    }
    return 1;
}

int main(int argc, char **argv)
{
    PortableDatabase shared = {0}, windows = {0};
    PortableDbRecord colors = {0}, palette_record = {0};
    PortableFontSet fonts;
    PortableBiosFonts bios;
    PortablePalette palette;
    PortableWindowRenderer renderer = {0};
    PortableFramebuffer framebuffer;
    Host *host = NULL;
    HostPalette host_palette;
    uint8_t *pixels = NULL, *before = NULL;
    size_t pixel_bytes = HOST_LOGICAL_WIDTH * HOST_LOGICAL_HEIGHT, i;
    int okay = 0;
    PortablePictureDialog dialog = {0};
    PortablePictureDialogRequest inspect_request = {0, 11000, 1, 0,
                                                     HOST_LOGICAL_WIDTH,
                                                     HOST_LOGICAL_HEIGHT};
    TestClock clock = {UINT32_C(1000)};
    InjectEvent inside_then_key[] = {
        {INJECT_MOUSE, 0, 0, 80, 0, NULL, 0},
        {INJECT_KEY, 0, 0, 180, 0, NULL, 0}
    };
    InjectEvent outside_then_key[] = {
        {INJECT_MOUSE, 4, 4, 80, 0, NULL, 0},
        {INJECT_KEY, 0, 0, 180, 0, NULL, 0}
    };
    InjectEvent quit_event[] = {{INJECT_QUIT, 0, 0, 80, 0, NULL, 0}};
    InjectEvent timeout_events[] = {
        {INJECT_MODIFIER, 0, 0, 80, 0, NULL, 0},
        {INJECT_CLOCK, 0, 0, 140, UINT32_C(1269), &clock, 0},
        {INJECT_CLOCK, 0, 0, 200, UINT32_C(1270), &clock, 0}
    };
    PortablePictureModalStatus click_status;
    size_t outside_event_count;
    uint16_t source_window_flags = 0;
    char bios_provider_id[96] = "unavailable";
    if (argc != 2) {
        fprintf(stderr, "usage: picture-modal-host-test asset-directory\n");
        return 2;
    }
    if (portable_picture_modal_deadline_reached(1000, 1269) ||
        !portable_picture_modal_deadline_reached(1000, 1270) ||
        !portable_picture_modal_deadline_reached(UINT32_C(0xfffffff0),
                                                  UINT32_C(0xfffffff1)) ||
        !portable_picture_modal_deadline_reached(UINT32_C(0xffffff00),
                                                  UINT32_C(0xffffff01))) {
        fprintf(stderr, "source deadline boundary or wrap predicate failed\n");
        return 1;
    }
    /* Shared and HCEGANT are separate databases with the same asset root. */
    {
        char shared_path[1024], window_path[1024];
        if (snprintf(shared_path, sizeof(shared_path), "%s/SHARED", argv[1]) >= (int)sizeof(shared_path) ||
            snprintf(window_path, sizeof(window_path), "%s/HCEGANT", argv[1]) >= (int)sizeof(window_path) ||
            portable_db_open(&shared, shared_path) != PORTABLE_DB_OK ||
            portable_db_open(&windows, window_path) != PORTABLE_DB_OK ||
            portable_db_load(&windows, 0x81, 0, &colors) != PORTABLE_DB_OK ||
            portable_db_load(&windows, 1, 15, &palette_record) != PORTABLE_DB_OK) {
            fprintf(stderr, "database setup failed: shared=%s windows=%s\n",
                    portable_db_error(&shared), portable_db_error(&windows));
            goto done;
        }
    }
    portable_fonts_init(&fonts);
    portable_bios_fonts_init(&bios);
    if (portable_fonts_load(&fonts, argv[1]) != PORTABLE_RENDER_OK ||
        portable_palette_load_ega(&palette, palette_record.data, palette_record.size) != PORTABLE_RENDER_OK) {
        fprintf(stderr, "font/palette setup failed: %s\n", fonts.error);
        goto cleanup_resources;
    }
    pixels = (uint8_t *)malloc(pixel_bytes);
    before = (uint8_t *)malloc(pixel_bytes);
    if (pixels == NULL || before == NULL) { fprintf(stderr, "frame allocation failed\n"); goto cleanup_resources; }
    for (i = 0; i < pixel_bytes; ++i)
        pixels[i] = (uint8_t)((i * 13u + i / HOST_LOGICAL_WIDTH) & 15u);
    memcpy(before, pixels, pixel_bytes);
    if (portable_framebuffer_init(&framebuffer, HOST_LOGICAL_WIDTH,
                                  HOST_LOGICAL_HEIGHT, HOST_LOGICAL_WIDTH,
                                  pixels) != PORTABLE_RENDER_OK)
        goto cleanup_resources;
    renderer.framebuffer = &framebuffer;
    renderer.database = &windows;
    renderer.colors = colors.data;
    renderer.colors_size = colors.size;
    renderer.screen_width = HOST_LOGICAL_WIDTH;
    for (i = 0; i < 4; ++i)
        renderer.fonts[i] = portable_fonts_get(&fonts, (unsigned)i + 2);
    if (portable_bios_fonts_load(&bios, NULL) == PORTABLE_BIOS_FONTS_OK)
        renderer.bios_fonts = &bios.provider;
    if (renderer.bios_fonts != NULL)
        snprintf(bios_provider_id, sizeof(bios_provider_id), "%s",
                 renderer.bios_fonts->font_8x14.provider_id);
    portable_picture_dialog_init(&dialog);
    {
        PortablePictureDialogStatus prep = portable_picture_dialog_prepare(
            &dialog, &shared, &windows, &fonts, inspect_request);
        if (prep != PORTABLE_PICTURE_DIALOG_OK) {
            fprintf(stderr, "dialog prepare failed: %s\n",
                    portable_picture_dialog_status_string(prep));
            goto cleanup_resources;
        }
    }
    inside_then_key[0].x = (dialog.rect.left + dialog.rect.right) / 2;
    inside_then_key[0].y = (dialog.rect.top + dialog.rect.bottom) / 2;
    source_window_flags = dialog.window.flags;
    host = host_create("SimAnt picture dialog integration", 1);
    if (host == NULL) { fprintf(stderr, "host_create: %s\n", host_error()); goto cleanup_resources; }
    memcpy(host_palette.rgb, palette.rgb, sizeof(host_palette.rgb));
    if (!host_present(host, pixels, HOST_LOGICAL_WIDTH, &host_palette)) goto cleanup_resources;
    if (!run_case(host, &palette, &fonts, &renderer, &shared, &windows,
                  before, pixel_bytes, inside_then_key, 2, &clock,
                  PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY, 0)) goto cleanup_resources;
    click_status = (dialog.window.flags & PORTABLE_WINDOW_CLOSE_ON_SWITCH)
        ? PORTABLE_PICTURE_MODAL_DISMISSED_BY_WINDOW_CLICK
        : PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY;
    outside_event_count = (dialog.window.flags & PORTABLE_WINDOW_CLOSE_ON_SWITCH) ? 1 : 2;
    if (!run_case(host, &palette, &fonts, &renderer, &shared, &windows,
                  before, pixel_bytes, outside_then_key, outside_event_count,
                  &clock,
                  click_status, 0))
        goto cleanup_resources;
    if (!run_case(host, &palette, &fonts, &renderer, &shared, &windows,
                  before, pixel_bytes, quit_event, 1, &clock,
                  PORTABLE_PICTURE_MODAL_QUIT_REJECTED, 1)) goto cleanup_resources;
    clock.tick = 1000;
    if (!run_case(host, &palette, &fonts, &renderer, &shared, &windows,
                  before, pixel_bytes, timeout_events, 3, &clock,
                  PORTABLE_PICTURE_MODAL_DISMISSED_BY_SOURCE_TIMEOUT, 0))
        goto cleanup_resources;
    okay = 1;
cleanup_resources:
    if (host != NULL) host_destroy(host);
    portable_picture_dialog_release(&dialog);
    portable_bios_fonts_free(&bios);
    portable_fonts_destroy(&fonts);
    free(before);
    free(pixels);
done:
    portable_db_record_free(&colors);
    portable_db_record_free(&palette_record);
    portable_db_close(&windows);
    portable_db_close(&shared);
    if (!okay) return 1;
    printf("SDL3 picture modal passed; source_window_flags=0x%04x; BIOS-reference=%s\n",
           source_window_flags, bios_provider_id);
    return 0;
}
