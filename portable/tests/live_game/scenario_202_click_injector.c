/* Opt-in physical SDL click for the bounded NEXT5 scenario-202 smoke. */
#include "../../game/resources/database.h"
#include "../../ui_model/windows/open.h"
#include "../../ui_model/windows/registry.h"

#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { SCREEN_WIDTH = 640, SCREEN_HEIGHT = 350, SCENARIO_WINDOW_ID = 0x0200 };

static SDL_TimerID timer_id;
static volatile unsigned pushed_events;
static volatile unsigned endgame_key_events;
static volatile unsigned scenario_mouse_events;
static volatile unsigned wait_callbacks;
static volatile int endgame_dismissed;
static int target_x = -1;
static int target_y = -1;
static int rect[4] = {-1, -1, -1, -1};
static int target_ready;

static int derive_target_from_resource(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    PortableWindowOpenScene scene = {0};
    PortableWindowOpenResult open_result;
    PortableWindowRegistrySlot *slot;
    PortableWindowRect menu = {0, 0, SCREEN_WIDTH, 0};
    int16_t no_open_windows[1];
    int16_t args[4] = {0, 0, 0, 0};
    char root[1024];
    int okay = 0;

    const char *asset_dir = getenv("SIMANT_ASSET_DIR");
    if (asset_dir == NULL || asset_dir[0] == '\0') asset_dir = "assets";
    if (snprintf(root, sizeof(root), "%s/HCEGANT", asset_dir) >=
        (int)sizeof(root))
        goto done;
    if (portable_db_open(&database, root) != PORTABLE_DB_OK ||
        portable_window_registry_init(&registry, &database, 0) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        portable_window_registry_load(&registry, 2) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        portable_window_open_scene_init(&registry, no_open_windows, 0, &scene) !=
            PORTABLE_WINDOW_OPEN_OK)
        goto done;
    if (portable_window_open_apply(&registry, &scene, SCENARIO_WINDOW_ID, args,
            SCREEN_WIDTH, SCREEN_HEIGHT, &menu, &open_result) !=
        PORTABLE_WINDOW_OPEN_OK)
        goto done;
    slot = &registry.slots[2];
    if (slot->window.count <= 2 ||
        !(slot->window.objects[2].flags & PORTABLE_WINDOW_OBJECT_SELECTABLE))
        goto done;
    rect[0] = slot->window.objects[2].rect.left;
    rect[1] = slot->window.objects[2].rect.top;
    rect[2] = slot->window.objects[2].rect.right;
    rect[3] = slot->window.objects[2].rect.bottom;
    if (rect[0] >= rect[2] || rect[1] >= rect[3]) goto done;
    target_x = (rect[0] + rect[2]) / 2;
    target_y = (rect[1] + rect[3]) / 2;
    target_ready = 1;
    okay = 1;
done:
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
    return okay;
}

static int selector_is_active(void)
{
    const char *path = getenv("SIMANT_LIVE_SCENARIO_READY");
    FILE *file;
    if (path == NULL || path[0] == '\0') return 0;
    file = fopen(path, "rb");
    if (file == NULL) return 0;
    (void)fclose(file);
    return 1;
}

static int endgame_is_active(void)
{
    const char *path = getenv("SIMANT_LIVE_ENDGAME_READY");
    FILE *file;
    if (path == NULL || path[0] == '\0') return 0;
    file = fopen(path, "rb");
    if (file == NULL) return 0;
    (void)fclose(file);
    return 1;
}

static int push_escape(SDL_EventType type)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = type;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.scancode = SDL_SCANCODE_ESCAPE;
    event.key.key = SDLK_ESCAPE;
    event.key.mod = SDL_KMOD_NONE;
    event.key.down = (type == SDL_EVENT_KEY_DOWN);
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    ++endgame_key_events;
    return 1;
}

static void write_event_report(void)
{
    const char *path = getenv("SIMANT_LIVE_SCENARIO_EVENT_REPORT");
    FILE *file;
    if (path == NULL || path[0] == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fprintf(file,
        "{\"target_derived_from_resource\":%s,\"window_id\":512,"
        "\"object_index\":2,\"object_rect\":[%d,%d,%d,%d],"
        "\"target\":[%d,%d],\"pushed_event_count\":%u,"
        "\"endgame_key_events\":%u,\"scenario_mouse_events\":%u,"
        "\"selector_wait_callbacks\":%u}\n",
        target_ready ? "true" : "false", rect[0], rect[1], rect[2], rect[3],
        target_x, target_y, pushed_events, endgame_key_events,
        scenario_mouse_events, wait_callbacks);
    (void)fclose(file);
}

static int push_mouse(SDL_EventType type)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = type;
    event.button.timestamp = SDL_GetTicksNS();
    event.button.button = SDL_BUTTON_LEFT;
    event.button.down = (type == SDL_EVENT_MOUSE_BUTTON_DOWN);
    event.button.x = (float)target_x;
    event.button.y = (float)target_y;
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    return 1;
}

static Uint32 SDLCALL inject_when_ready(void *context, SDL_TimerID id,
                                        Uint32 interval)
{
    (void)context;
    (void)id;
    (void)interval;
    ++wait_callbacks;
    if (!endgame_dismissed) {
        if (!endgame_is_active()) return 25;
        if (!push_escape(SDL_EVENT_KEY_DOWN) ||
            !push_escape(SDL_EVENT_KEY_UP))
            return 0;
        endgame_dismissed = 1;
        write_event_report();
        return 25;
    }
    if (!target_ready || !selector_is_active()) return 25;
    if (!push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN) ||
        !push_mouse(SDL_EVENT_MOUSE_BUTTON_UP)) return 0;
    scenario_mouse_events = 2;
    write_event_report();
    return 0;
}

__attribute__((constructor)) static void start_scenario_click_timer(void)
{
    (void)derive_target_from_resource();
    timer_id = SDL_AddTimer(25, inject_when_ready, NULL);
    write_event_report();
}

__attribute__((destructor)) static void write_scenario_click_report(void)
{
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    write_event_report();
}
