/* Native lifecycle only. Startup, dialogs and simulation remain in dos_game_main. */
#include "platform/graphics.h"
#include "platform/graphics_entry_source.h"
#include "platform/graphics_capture_source.h"
#include "platform/graphics_misc_source.h"
#include "platform/graphics_tile_upload.h"
#include "platform/m1b73_mouse.h"
#include "platform/ega_map_readback.h"
#include "platform/native_video_profile.h"
#include "platform/handles.h"
#include "platform/dos_io.h"
#include "platform/seed_source.h"
#include "platform/sdl3/m1b73_application_input.h"
#include "platform/sdl3/host_modes.h"
#include "platform/sdl3/diagnostics.h"
#include "platform/sdl3/native_windows.h"
#include "platform/sdl3/native_menu.h"
#include "platform/window_hosting.h"
#include "portable/whole_program/platform/graphics_resources.h"
#include "portable/platform/sdl3/whole_audio_provider.h"
#include "portable/platform/sdl3/whole_audio_startup.h"
#include "platform/audio_native.h"
#include "state/main_loop_counter.h"
#include "text_bitmap_bridge.h"
#include "window_source_globals.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <SDL3/SDL.h>

extern void dos_game_main(int16_t argc, char **argv);

typedef struct ReplayKey {
    uint64_t milliseconds;
    SDL_Keycode key;
    int down;
    HostEvent pointer;
    int checkpoint, quit;
    int close, resize_w, resize_h; /* close@ID, resize@ID W H */
    int native_w, native_h;        /* size@ID W H: the native client, as the user sizes it */
    int wheel_x, wheel_y, wheel;   /* wheel@ID X Y STEPS */
    int menu;                      /* menu FDxx: a native menu choice */
    int relative, current_pointer;
    int16_t window; /* op@ID: window-local input to a hosted window */
    int targeted;
} ReplayKey;

typedef struct Application {
    Host *host;
    SimGraphicsDriver graphics;
    SimSdlPaletteHost palette;
    PortableSourceGraphicsResources resources;
    PortableM1B73SdlApplicationInput input;
    SimTimingClock game_clock, bios_clock;
    PortableSdl3WholeAudio audio;
    uint32_t seed;
    uint64_t last_present;
    uint64_t started_ns, smoke_deadline_ns;
    char capture_path[MAX_PATH];
    int display_active;
    int cleaned;
    ReplayKey *replay;
    size_t replay_count, replay_next, replay_capacity;
    SDL_Keymod replay_modifiers;
    int test_input;
} Application;
static Application app;
static int exit_status;
static const char *exit_reason = "source main returned";
extern void __real_exit(int status) __attribute__((noreturn));
/* Observe all CRT exit calls, including canonical Punt paths, before atexit.
 * Linker wrapping changes no game decision or status. */
void __wrap_exit(int status)
{
    exit_status = status;
    if (!strcmp(exit_reason, "source main returned")) exit_reason = "source/platform exit";
    __real_exit(status);
}
static void close_diagnostics(void) { simant_diagnostics_close(exit_status, exit_reason); }
static void idle(void *context);
static void request_quit(void *context);
static void fail(const char *where);

static void drain_host_observations(void)
{
    HostEvent event;
    int had_event;
    do {
        if (portable_m1b73_sdl_application_input_service_one(&app.input,
                &event, &had_event) != PORTABLE_M1B73_APP_INPUT_OK)
            fail("retained input queue");
    } while (had_event);
}

/* Read-only debugger observation boundary. Break here to dump canonical
 * symbols and SaveRec payloads; no simulation callback/state writes. */
__attribute__((noinline)) void portable_native_checkpoint(uint64_t milliseconds)
{
    fprintf(stderr, "Native checkpoint %llu ms game_ticks=%u bios_ticks=%u outer_loops=%ld\n",
        (unsigned long long)milliseconds, sim_timing_tick_count(&app.game_clock),
        sim_timing_tick_count(&app.bios_clock), (long)fd_50F6_383A);
}

static void fail(const char *where)
{
    exit_reason = where;
    fprintf(stderr, "SimAnt native boundary failed: %s\n", where);
    exit(70);
}
static void runtime_child(char *out, size_t capacity,
                          const char *directory, const char *child)
{
    size_t base = strlen(directory), tail = strlen(child);
    if (base + tail + 2 > capacity) fail("runtime directory path");
    memcpy(out, directory, base);
    out[base] = '\\';
    memcpy(out + base + 1, child, tail + 1);
}
static int directory_exists(const char *path)
{
    DWORD attributes = GetFileAttributesA(path);
    return attributes != INVALID_FILE_ATTRIBUTES &&
        (attributes & FILE_ATTRIBUTE_DIRECTORY) != 0;
}
/* Test input enters the same SDL event boundary as physical keyboard input.
 * This never calls a game function or writes source game state. */
static void load_replay(const char *path)
{
    FILE *file = fopen(path, "r");
    char line[192], operation[16], key_name[64], extra;
    int x, y;
    unsigned long long milliseconds;
    size_t number = 0;
    if (!file) fail("input replay file");
    while (fgets(line, sizeof(line), file)) {
        ReplayKey *entry;
        ++number;
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        if (sscanf(line, "%llu %15s", &milliseconds, operation) != 2) {
            fprintf(stderr, "Invalid keyboard replay line %zu\n", number);
            fail("keyboard replay syntax");
        }
        if (app.replay_count == app.replay_capacity) {
            size_t capacity = app.replay_capacity ? app.replay_capacity * 2 : 512;
            ReplayKey *grown;
            if (capacity < app.replay_capacity || capacity > SIZE_MAX / sizeof(*grown)) fail("replay size");
            grown = realloc(app.replay, capacity * sizeof(*grown));
            if (!grown) fail("replay storage");
            app.replay = grown;
            app.replay_capacity = capacity;
        }
        entry = &app.replay[app.replay_count];
        memset(entry, 0, sizeof(*entry));
        entry->milliseconds = milliseconds;
        if (strchr(operation, '@')) {
            /* op@ID: blank the suffix in the line so every parser below sees op. */
            char *at = strchr(line, '@'), *end;
            unsigned long id = strtoul(at + 1, &end, 16);
            if (end == at + 1 || id > 0xffffu || (*end && !strchr(" \t\r\n", *end)))
                fail("replay window target");
            entry->window = (int16_t)(uint16_t)id;
            entry->targeted = 1;
            memset(at, ' ', (size_t)(end - at));
            *strchr(operation, '@') = 0;
        }
        if (!strcmp(operation, "down") || !strcmp(operation, "up")) {
            size_t length;
            if (sscanf(line, "%llu %15s %63[^\r\n]", &milliseconds, operation,
                       key_name) != 3) fail("keyboard replay syntax");
            length = strlen(key_name);
            while (length && key_name[length - 1] == ' ') key_name[--length] = 0;
            entry->down = !strcmp(operation, "down");
            entry->key = SDL_GetKeyFromName(key_name);
            if (!entry->key) fail("keyboard replay key");
        } else if (!strcmp(operation, "move") || !strcmp(operation, "relative")) {
            if (sscanf(line, "%llu %15s %d %d %c", &milliseconds, operation,
                       &x, &y, &extra) != 4) fail("pointer replay syntax");
            entry->pointer.kind = HOST_EVENT_MOUSE_MOVE;
            entry->relative = !strcmp(operation, "relative");
        } else if (!strcmp(operation, "button-down") || !strcmp(operation, "button-up")) {
            if (sscanf(line, "%llu %15s %63s %c", &milliseconds, operation,
                       key_name, &extra) != 3) fail("pointer replay syntax");
            entry->pointer.kind = !strcmp(operation, "button-down") ?
                                  HOST_EVENT_MOUSE_DOWN : HOST_EVENT_MOUSE_UP;
            entry->pointer.button = !strcmp(key_name, "Left") ? SDL_BUTTON_LEFT :
                !strcmp(key_name, "Right") ? SDL_BUTTON_RIGHT :
                !strcmp(key_name, "Middle") ? SDL_BUTTON_MIDDLE : 0;
            if (!entry->pointer.button) fail("pointer replay button");
            entry->current_pointer = 1;
            x = y = 0;
        } else if (!strcmp(operation, "mouse-down") || !strcmp(operation, "mouse-up")) {
            if (sscanf(line, "%llu %15s %63s %d %d %c", &milliseconds, operation,
                       key_name, &x, &y, &extra) != 5) fail("pointer replay syntax");
            entry->pointer.kind = !strcmp(operation, "mouse-down") ?
                                  HOST_EVENT_MOUSE_DOWN : HOST_EVENT_MOUSE_UP;
            entry->pointer.button = !strcmp(key_name, "Left") ? SDL_BUTTON_LEFT :
                !strcmp(key_name, "Right") ? SDL_BUTTON_RIGHT :
                !strcmp(key_name, "Middle") ? SDL_BUTTON_MIDDLE : 0;
            if (!entry->pointer.button) fail("pointer replay button");
        } else if (!strcmp(operation, "menu")) {
            if (sscanf(line, "%llu %15s %x %c", &milliseconds, operation, &entry->menu, &extra) != 3 ||
                (entry->menu & 0xff00) != 0xfd00) fail("menu replay syntax");
        } else if (!strcmp(operation, "close") && entry->targeted) entry->close = 1;
        else if (!strcmp(operation, "resize") && entry->targeted) {
            if (sscanf(line, "%llu %15s %d %d %c", &milliseconds, operation,
                       &entry->resize_w, &entry->resize_h, &extra) != 4) fail("resize replay syntax");
        } else if (!strcmp(operation, "size") && entry->targeted) {
            if (sscanf(line, "%llu %15s %d %d %c", &milliseconds, operation,
                       &entry->native_w, &entry->native_h, &extra) != 4 ||
                entry->native_w <= 0 || entry->native_h <= 0) fail("size replay syntax");
        } else if (!strcmp(operation, "wheel") && entry->targeted) {
            if (sscanf(line, "%llu %15s %d %d %d %c", &milliseconds, operation, &entry->wheel_x,
                       &entry->wheel_y, &entry->wheel, &extra) != 5 || !entry->wheel)
                fail("wheel replay syntax");
        } else if (!strcmp(operation, "checkpoint")) entry->checkpoint = 1;
        else if (!strcmp(operation, "exit")) entry->quit = 1;
        else fail("input replay operation");
        if (entry->pointer.kind) {
            if (x < INT16_MIN || x > INT16_MAX || y < INT16_MIN || y > INT16_MAX)
                fail("pointer replay coordinate range");
            entry->pointer.x = (int16_t)x;
            entry->pointer.y = (int16_t)y;
        }
        if (app.replay_count && milliseconds < app.replay[app.replay_count - 1].milliseconds)
            fail("input replay event order");
        ++app.replay_count;
    }
    if (ferror(file)) fail("keyboard replay read");
    fclose(file);
}
static void replay_input(uint64_t now)
{
    simant_diagnostics_progress("replay_input", app.replay_next, (long)fd_50F6_383A);
    uint64_t elapsed = (now - app.started_ns) / 1000000u;
    while (app.replay_next < app.replay_count &&
            app.replay[app.replay_next].milliseconds <= elapsed) {
        ReplayKey *entry = &app.replay[app.replay_next];
        SDL_Event event = {0};
        /* Preserve script order for equal-time input/checkpoint commands.
         * Ingestion is reentrancy-guarded and consumes no additional time. */
        if (host_virtual_clock_enabled()) drain_host_observations();
        if (entry->checkpoint) {
            portable_native_checkpoint(entry->milliseconds);
            ++app.replay_next;
            continue;
        }
        if (entry->quit) { exit_reason = "input replay exit"; exit(0); }
        if (entry->menu) {
            if (!native_menu_command(entry->menu)) fail("replay menu command");
            fprintf(stderr, "Replay menu command %zu: %llu ms %04X\n", app.replay_next,
                    (unsigned long long)entry->milliseconds, (unsigned)entry->menu);
            ++app.replay_next;
            continue;
        }
        if (entry->close || entry->resize_w) {
            if (entry->close ? !native_windows_request_close(entry->window) :
                !native_windows_request_resize(entry->window, entry->resize_w, entry->resize_h))
                fail("replay window request");
            fprintf(stderr, "Replay window request %zu: %llu ms %s %04X\n", app.replay_next,
                    (unsigned long long)entry->milliseconds, entry->close ? "close" : "resize",
                    (unsigned)(uint16_t)entry->window);
            ++app.replay_next;
            continue;
        }
        if (entry->native_w || entry->wheel) {
            if (entry->native_w ? !native_windows_push_native_size(entry->window, entry->native_w, entry->native_h) :
                !native_windows_push_wheel(entry->window, entry->wheel_x, entry->wheel_y, (float)entry->wheel))
                fail("replay window input");
            fprintf(stderr, "Replay window request %zu: %llu ms %s %04X\n", app.replay_next,
                    (unsigned long long)entry->milliseconds, entry->native_w ? "size" : "wheel",
                    (unsigned)(uint16_t)entry->window);
            ++app.replay_next;
            continue;
        }
        if (entry->pointer.kind) {
            if (entry->relative || entry->current_pointer) {
                HostInputState state;
                int px, py;
                if (!host_get_input_state(app.host, &state)) fail("replay pointer state");
                /* Source S17 sets both INT33 mickey ratios to 16. The pinned
                 * DOSBox hook bypasses sensitivity: 8/16 pixels per mickey. */
                px = state.x + (entry->relative ? entry->pointer.x / 2 : 0);
                py = state.y + (entry->relative ? entry->pointer.y / 2 : 0);
                if (px < 0) px = 0;
                if (py < 0) py = 0;
                if (px > g_3DB2 - 4) px = g_3DB2 - 4;
                if (py > g_3DB4 - 4) py = g_3DB4 - 4;
                entry->pointer.x = (int16_t)px;
                entry->pointer.y = (int16_t)py;
            }
            if (entry->targeted ? !native_windows_push_pointer(entry->window, &entry->pointer) :
                                !host_push_pointer_event(app.host, &entry->pointer))
                fail("SDL pointer replay enqueue");
            fprintf(stderr, "Replay SDL pointer %zu: %llu ms kind=%d button=%u (%d,%d)\n",
                app.replay_next, (unsigned long long)entry->milliseconds,
                (int)entry->pointer.kind, (unsigned)entry->pointer.button,
                (int)entry->pointer.x, (int)entry->pointer.y);
            ++app.replay_next;
            continue;
        }
        event.type = entry->down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
        event.key.key = entry->key;
        event.key.scancode = SDL_GetScancodeFromKey(entry->key, &event.key.mod);
        {
            SDL_Keymod modifier = entry->key == SDLK_LSHIFT ? SDL_KMOD_LSHIFT :
                entry->key == SDLK_RSHIFT ? SDL_KMOD_RSHIFT : entry->key == SDLK_LCTRL ? SDL_KMOD_LCTRL :
                entry->key == SDLK_RCTRL ? SDL_KMOD_RCTRL : entry->key == SDLK_LALT ? SDL_KMOD_LALT :
                entry->key == SDLK_RALT ? SDL_KMOD_RALT : SDL_KMOD_NONE;
            if (entry->down) app.replay_modifiers |= modifier;
            else app.replay_modifiers &= ~modifier;
            if (entry->down && entry->key == SDLK_CAPSLOCK) app.replay_modifiers ^= SDL_KMOD_CAPS;
            event.key.mod |= app.replay_modifiers;
        }
        event.key.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        event.key.down = entry->down != 0;
        if (!event.key.scancode || !SDL_PushEvent(&event))
            fail("SDL keyboard replay enqueue");
        fprintf(stderr, "Replay SDL key %zu: %llu ms %s %s\n",
            app.replay_next, (unsigned long long)entry->milliseconds,
            entry->down ? "down" : "up", SDL_GetKeyName(entry->key));
        ++app.replay_next;
    }
}
static int read_seed(void *context, uint32_t *value)
{
    *value = ((Application *)context)->seed;
    return 1;
}
static int resolve_handle(void *context, const void *handle,
                          const uint8_t **bytes, size_t *size)
{
    (void)context;
    return sim_handles_global_resolve_payload(handle, bytes, size);
}
static int measure_resource(void *context, const uint8_t *bytes, size_t *size)
{
    (void)context;
    return sim_handles_global_measure_payload(bytes, size);
}
static int read_plane(void *context, uint8_t plane, uint16_t offset,
                      uint8_t output[128])
{
    (void)context;
    return sim_graphics_tile_upload_read_plane(plane, offset, output, 128) ==
        SIM_GRAPHICS_TILE_UPLOAD_OK;
}
static SimGraphicsStatus change_dimensions(void *context, int32_t width,
                                           int32_t height)
{
    Application *a = context;
    return host_set_logical_size(a->host, width, height) ? SIM_GRAPHICS_OK :
        SIM_GRAPHICS_INVALID_ARGUMENT;
}
static void retire_display(void *context)
{
    ((Application *)context)->display_active = 0;
}
/* The source exports abort on a failed mouse service. Returning success here
 * therefore requires the original transition to have completed. */
static int hide_cursor(void *context)
{
    (void)context;
    f_1B73_0196();
    return 1;
}
static int update_cursor(void *context)
{
    (void)context;
    f_1B73_00D9();
    return 1;
}
static int redraw_cursor(void *context)
{
    (void)context;
    f_1B73_04BB();
    return 1;
}
static void uninstall_video(void *context)
{
    Application *a = context;
    a->display_active = 0;
    portable_text_bitmap_unbind_source();
    portable_ega_map_readback_unbind();
    sim_graphics_tile_upload_unbind();
    sim_graphics_cursor_hooks_unbind();
    sim_graphics_source_misc_unbind();
    sim_graphics_source_capture_unbind();
    sim_graphics_source_entry_unbind();
    sim_graphics_source_palette_unbind();
}
static int install_video(void *context, SimGraphicsDriver *graphics,
                         SimNativeVideoProfile profile)
{
    Application *a = context;
    const SimGraphicsCursorHooks cursor_hooks = {
        a, hide_cursor, update_cursor, redraw_cursor
    };
    SimGraphicsCursorSourceBindings cursor = {0};
    PortableM1B73ApplicationInputStatus input_status;
    if (graphics != &a->graphics ||
        !sim_sdl_palette_init(&a->palette, profile) ||
        sim_graphics_cursor_hooks_bind(&cursor_hooks) != SIM_GRAPHICS_CURSOR_HOOKS_OK ||
        sim_graphics_source_entry_bind(graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_source_capture_bind(graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_source_misc_bind(graphics, retire_display, a) != SIM_GRAPHICS_OK ||
        portable_text_bitmap_bind_source((uint8_t)g_5A97, NULL, 0) !=
            PORTABLE_TEXT_BITMAP_OK ||
        sim_graphics_tile_upload_bind(graphics) != SIM_GRAPHICS_TILE_UPLOAD_OK ||
        !portable_ega_map_readback_bind(read_plane, a) ||
        !sim_sdl_palette_bind(&a->palette)) {
        uninstall_video(a);
        return 0;
    }
    fprintf(stderr,
        "Source-selected video profile=%d mode=%02Xh logical=%dx%d\n",
        (int)profile, (unsigned)graphics->video_mode,
        graphics->framebuffer.width, graphics->framebuffer.height);
    /* Cursor binding requires the callbacks selected by original IBMInitStuff.
     * Bind at that source mode boundary, before it initializes the mouse. */
    if (!a->input.bound) {
        cursor.resolve_handle = resolve_handle;
        cursor.measure_active_resource = measure_resource;
        input_status = portable_m1b73_sdl_application_input_bind(&a->input, a->host,
            graphics, &a->palette, &a->game_clock, &a->bios_clock, &cursor);
        if (input_status != PORTABLE_M1B73_APP_INPUT_OK) {
            fprintf(stderr, "Source input binding status=%d\n", (int)input_status);
            fail("source input binding");
        }
        portable_m1b73_sdl_application_input_set_idle_hook(&a->input, idle, a);
        portable_input_time_host_set_interrupt_guard(&a->input.input_host,
            portable_whole_audio_interrupts_enabled);
        portable_m1b73_sdl_application_input_set_quit_hook(&a->input, request_quit, a);
    }
    a->display_active = 1;
    return 1;
}
static void cleanup(void)
{
    if (app.cleaned) return;
    app.cleaned = 1;
    host_set_event_observer(NULL, NULL);
    free(app.replay);
    portable_m1b73_sdl_application_input_unbind(&app.input);
    if (portable_whole_audio_timer_armed()) f_28BC_04E0(0);
    portable_sdl3_whole_audio_unbind_source_services();
    portable_sdl3_whole_audio_close(&app.audio);
    sim_native_video_startup_unbind();
    portable_source_graphics_resources_destroy(&app.resources);
    sim_graphics_destroy(&app.graphics);
    dos_files_close_all();
    portable_seed_source_unbind();
    host_destroy(app.host);
    app.host = NULL;
}
static void request_quit(void *context)
{
    (void)context;
    exit_reason = "window closed";
    exit(0); /* Native window close; atexit releases borrowed bindings first. */
}
static void source_timer_changed(void *context, uint16_t divisor, uint16_t reload)
{
    Application *a = context;
    uint32_t pit_divisor = divisor ? divisor : 65536u;
    uint32_t chain = reload ? reload : 1u;
    if (a->cleaned) return;
    /* Account for elapsed time under the old source rate before changing it.
     * Both counters retain their values and the private enable flag. */
    if (!portable_input_time_host_refresh_from_sdl_monotonic(
            &a->input.input_host.monotonic_refresh, &a->game_clock) ||
        sim_timing_clock_configure_rate(&a->game_clock, 14318180, 12,
            pit_divisor, chain) != SIM_TIMING_OK ||
        sim_timing_clock_configure_rate(&a->bios_clock, 14318180, 12,
            pit_divisor, chain) != SIM_TIMING_OK) fail("source PIT rate transition");
    /* f_28BC_03CC arms g_74A3=1 before the first interrupt. The old INT08
     * chain runs after that one interrupt, then every g_74A5 interrupts. */
    if (divisor && reload) {
        a->game_clock.pit_fraction = (uint64_t)(reload - 1u) * divisor;
        a->bios_clock.pit_fraction = a->game_clock.pit_fraction;
    }
}
static void idle(void *context)
{
    Application *a = context;
    uint64_t now = host_time_ns();
    simant_diagnostics_progress("application.idle", a->replay_next, (long)fd_50F6_383A);
    if (a->test_input > 0 && a->last_present) {
        /* Hidden regression hook: untagged SDL input exercises the same
         * recording boundary as a keyboard/mouse, without OS focus races. */
        SDL_Event event = {0};
        int down, count = a->test_input == 2 ? 240 : 1, n;
        a->test_input = a->test_input == 2 ? -1 : 0;
        SDL_Log("SimAnt diagnostics SDL log regression");
        event.type = SDL_EVENT_MOUSE_MOTION;
        event.motion.which = SDL_TOUCH_MOUSEID; /* A real SDL mouse ID, not a replay tag. */
        event.motion.x = 120; event.motion.y = 140;
        for (n = 0; n < count; ++n) SDL_PushEvent(&event);
        for (down = 1; down >= 0; --down) {
            memset(&event, 0, sizeof(event));
            event.type = down ? SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
            event.button.button = SDL_BUTTON_RIGHT;
            event.button.x = 120; event.button.y = 140;
            event.button.down = down != 0;
            SDL_PushEvent(&event);
        }
        for (down = 1; down >= 0; --down) {
            memset(&event, 0, sizeof(event));
            event.type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
            event.key.key = SDLK_LSHIFT; event.key.scancode = SDL_SCANCODE_LSHIFT;
            event.key.mod = down ? SDL_KMOD_LSHIFT : SDL_KMOD_NONE;
            event.key.down = down != 0;
            SDL_PushEvent(&event);
        }
        for (down = 1; down >= 0; --down) {
            memset(&event, 0, sizeof(event));
            event.type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
            event.key.key = SDLK_F12; event.key.scancode = SDL_SCANCODE_F12;
            event.key.down = down != 0;
            SDL_PushEvent(&event);
        }
    }
    if (host_virtual_clock_enabled() && a->audio.active &&
        portable_sdl3_whole_audio_pump(&a->audio) != PORTABLE_SDL3_WHOLE_AUDIO_OK)
        fail("virtual PIT audio work");
    replay_input(now);
    /* Events were routed at ingestion. Release the retained host observations;
     * source BIOS keys and hotbox records have their own canonical queues. */
    drain_host_observations();
    simant_diagnostics_capture(a->host, (long)fd_50F6_383A);
    if (a->test_input == -1) simant_diagnostics_test_crash();
    if (!host_virtual_clock_enabled() && a->audio.active && portable_sdl3_whole_audio_pump(&a->audio) !=
            PORTABLE_SDL3_WHOLE_AUDIO_OK) fail("ISA audio output");
    /* Polling yields after a draw, including held-input tracking. g_5AAC is
     * the current clip list, which those loops retain until release; it is
     * not a frame-in-progress flag. Raster/cursor exclusion is g_3DD4. */
    /* DOS speed in held-edge scrolling and Fast/Ultra simulation is bounded
     * only by the machine: those source loops redraw without a timer wait.
     * The display shows one refresh of VGA memory at a time (mode 12h:
     * 25.175 MHz / (800 x 525) = 59.94 Hz), so a loop that has stored to VGA
     * since the last presented refresh waits for the next one here, at the
     * platform boundary, instead of producing invisible frames at host speed. */
    if (a->display_active && (g_3DD4 & 255u) == 0 && sim_sdl_palette_view(&a->palette)) {
        const uint64_t refresh_ns = 16683217;
        /* Wait in short slices: audio is rendered only up to host time, so
         * the device keeps the same feed cadence while the source waits. */
        while (a->graphics.vga.written && a->last_present && !host_virtual_clock_enabled() &&
               now - a->last_present < refresh_ns) {
            uint64_t remaining = refresh_ns - (now - a->last_present);
            SDL_DelayPrecise(remaining < 1000000u ? remaining : 1000000u);
            if (a->audio.active && portable_sdl3_whole_audio_pump(&a->audio) !=
                    PORTABLE_SDL3_WHOLE_AUDIO_OK) fail("ISA audio output");
            now = host_time_ns();
        }
        if (now - a->last_present >= refresh_ns) {
            if (portable_m1b73_sdl_application_input_present(&a->input) !=
                    PORTABLE_M1B73_APP_INPUT_OK) fail("indexed presentation");
            a->graphics.vga.written = 0;
            a->last_present = now;
        }
    }
    if (a->smoke_deadline_ns && now >= a->smoke_deadline_ns) {
        if (!a->last_present || !a->display_active)
            fail("smoke deadline reached before a source frame was presented");
        if (a->capture_path[0] && (!host_save_frame(a->host, a->capture_path) ||
                                   !native_windows_save_frames(a->capture_path)))
            fail("smoke frame capture");
        fprintf(stderr, "Source-main smoke frame captured; outer game loop count=%ld; full gameplay remains a separate check\n",
            (long)fd_50F6_383A);
        exit_reason = "smoke deadline";
        exit(0);
    }
}

int main(int argc, char **argv)
{
    char runtime_assets[MAX_PATH];
    char runtime_fonts[MAX_PATH];
    const char *assets = runtime_assets, *fonts = runtime_fonts;
    int source_argc = 1, i;
    int headless = 0;
    int explicit_seed = 0;
    char replay_path[MAX_PATH] = {0};
    uint64_t smoke_ms = 0;
    uint64_t virtual_quantum_ns = 0;
    char **source_argv;
    int debug = 0, test_crash = 0, test_abort = 0, smooth_zoom = 0;
    /* Modern presentation: these logical windows become native windows. */
    int16_t hosted_ids[SIM_HOSTING_SLOTS];
    unsigned hosted_count = 0;
    int window_scale = 2; /* --scale N: one scale for every window */
    const char *diagnostics_root = NULL;
    setvbuf(stderr, NULL, _IONBF, 0);
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    /* Establish crash capture before resource paths, SDL startup or game code. */
    for (i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--debug")) debug = 1;
        else if (!strncmp(argv[i], "--diagnostics-dir=", 18)) diagnostics_root = argv[i] + 18;
    }
    simant_diagnostics_init(debug, diagnostics_root);
    atexit(close_diagnostics);
    {
        /* This MinGW import library omits an export present in the loaded
         * Windows CRT. Resolve that same CRT's diagnostic policy directly. */
        HMODULE crt = GetModuleHandleA("msvcrt.dll");
        FARPROC procedure = crt ? GetProcAddress(crt, "_set_abort_behavior") : NULL;
        unsigned (__cdecl *set_abort_behavior)(unsigned, unsigned) = NULL;
        _Static_assert(sizeof(procedure) == sizeof(set_abort_behavior), "Windows function pointer ABI");
        if (procedure) {
            memcpy(&set_abort_behavior, &procedure, sizeof(set_abort_behavior));
            set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
        }
    }
    {
        char executable_directory[MAX_PATH], candidate[MAX_PATH];
        DWORD length = GetModuleFileNameA(NULL, runtime_assets, sizeof(runtime_assets));
        char *separator;
        if (!length || length >= sizeof(runtime_assets)) fail("executable asset path");
        separator = strrchr(runtime_assets, '\\');
        if (!separator) fail("runtime asset path");
        *separator = '\0';
        strcpy(executable_directory, runtime_assets);
        /* Build snapshots use isolated copies. A drop-in release instead
         * reads the original game files beside the native executable. */
        runtime_child(candidate, sizeof(candidate), executable_directory, "runtime-assets");
        if (directory_exists(candidate)) strcpy(runtime_assets, candidate);
        runtime_child(runtime_fonts, sizeof(runtime_fonts), executable_directory,
                      "simant-sdl3-fonts");
        if (!directory_exists(runtime_fonts))
            runtime_child(runtime_fonts, sizeof(runtime_fonts), executable_directory,
                          "runtime-bios-fonts");
    }
    app.seed = (uint32_t)host_time_ns();
    source_argv = calloc((size_t)argc + 4, sizeof(*source_argv));
    if (!source_argv) fail("argument storage");
    source_argv[0] = argv[0];
    for (i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--debug") || !strncmp(argv[i], "--diagnostics-dir=", 18)) continue;
        else if (!strcmp(argv[i], "--test-crash")) test_crash = 1;
        else if (!strcmp(argv[i], "--test-crash-thread")) test_crash = 2;
        else if (!strcmp(argv[i], "--test-abort")) test_abort = 1;
        else if (!strcmp(argv[i], "--test-input")) app.test_input = 1;
        else if (!strcmp(argv[i], "--test-input-crash")) app.test_input = 2;
        else if (!strcmp(argv[i], "--headless")) headless = 1;
        else if (!strncmp(argv[i], "--scale=", 8)) {
            window_scale = atoi(argv[i] + 8);
            if (window_scale < 1 || window_scale > 8) fail("--scale expects 1..8");
        }
        else if (!strncmp(argv[i], "--windows", 9) && (argv[i][9] == 0 || argv[i][9] == '=')) {
            /* --windows[=ID,ID...] (hex logical IDs). Default: every logical
             * window, dialogs included, is a native window as in Win16. */
            const char *list = argv[i][9] ? argv[i] + 10 : "";
            char *end;
            if (!*list)
                for (hosted_count = 0; hosted_count < SIM_HOSTING_SLOTS; ++hosted_count)
                    hosted_ids[hosted_count] = (int16_t)(hosted_count << 8);
            while (*list && hosted_count < SIM_HOSTING_SLOTS) {
                unsigned long id = strtoul(list, &end, 16);
                if (end == list || id > 0xffffu || (id & 0xffu) || (id >> 8) >= SIM_HOSTING_SLOTS)
                    fail("--windows expects hex logical window IDs such as 1200,1300");
                hosted_ids[hosted_count++] = (int16_t)(uint16_t)id;
                list = *end == ',' ? end + 1 : end;
            }
        }
        /* Modern Game Window: linear filtering of zoomed world pixels. */
        else if (!strcmp(argv[i], "--smooth-zoom")) smooth_zoom = 1;
        else if (!strcmp(argv[i], "--deterministic")) virtual_quantum_ns = 1000000u;
        else if (!strcmp(argv[i], "--poll-ns") && i + 1 < argc) {
            virtual_quantum_ns = strtoull(argv[++i], NULL, 0);
            if (!virtual_quantum_ns || virtual_quantum_ns > 1000000u)
                fail("virtual poll quantum range 1..1000000 ns");
        }
        else if (!strcmp(argv[i], "--input-script") && i + 1 < argc) {
            if (!_fullpath(replay_path, argv[++i], sizeof(replay_path)))
                fail("input replay path");
        }
        else if (!strcmp(argv[i], "--assets") && i + 1 < argc) assets = argv[++i];
        else if (!strcmp(argv[i], "--bios-fonts") && i + 1 < argc) fonts = argv[++i];
        else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            app.seed = (uint32_t)strtoul(argv[++i], NULL, 0);
            explicit_seed = 1;
        }
        else if (!strcmp(argv[i], "--smoke-ms") && i + 1 < argc)
            smoke_ms = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--frame") && i + 1 < argc) {
            if (!_fullpath(app.capture_path, argv[++i], sizeof(app.capture_path)))
                fail("capture path");
        }
        else source_argv[source_argc++] = argv[i];
    }
    if (source_argc > INT16_MAX) fail("source argument count");
    source_argv[source_argc] = NULL;
    if (virtual_quantum_ns) {
        host_virtual_clock_configure(virtual_quantum_ns);
        if (!explicit_seed) app.seed = 0; /* 046C:0000 RAM policy, not BIOS time. */
    }
    simant_diagnostics_launch(assets, app.seed);
    if (test_crash == 1) simant_diagnostics_test_crash();
    if (test_crash == 2) simant_diagnostics_test_thread_crash();
    if (test_abort) abort();
    if (headless &&
        (!SDL_SetHintWithPriority(SDL_HINT_VIDEO_DRIVER, "dummy", SDL_HINT_OVERRIDE) ||
         !SDL_SetHintWithPriority(SDL_HINT_AUDIO_DRIVER, "dummy", SDL_HINT_OVERRIDE)))
        fail("headless SDL driver selection");
    atexit(cleanup);
    app.host = host_create("SimAnt", 1);
    if (!app.host) { fprintf(stderr, "%s\n", host_error()); exit_status = 70; exit_reason = "SDL host startup"; return 70; }
    if (!host_set_window_scale(app.host, window_scale)) fail("window scale");
    host_set_event_observer(simant_diagnostics_event, NULL);
    fprintf(stderr, "Native video driver: %s\n", SDL_GetCurrentVideoDriver());
    if (replay_path[0]) load_replay(replay_path);
    if (sim_graphics_init(&app.graphics) != SIM_GRAPHICS_OK) fail("framebuffer");
    if (hosted_count &&
        (!sim_window_hosting_enable(&app.graphics.vga, hosted_ids, hosted_count) ||
         !native_windows_init(app.host, host_sdl_window(app.host))))
        fail("native window hosting");
    native_windows_set_smooth_zoom(smooth_zoom);
    sim_graphics_set_mode_changed_callback(&app.graphics, change_dimensions, &app);
    portable_source_graphics_resources_init(&app.resources);
    if (portable_source_graphics_resources_bind(&app.resources, &app.graphics, fonts) !=
            PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK) {
        fprintf(stderr, "%s\n", portable_source_graphics_resources_error(&app.resources));
        fail("verified font and pattern resources");
    }
    if (sim_graphics_source_clip_bind(&app.graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_bind_source_abi(&app.graphics, &g_5AAC) != SIM_GRAPHICS_OK ||
        sim_native_video_set_mode_services(install_video, uninstall_video, &app) != SIM_NATIVE_VIDEO_OK ||
        sim_native_video_startup_bind(&app.graphics) != SIM_NATIVE_VIDEO_OK)
        fail("source video startup binding");
    if (sim_handles_global_configure(64u * 1024u * 1024u, 65535) != SIM_HANDLE_OK)
        fail("native resource handles");
    if (sim_timing_clock_init_bios(&app.game_clock, 14318180, 12) != SIM_TIMING_OK ||
        sim_timing_clock_init_bios(&app.bios_clock, 14318180, 12) != SIM_TIMING_OK ||
        !portable_seed_source_bind(read_seed, &app)) fail("source clocks and seed");
    if (virtual_quantum_ns) app.bios_clock.tick_count = 0x1800b0u / 2u;
    if (!portable_sdl3_whole_audio_open(&app.audio))
        fail("ISA audio startup binding");
    portable_sdl3_whole_audio_set_source_timer_observer(&app.audio,
        source_timer_changed, &app);
    if (!portable_sdl3_whole_audio_bind_source_services(&app.audio))
        fail("source audio services");
    if (dos_files_set_root(assets) < 0) fail("asset directory");
    app.started_ns = host_time_ns();
    simant_diagnostics_start(app.started_ns);
    if (smoke_ms) app.smoke_deadline_ns = app.started_ns + smoke_ms * 1000000u;
    fprintf(stderr, "Entering reconstructed DOS main, seed=%u\n", app.seed);
    simant_diagnostics_progress("dos_game_main", app.replay_next, (long)fd_50F6_383A);
    dos_game_main((int16_t)source_argc, source_argv);
    free(source_argv);
    return 0;
}
