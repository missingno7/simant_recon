#include "../../platform/sdl3/scenario_modal.h"
#include "../../game/resources/bios_fonts.h"
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct TestClock { uint32_t tick; } TestClock;
typedef struct InjectEvent {
    int kind, x, y;
    uint32_t delay_ms;
    volatile int fired;
} InjectEvent;

enum { INJECT_CLICK, INJECT_ESCAPE, INJECT_CONTROL, INJECT_QUIT };

static uint32_t read_clock(void *context)
{
    TestClock *clock = (TestClock *)context;
    return clock->tick++;
}

static Uint32 inject_later(void *context, Uint32 interval, Uint32 missed)
{
    InjectEvent *inject = (InjectEvent *)context;
    SDL_Event event;
    (void)interval;
    (void)missed;
    memset(&event, 0, sizeof(event));
    if (inject->kind == INJECT_CLICK) {
        event.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
        event.button.button = SDL_BUTTON_LEFT;
        event.button.x = (float)inject->x;
        event.button.y = (float)inject->y;
    } else if (inject->kind == INJECT_QUIT) {
        event.type = SDL_EVENT_QUIT;
    } else {
        event.type = SDL_EVENT_KEY_DOWN;
        event.key.key = inject->kind == INJECT_ESCAPE ? SDLK_ESCAPE : SDLK_LCTRL;
    }
    inject->fired = SDL_PushEvent(&event) != 0;
    return 0;
}

static int schedule(InjectEvent *event)
{
    return SDL_AddTimer(event->delay_ms, inject_later, event) != 0;
}

static int run_modal(Host *host, PortableScenarioModalRequest *request,
                     uint8_t *before, size_t size, InjectEvent **injects,
                     size_t inject_count,
                     uint16_t expected, PortableScenarioModalStatus expected_status,
                     int expected_quit)
{
    uint16_t result = 0xaaaa;
    volatile int quit_flag = 0;
    HostEvent discarded;
    PortableScenarioModalStatus status;
    while (host_poll_event(host, &discarded) > 0) {}
    request->quit_flag = &quit_flag;
    size_t i;
    for (i = 0; i < inject_count; ++i)
        if (!schedule(injects[i])) {
            fprintf(stderr, "SDL_AddTimer failed: %s\n", SDL_GetError());
            return 0;
        }
    status = portable_scenario_modal_run(host, request, &result);
    for (i = 0; i < inject_count; ++i)
        if (!injects[i]->fired) {
            fprintf(stderr, "scheduled SDL event %zu did not fire\n", i);
            return 0;
        }
    if (status != expected_status ||
        ((status == PORTABLE_SCENARIO_MODAL_SELECTED ||
          status == PORTABLE_SCENARIO_MODAL_CANCELLED)
             ? result != expected : result != 0xaaaa) ||
        (!!quit_flag) != (!!expected_quit) ||
        memcmp(request->renderer->framebuffer->pixels, before, size) != 0) {
        fprintf(stderr, "scenario modal status=%s result=%04x quit=%d fired=%d restored=%d\n",
                portable_scenario_modal_status_string(status), result, quit_flag,
                injects[0]->fired,
                memcmp(request->renderer->framebuffer->pixels, before, size) == 0);
        return 0;
    }
    return 1;
}

int main(int argc, char **argv)
{
    PortableDatabase windows = {0};
    PortableDbRecord colors = {0}, palette_record = {0};
    PortableWindowRegistry registry = {0};
    PortableWindowOpenScene scene = {0};
    PortableWindowRenderer renderer = {0};
    PortablePalette palette;
    PortableFontSet fonts;
    PortableBiosFonts bios;
    PortableFramebuffer framebuffer;
    PortableScenarioModalRequest request = {0};
    PortableWindowRegistrySlot *slot;
    HostPalette hp;
    Host *host = NULL;
    uint8_t *pixels = NULL, *before = NULL;
    size_t byte_count = (size_t)HOST_LOGICAL_WIDTH * HOST_LOGICAL_HEIGHT, i;
    int16_t no_windows[1];
    TestClock clock = {1000};
    InjectEvent click = {INJECT_CLICK, 0, 0, 100, 0};
    InjectEvent ctrl = {INJECT_CONTROL, 0, 0, 60, 0};
    InjectEvent escape = {INJECT_ESCAPE, 0, 0, 160, 0};
    InjectEvent quit = {INJECT_QUIT, 0, 0, 100, 0};
    InjectEvent *one_click[] = {&click};
    InjectEvent *modifier_then_escape[] = {&ctrl, &escape};
    InjectEvent *quit_event[] = {&quit};
    int okay = 0;
    if (argc != 2) {
        fprintf(stderr, "usage: scenario-modal-host-test asset-directory\n");
        return 2;
    }
    {
        char root[1024];
        if (snprintf(root, sizeof(root), "%s/HCEGANT", argv[1]) >= (int)sizeof(root) ||
            portable_db_open(&windows, root) != PORTABLE_DB_OK ||
            portable_db_load(&windows, 0x81, 0, &colors) != PORTABLE_DB_OK ||
            portable_db_load(&windows, 1, 15, &palette_record) != PORTABLE_DB_OK)
            goto done;
    }
    if (portable_window_registry_init(&registry, &windows, 0) !=
        PORTABLE_WINDOW_REGISTRY_OK ||
        portable_window_registry_load(&registry, 2) != PORTABLE_WINDOW_REGISTRY_OK)
        goto done;
    slot = &registry.slots[2];
    if (portable_window_registry_recalculate(&registry, 2,
                                              NULL) !=
        PORTABLE_WINDOW_REGISTRY_OK || slot->window.count <= 2 ||
        !(slot->window.objects[2].flags & PORTABLE_WINDOW_OBJECT_SELECTABLE)) {
        fprintf(stderr, "actual scenario resource object 2 is not a selectable hit\n");
        goto cleanup;
    }
    if (portable_window_open_scene_init(&registry, no_windows, 0, &scene) !=
        PORTABLE_WINDOW_OPEN_OK)
        goto cleanup;
    portable_fonts_init(&fonts);
    portable_bios_fonts_init(&bios);
    if (portable_fonts_load(&fonts, argv[1]) != PORTABLE_RENDER_OK ||
        portable_palette_load_ega(&palette, palette_record.data,
                                  palette_record.size) != PORTABLE_RENDER_OK)
        goto cleanup_fonts;
    pixels = (uint8_t *)malloc(byte_count);
    before = (uint8_t *)malloc(byte_count);
    if (pixels == NULL || before == NULL) goto cleanup_fonts;
    for (i = 0; i < byte_count; ++i)
        pixels[i] = (uint8_t)((i * 7u + i / HOST_LOGICAL_WIDTH) & 15u);
    memcpy(before, pixels, byte_count);
    if (portable_framebuffer_init(&framebuffer, HOST_LOGICAL_WIDTH,
                                  HOST_LOGICAL_HEIGHT, HOST_LOGICAL_WIDTH,
                                  pixels) != PORTABLE_RENDER_OK)
        goto cleanup_fonts;
    renderer.framebuffer = &framebuffer;
    renderer.database = &windows;
    renderer.colors = colors.data;
    renderer.colors_size = colors.size;
    renderer.screen_width = HOST_LOGICAL_WIDTH;
    for (i = 0; i < 4; ++i)
        renderer.fonts[i] = portable_fonts_get(&fonts, (unsigned)i + 2u);
    if (portable_bios_fonts_load(&bios, NULL) == PORTABLE_BIOS_FONTS_OK)
        renderer.bios_fonts = &bios.provider;
    host = host_create("SimAnt scenario modal integration", 1);
    if (host == NULL) goto cleanup_fonts;
    memcpy(hp.rgb, palette.rgb, sizeof(hp.rgb));
    if (!host_present(host, pixels, HOST_LOGICAL_WIDTH, &hp)) goto cleanup_fonts;
    request.registry = &registry;
    request.open_scene = &scene;
    request.palette = &palette;
    request.fonts = &fonts;
    request.renderer = &renderer;
    request.screen_width = HOST_LOGICAL_WIDTH;
    request.screen_height = HOST_LOGICAL_HEIGHT;
    /* S20's 8x14 menu layout is 17 logical pixels high. */
    request.menu_rect = (PortableWindowRect){0, 0, HOST_LOGICAL_WIDTH, 17};
    request.tick_count = read_clock;
    request.clock_context = &clock;
    click.x = (slot->window.objects[2].rect.left +
               slot->window.objects[2].rect.right) / 2;
    click.y = (slot->window.objects[2].rect.top +
               slot->window.objects[2].rect.bottom) / 2;
    if (!run_modal(host, &request, before, byte_count, one_click, 1, 0x0202,
                   PORTABLE_SCENARIO_MODAL_SELECTED, 0) ||
        scene.open_count != 0 ||
        (scene.windows[2].flags & PORTABLE_WINDOW_OPEN) != 0)
        goto cleanup_fonts;
    if (!run_modal(host, &request, before, byte_count, modifier_then_escape, 2,
                   PORTABLE_SCENARIO_CANCEL_CODE,
                   PORTABLE_SCENARIO_MODAL_CANCELLED, 0)) {
        goto cleanup_fonts;
    }
    if (!run_modal(host, &request, before, byte_count, quit_event, 1, 0xaaaa,
                   PORTABLE_SCENARIO_MODAL_QUIT_REJECTED, 1) ||
        scene.open_count != 0 ||
        (scene.windows[2].flags & PORTABLE_WINDOW_OPEN) != 0)
        goto cleanup_fonts;
    okay = 1;
cleanup_fonts:
    if (host != NULL) host_destroy(host);
    portable_bios_fonts_free(&bios);
    portable_fonts_destroy(&fonts);
    free(before);
    free(pixels);
cleanup:
    portable_window_registry_destroy(&registry);
done:
    portable_db_record_free(&colors);
    portable_db_record_free(&palette_record);
    portable_db_close(&windows);
    if (!okay) return 1;
    printf("SDL3 scenario modal passed; click=0x0202; physical Escape cancels\n");
    return 0;
}
