#include <SDL3/SDL.h>

#include "../../ui_model/menus/interaction.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct MenuTargets {
    int resource_id;
    int title_index;
    int title_rect[4];
    int speed_row_rect[4];
    int pause_row_rect[4];
    int title_x[3];
    int title_y[3];
    int row_x[3];
    int row_y[3];
    size_t target_row[3];
    int ready;
} MenuTargets;

static MenuTargets targets;
static SDL_TimerID timer_id;
static volatile unsigned pushed_events;
static volatile unsigned injection_failures;
static unsigned phase;
static uint64_t paused_window_ns;
static uint64_t pause_started_ns;

static int text_equals(const PortableMenuBar *menu,
                       const PortableMenuString *string,
                       const char *wanted)
{
    const uint8_t *bytes = portable_menu_string_bytes(menu, string);
    size_t i, length = strlen(wanted);
    if (bytes == NULL || string->length != length) return 0;
    for (i = 0; i < length; ++i)
        if ((bytes[i] & 0x7fu) != (uint8_t)wanted[i]) return 0;
    return 1;
}

static int prepare_targets(void)
{
    PortableDatabase database = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand draw[32];
    PortableMenuInteraction interaction;
    size_t command_count = 0, title = (size_t)-1, row;
    size_t fast_row = (size_t)-1, pause_row = (size_t)-1;
    int result = 0;

    if (portable_db_open(&database, "assets/SHARED") != PORTABLE_DB_OK)
        return 0;
    portable_menu_init(&menu);
    if (portable_menu_load(&menu, &database, 640) != PORTABLE_MENU_OK ||
        menu.resource_id != 0 ||
        portable_menu_build_draw_plan(&menu, 1,
            (PortableMenuRect){0, 0, 640, 350}, 640, 8, 14, 0,
            &layout, draw, sizeof(draw) / sizeof(draw[0]),
            &command_count) != PORTABLE_MENU_OK)
        goto done;
    for (row = 0; row < menu.titles.count; ++row) {
        if (text_equals(&menu, portable_menu_title(&menu, row), " Speed")) {
            title = row;
            break;
        }
    }
    if (title == (size_t)-1 ||
        portable_menu_interaction_init_from_bar(&interaction, &menu, &layout,
            title, 640, 350, 14, 8, 0) !=
            PORTABLE_MENU_INTERACTION_RUNNING)
        goto done;
    for (row = 0; row < interaction.item_count; ++row) {
        const PortableMenuString *item = portable_menu_item(&menu, title, row);
        if (text_equals(&menu, item, " Slow")) fast_row = row;
        if (text_equals(&menu, item, " Pause  ")) pause_row = row;
    }
    if (fast_row == (size_t)-1 || pause_row == (size_t)-1 ||
        !interaction.row_enabled[fast_row] || !interaction.row_enabled[pause_row])
        goto done;

    targets.title_x[0] = (layout.title_rects[title].left +
                          layout.title_rects[title].right) / 2;
    targets.title_y[0] = (layout.title_rects[title].top +
                          layout.title_rects[title].bottom) / 2;
    targets.resource_id = menu.resource_id;
    targets.title_index = (int)title;
    targets.title_rect[0] = layout.title_rects[title].left;
    targets.title_rect[1] = layout.title_rects[title].top;
    targets.title_rect[2] = layout.title_rects[title].right;
    targets.title_rect[3] = layout.title_rects[title].bottom;
    targets.speed_row_rect[0] = interaction.row_rects[fast_row].left;
    targets.speed_row_rect[1] = interaction.row_rects[fast_row].top;
    targets.speed_row_rect[2] = interaction.row_rects[fast_row].right;
    targets.speed_row_rect[3] = interaction.row_rects[fast_row].bottom;
    targets.pause_row_rect[0] = interaction.row_rects[pause_row].left;
    targets.pause_row_rect[1] = interaction.row_rects[pause_row].top;
    targets.pause_row_rect[2] = interaction.row_rects[pause_row].right;
    targets.pause_row_rect[3] = interaction.row_rects[pause_row].bottom;
    targets.row_x[0] = (interaction.row_rects[fast_row].left +
                        interaction.row_rects[fast_row].right) / 2;
    targets.row_y[0] = (interaction.row_rects[fast_row].top +
                        interaction.row_rects[fast_row].bottom) / 2;
    targets.target_row[0] = fast_row;
    targets.target_row[1] = targets.target_row[2] = pause_row;
    targets.title_x[1] = targets.title_x[2] = targets.title_x[0];
    targets.title_y[1] = targets.title_y[2] = targets.title_y[0];
    targets.row_x[1] = targets.row_x[2] =
        (interaction.row_rects[pause_row].left +
         interaction.row_rects[pause_row].right) / 2;
    targets.row_y[1] = targets.row_y[2] =
        (interaction.row_rects[pause_row].top +
         interaction.row_rects[pause_row].bottom) / 2;
    targets.ready = 1;
    result = 1;
done:
    portable_menu_release(&menu);
    portable_db_close(&database);
    return result;
}

static int push_mouse(uint32_t type, int x, int y)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = type;
    if (type == SDL_EVENT_MOUSE_MOTION) {
        event.motion.timestamp = SDL_GetTicksNS();
        event.motion.x = (float)x;
        event.motion.y = (float)y;
        event.motion.state = SDL_BUTTON_LMASK;
    } else {
        event.button.timestamp = SDL_GetTicksNS();
        event.button.button = SDL_BUTTON_LEFT;
        event.button.down = type == SDL_EVENT_MOUSE_BUTTON_DOWN;
        event.button.x = (float)x;
        event.button.y = (float)y;
    }
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    return 1;
}

static int push_drag_release(unsigned target)
{
    return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN,
                     targets.title_x[target], targets.title_y[target]) &&
           push_mouse(SDL_EVENT_MOUSE_MOTION,
                     targets.row_x[target], targets.row_y[target]) &&
           push_mouse(SDL_EVENT_MOUSE_BUTTON_UP,
                     targets.row_x[target], targets.row_y[target]);
}

static Uint32 SDLCALL inject_physical_menu(void *context, SDL_TimerID id,
                                          Uint32 interval)
{
    (void)context;
    (void)id;
    (void)interval;
    if (!targets.ready) {
        ++injection_failures;
        return 0;
    }
    if (phase == 0) {
        ++phase;
        if (!push_drag_release(0)) ++injection_failures;
        return 300;
    }
    if (phase == 1) {
        ++phase;
        if (!push_drag_release(1)) ++injection_failures;
        pause_started_ns = SDL_GetTicksNS();
        return 700;
    }
    if (phase == 2) {
        ++phase;
        if (!push_drag_release(2)) ++injection_failures;
        paused_window_ns = SDL_GetTicksNS() - pause_started_ns;
        return 0;
    }
    return 0;
}

__attribute__((constructor)) static void start_physical_menu_timer(void)
{
    if (prepare_targets())
        timer_id = SDL_AddTimer(350, inject_physical_menu, NULL);
    else
        ++injection_failures;
}

__attribute__((destructor)) static void stop_physical_menu_timer(void)
{
    const char *event_path = getenv("SIMANT_LIVE_SMOKE_EVENT_REPORT");
    const char *geometry_path = getenv("SIMANT_LIVE_MENU_GEOMETRY_REPORT");
    FILE *file;
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    if (geometry_path != NULL && geometry_path[0] != '\0') {
        file = fopen(geometry_path, "wb");
        if (file != NULL) {
            (void)fprintf(file,
                "{\"resource\":\"SHARED kind 6\",\"resource_id\":%d,"
                "\"title\":\" Speed\",\"title_index\":%d,"
                "\"title_rect\":[%d,%d,%d,%d],\"speed_target\":\" Slow\","
                "\"speed_row_index\":%zu,\"speed_row_rect\":[%d,%d,%d,%d],"
                "\"pause_row\":\" Pause  \",\"pause_row_index\":%zu,"
                "\"pause_row_rect\":[%d,%d,%d,%d]}\n",
                targets.resource_id, targets.title_index,
                targets.title_rect[0], targets.title_rect[1],
                targets.title_rect[2], targets.title_rect[3], targets.target_row[0],
                targets.speed_row_rect[0], targets.speed_row_rect[1],
                targets.speed_row_rect[2], targets.speed_row_rect[3],
                targets.target_row[1], targets.pause_row_rect[0],
                targets.pause_row_rect[1], targets.pause_row_rect[2],
                targets.pause_row_rect[3]);
            (void)fclose(file);
        }
    }
    if (event_path == NULL || event_path[0] == '\0') return;
    file = fopen(event_path, "wb");
    if (file == NULL) return;
    (void)fprintf(file,
        "{\"event_kind\":\"SDL physical title-drag-row-release\","
        "\"interaction_count\":%u,\"pushed_event_count\":%u,"
        "\"injection_failures\":%u,\"paused_window_ns\":%llu}\n",
        phase, pushed_events, injection_failures,
        (unsigned long long)paused_window_ns);
    (void)fclose(file);
}
