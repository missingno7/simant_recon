#include <SDL3/SDL.h>

#include "../../platform/host.h"
#include "../../ui_model/menus/interaction.h"
#include "../../ui_model/windows/history_render.h"
#include "../../game/recovered/engine.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct HistoryTestRect { int left, top, right, bottom; } HistoryTestRect;
typedef struct Target {
    int window_x, window_y, history_row, pause_x, pause_y, pause_row_x, pause_row_y;
    int history_x, history_y;
    HistoryTestRect buttons[10], graph;
    HistoryTestRect window;
    int geometry_ready;
    int menu_title, speed_title, pause_row;
} Target;

static Target target;
static SDL_TimerID timer_id;
static volatile unsigned phase, pushed_events, failures;
static volatile unsigned pause_toggles;
static unsigned long long operation_mask;
static HostEvent history_pointer_events[64];
static unsigned history_pointer_event_count;
static unsigned wrapped_history_events;
static int menu_prepared;

static void trace_host_event(const HostEvent *event)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_HOST_TRACE");
    FILE *file;
    if (path == NULL || *path == '\0' || event == NULL) return;
    file = fopen(path, "ab");
    if (file == NULL) return;
    (void)fprintf(file, "{\"kind\":%d,\"x\":%d,\"y\":%d,\"button\":%u}\n",
        (int)event->kind, event->x, event->y, (unsigned)event->button);
    (void)fclose(file);
}

static void write_progress(void)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_EVENT_PROGRESS");
    FILE *file;
    if (path == NULL || *path == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fprintf(file, "{\"menu_prepared\":%s,\"phase\":%u,"
        "\"geometry_ready\":%s,\"history_title\":%d,\"history_row\":%d,"
        "\"history_point\":[%d,%d],\"failures\":%u,\"pushed\":%u,"
        "\"wrapped_calls\":%u}\n", menu_prepared ? "true" : "false", phase,
        target.geometry_ready ? "true" : "false", target.menu_title,
        target.history_row, target.history_x, target.history_y, failures,
        pushed_events, wrapped_history_events);
    (void)fclose(file);
}

int __real_host_poll_event(Host *host, HostEvent *event);
int __real_sim_recovered_engine_history_event(SimRecoveredEngine *engine,
                                               uint16_t command);
SimRecoveredEngineStatus __real_sim_recovered_engine_proc_menu_command(
    SimRecoveredEngine *engine, uint16_t command);

SimRecoveredEngineStatus __wrap_sim_recovered_engine_proc_menu_command(
    SimRecoveredEngine *engine, uint16_t command)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_MENU_TRACE");
    const int16_t pause_before = engine->recovered.fd_50F6_047E;
    const uint64_t ticks_before = engine->completed_ticks;
    const SimRecoveredEngineStatus status =
        __real_sim_recovered_engine_proc_menu_command(engine, command);
    const int16_t pause_after = engine->recovered.fd_50F6_047E;
    const uint64_t ticks_after = engine->completed_ticks;
    FILE *file;
    if (path == NULL || *path == '\0') return status;
    file = fopen(path, "ab");
    if (file != NULL) {
        (void)fprintf(file, "{\"command\":%u,\"status\":%d,\"source_pause\":[%d,%d],"
            "\"completed_ticks\":[%llu,%llu]}\n", (unsigned)command, (int)status,
            (int)pause_before, (int)pause_after,
            (unsigned long long)ticks_before, (unsigned long long)ticks_after);
        (void)fclose(file);
    }
    return status;
}

int __wrap_host_poll_event(Host *host, HostEvent *event)
{
    const int result = __real_host_poll_event(host, event);
    if (result > 0) trace_host_event(event);
    if (result > 0 && target.geometry_ready &&
        (event->kind == HOST_EVENT_MOUSE_MOVE ||
         event->kind == HOST_EVENT_MOUSE_DOWN ||
         event->kind == HOST_EVENT_MOUSE_UP) &&
        event->x >= target.window.left && event->x <= target.window.right &&
        event->y >= target.window.top && event->y <= target.window.bottom &&
        history_pointer_event_count < 64)
        history_pointer_events[history_pointer_event_count++] = *event;
    return result;
}

static void write_snapshot(FILE *file, const PortableHistoryUiSnapshot *ui,
                           int16_t count)
{
    int i;
    (void)fprintf(file, "{\"ok\":true,\"shown_count\":%d,\"graph_colors\":[",
                  count);
    for (i = 0; i < PORTABLE_HISTORY_VISIBLE_GRAPHS; ++i)
        (void)fprintf(file, "%s%d", i ? "," : "", ui->graph_colors[i]);
    (void)fprintf(file, "],\"history_color\":[");
    for (i = 0; i < PORTABLE_HISTORY_SERIES_COUNT; ++i)
        (void)fprintf(file, "%s%d", i ? "," : "", ui->history_color[i]);
    (void)fprintf(file, "],\"shown_graphs\":[");
    for (i = 0; i < PORTABLE_HISTORY_VISIBLE_GRAPHS; ++i)
        (void)fprintf(file, "%s%d", i ? "," : "", ui->shown_graphs[i]);
    (void)fprintf(file, "]}");
}

static int snapshot(SimRecoveredEngine *engine, PortableHistoryUiSnapshot *ui,
                    int16_t *shown_count)
{
    memset(ui, 0, sizeof(*ui));
    *shown_count = 0;
    return sim_recovered_engine_history_ui_snapshot(engine, ui, shown_count);
}

int __wrap_sim_recovered_engine_history_event(SimRecoveredEngine *engine,
                                                uint16_t command)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_EVENT_TRACE");
    PortableHistoryUiSnapshot before, after;
    int16_t before_count = 0, after_count = 0;
    const int before_ok = snapshot(engine, &before, &before_count);
    const uint64_t ticks_before = engine->completed_ticks;
    const uint16_t rng_s_before = engine->session->rng.s_state;
    const uint32_t rng_c_before = engine->session->rng.c_state;
    const int16_t pause_before = engine->recovered.fd_50F6_047E;
    const int result = __real_sim_recovered_engine_history_event(engine, command);
    const int after_ok = snapshot(engine, &after, &after_count);
    const uint64_t ticks_after = engine->completed_ticks;
    const uint16_t rng_s_after = engine->session->rng.s_state;
    const uint32_t rng_c_after = engine->session->rng.c_state;
    const int16_t pause_after = engine->recovered.fd_50F6_047E;
    FILE *file;
    if (path != NULL && *path != '\0' && before_ok && after_ok) {
        file = fopen(path, "ab");
        if (file != NULL) {
            (void)fprintf(file, "{\"command\":%u,\"result\":%d,\"ticks\":[%llu,%llu],"
                "\"source_pause\":[%d,%d],"
                "\"rng\":[%u,%u,%u,%u],\"before\":", command, result,
                (unsigned long long)ticks_before, (unsigned long long)ticks_after,
                (int)pause_before, (int)pause_after,
                (unsigned)rng_s_before, (unsigned)rng_c_before,
                (unsigned)rng_s_after, (unsigned)rng_c_after);
            write_snapshot(file, &before, before_count);
            (void)fprintf(file, ",\"after\":");
            write_snapshot(file, &after, after_count);
            (void)fprintf(file, "}\n");
            (void)fclose(file);
        }
    }
    ++wrapped_history_events;
    return result;
}

static int text_has(const PortableMenuBar *menu, const PortableMenuString *s,
                    const char *wanted)
{
    const uint8_t *bytes = portable_menu_string_bytes(menu, s);
    size_t i, j, n = strlen(wanted);
    if (bytes == NULL || n == 0 || s->length < n) return 0;
    for (i = 0; i + n <= s->length; ++i) {
        for (j = 0; j < n; ++j) {
            uint8_t c = bytes[i + j] & 0x7fu;
            char lower = wanted[j];
            if (c >= 'A' && c <= 'Z') c = (uint8_t)(c + ('a' - 'A'));
            if (lower >= 'A' && lower <= 'Z') lower = (char)(lower + ('a' - 'A'));
            if (c != (uint8_t)lower) break;
        }
        if (j == n) return 1;
    }
    return 0;
}

static int prepare_menu(void)
{
    PortableDatabase database = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[64];
    PortableMenuInteraction interaction;
    size_t count = 0, row;
    size_t window_title = (size_t)-1, speed_title = (size_t)-1;
    size_t history_row = (size_t)-1, pause_row = (size_t)-1;
    int result = 0;
    if (portable_db_open(&database, "assets/SHARED") != PORTABLE_DB_OK) return 0;
    portable_menu_init(&menu);
    if (portable_menu_load(&menu, &database, 640) != PORTABLE_MENU_OK ||
        portable_menu_build_draw_plan(&menu, 1, (PortableMenuRect){0,0,640,350},
            640, 8, 14, 0, &layout, commands, 64, &count) != PORTABLE_MENU_OK)
        goto done;
    for (row = 0; row < menu.titles.count; ++row) {
        if (text_has(&menu, portable_menu_title(&menu, row), "window"))
            window_title = row;
        if (text_has(&menu, portable_menu_title(&menu, row), "speed"))
            speed_title = row;
    }
    if (window_title == (size_t)-1 || speed_title == (size_t)-1 ||
        portable_menu_interaction_init_from_bar(&interaction, &menu, &layout,
            window_title, 640, 350, 14, 8, 0) != PORTABLE_MENU_INTERACTION_RUNNING)
        goto done;
    for (row = 0; row < interaction.item_count; ++row)
        if (text_has(&menu, portable_menu_item(&menu, window_title, row), "history"))
            history_row = row;
    if (history_row == (size_t)-1 || !interaction.row_enabled[history_row] ||
        ((((window_title << 4) + history_row - 0x2ffu) & 0xffffu) != 0xfd15u))
        goto done;
    target.menu_title = (int)window_title;
    target.history_row = (int)history_row;
    target.window_x = (layout.title_rects[window_title].left +
                       layout.title_rects[window_title].right) / 2;
    target.window_y = (layout.title_rects[window_title].top +
                       layout.title_rects[window_title].bottom) / 2;
    target.history_x = (interaction.row_rects[history_row].left +
                        interaction.row_rects[history_row].right) / 2;
    target.history_y = (interaction.row_rects[history_row].top +
                        interaction.row_rects[history_row].bottom) / 2;
    if (portable_menu_interaction_init_from_bar(&interaction, &menu, &layout,
            speed_title, 640, 350, 14, 8, 0) != PORTABLE_MENU_INTERACTION_RUNNING)
        goto done;
    for (row = 0; row < interaction.item_count; ++row)
        if (text_has(&menu, portable_menu_item(&menu, speed_title, row), "pause"))
            pause_row = row;
    if (pause_row == (size_t)-1 || !interaction.row_enabled[pause_row] ||
        ((((speed_title << 4) + pause_row - 0x2ffu) & 0xffffu) != 0xfd41u))
        goto done;
    target.speed_title = (int)speed_title;
    target.pause_row = (int)pause_row;
    target.pause_x = (layout.title_rects[speed_title].left +
                      layout.title_rects[speed_title].right) / 2;
    target.pause_y = (layout.title_rects[speed_title].top +
                      layout.title_rects[speed_title].bottom) / 2;
    target.pause_row_x = (interaction.row_rects[pause_row].left +
                          interaction.row_rects[pause_row].right) / 2;
    target.pause_row_y = (interaction.row_rects[pause_row].top +
                          interaction.row_rects[pause_row].bottom) / 2;
    result = 1;
done:
    portable_menu_release(&menu);
    portable_db_close(&database);
    return result;
}

static int read_rect(unsigned object_id, HistoryTestRect *rect)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_GEOMETRY_REPORT");
    FILE *file;
    long size;
    char *data, needle[64], *at, *end;
    int ok = 0;
    if (path == NULL || rect == NULL) return 0;
    file = fopen(path, "rb");
    if (file == NULL) return 0;
    if (fseek(file, 0, SEEK_END) != 0 || (size = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) != 0) goto done;
    data = (char *)malloc((size_t)size + 1);
    if (data == NULL) goto done;
    if (fread(data, 1, (size_t)size, file) != (size_t)size) { free(data); goto done; }
    data[size] = '\0';
    (void)snprintf(needle, sizeof(needle), "\"object_id\":%u", object_id);
    at = strstr(data, needle);
    if (at != NULL && (end = strstr(at, "\"rect\":[")) != NULL && end - at < 160 &&
        sscanf(end, "\"rect\":[%d,%d,%d,%d]", &rect->left, &rect->top,
               &rect->right, &rect->bottom) == 4) ok = 1;
    free(data);
done:
    (void)fclose(file);
    return ok;
}

static int prepare_geometry(void)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_GEOMETRY_REPORT");
    FILE *file;
    char line[128];
    int got_window = 0, object_id;
    if (!read_rect(0x150e, &target.graph)) return 0;
    for (object_id = 0x1503; object_id <= 0x150c; ++object_id)
        if (!read_rect((unsigned)object_id, &target.buttons[object_id - 0x1503]))
            return 0;
    file = fopen(path, "rb");
    if (file == NULL) return 0;
    while (fgets(line, sizeof(line), file) != NULL) {
        if (strstr(line, "\"window_rect\":[") != NULL &&
            sscanf(strstr(line, "\"window_rect\":["),
                   "\"window_rect\":[%d,%d,%d,%d]", &target.window.left,
                   &target.window.top, &target.window.right, &target.window.bottom) == 4)
            got_window = 1;
    }
    (void)fclose(file);
    target.geometry_ready = got_window;
    return got_window;
}

static int push_mouse(uint32_t type, int x, int y)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = type;
    if (type == SDL_EVENT_MOUSE_MOTION) {
        event.motion.timestamp = SDL_GetTicksNS();
        event.motion.x = (float)x; event.motion.y = (float)y;
        event.motion.state = SDL_BUTTON_LMASK;
    } else {
        event.button.timestamp = SDL_GetTicksNS();
        event.button.button = SDL_BUTTON_LEFT;
        event.button.down = type == SDL_EVENT_MOUSE_BUTTON_DOWN;
        event.button.x = (float)x; event.button.y = (float)y;
    }
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    return 1;
}

static int click(int x, int y)
{ return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN, x, y) &&
         push_mouse(SDL_EVENT_MOUSE_BUTTON_UP, x, y); }

static int select_history(void)
{ return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN, target.window_x, target.window_y) &&
         push_mouse(SDL_EVENT_MOUSE_MOTION, target.history_x, target.history_y) &&
         push_mouse(SDL_EVENT_MOUSE_BUTTON_UP, target.history_x, target.history_y); }

static int toggle_pause(void)
{
    ++pause_toggles;
    return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN, target.pause_x, target.pause_y) &&
           push_mouse(SDL_EVENT_MOUSE_MOTION, target.pause_row_x, target.pause_row_y) &&
           push_mouse(SDL_EVENT_MOUSE_BUTTON_UP, target.pause_row_x, target.pause_row_y);
}

static const unsigned button_sequence[8] = {0x1503,0x1504,0x1505,0x1506,
                                             0x1507,0x1507,0x1505,0x1504};

static Uint32 SDLCALL inject_history(void *context, SDL_TimerID id, Uint32 interval)
{
    int x, y;
    (void)context; (void)id; (void)interval;
    if (phase >= 2 && phase <= 9 && !target.geometry_ready && !prepare_geometry()) {
        write_progress();
        return 100;
    }
    switch (phase) {
    case 0:
        if (!toggle_pause()) ++failures;
        operation_mask |= 1u;
        break;
    case 1:
        if (!select_history()) ++failures;
        operation_mask |= 2u;
        break;
    case 10:
        if (!target.geometry_ready ||
            (x = (target.graph.left + target.graph.right) / 2,
             y = (target.graph.top + target.graph.bottom) / 2,
             !push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN, x, y))) ++failures;
        operation_mask |= 1u << 10;
        break;
    case 11:
        x = (target.graph.left + target.graph.right) / 2 + 8;
        y = (target.graph.top + target.graph.bottom) / 2;
        if (!push_mouse(SDL_EVENT_MOUSE_MOTION, x, y)) ++failures;
        operation_mask |= 1u << 11;
        break;
    case 12:
        x = (target.graph.left + target.graph.right) / 2 + 8;
        y = (target.graph.top + target.graph.bottom) / 2;
        if (!push_mouse(SDL_EVENT_MOUSE_BUTTON_UP, x, y)) ++failures;
        operation_mask |= 1u << 12;
        break;
    case 13:
        if (!toggle_pause()) ++failures;
        operation_mask |= 4u;
        break;
    default:
        if (phase >= 2 && phase <= 9) {
            const unsigned button = button_sequence[phase - 2];
            HistoryTestRect *r = &target.buttons[button - 0x1503];
            if (!click((r->left + r->right) / 2, (r->top + r->bottom) / 2))
                ++failures;
            operation_mask |= 1u << (phase - 2 + 2);
        } else return 0;
        break;
    }
    ++phase;
    write_progress();
    return phase == 13 ? 400 : 250;
}

__attribute__((constructor)) static void start_history_timer(void)
{
    menu_prepared = prepare_menu();
    if (menu_prepared) timer_id = SDL_AddTimer(350, inject_history, NULL);
    else ++failures;
    write_progress();
}

__attribute__((destructor)) static void write_history_report(void)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_EVENT_REPORT");
    FILE *file;
    unsigned i;
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    if (path == NULL || *path == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fprintf(file, "{\"schema\":\"portable-live-history-inject-v1\","
        "\"phase_count\":%u,\"pushed_event_count\":%u,\"injection_failures\":%u,"
        "\"operation_mask\":%llu,\"menu_title\":%d,\"history_row\":%d,"
        "\"history_command\":64789,\"pause_toggles\":%u,\"button_commands\":[",
        phase, pushed_events, failures, operation_mask, target.menu_title,
        target.history_row, pause_toggles);
    for (i = 0; i < 8; ++i)
        (void)fprintf(file, "%s%u", i ? "," : "", button_sequence[i]);
    (void)fprintf(file, "],\"graph_area\":[%d,%d,%d,%d],\"window_rect\":[%d,%d,%d,%d],"
        "\"host_pointer_events\":[", target.graph.left, target.graph.top,
        target.graph.right, target.graph.bottom, target.window.left, target.window.top,
        target.window.right, target.window.bottom);
    for (i = 0; i < history_pointer_event_count; ++i) {
        const HostEvent *event = &history_pointer_events[i];
        (void)fprintf(file, "%s{\"kind\":%d,\"x\":%d,\"y\":%d,\"button\":%u}",
            i ? "," : "", (int)event->kind, event->x, event->y,
            (unsigned)event->button);
    }
    (void)fprintf(file, "],\"wrapped_history_events\":%u}\n",
                  wrapped_history_events);
    (void)fclose(file);
}
