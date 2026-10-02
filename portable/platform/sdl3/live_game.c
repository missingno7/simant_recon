#include "live_game.h"

#include <stdlib.h>

#ifndef SIMANT_ENABLE_RECOVERED_CORE

struct PortableLiveGame { char unavailable; };

PortableLiveGame *portable_live_game_create(
    SimSession *session, PortableWindowRegistry *registry,
    PortableWindowRenderer *renderer, PortableFontSet *fonts,
    const PortableWindowTitlesStringSet *titles,
    PortableWindowTitleProjection *title_projection, Host *host,
    const HostPalette *host_palette, const PortablePalette *palette)
{
    (void)session; (void)registry; (void)renderer; (void)fonts;
    (void)titles; (void)title_projection; (void)host;
    (void)host_palette; (void)palette;
    return NULL;
}

int portable_live_game_update(PortableLiveGame *game, uint64_t now_ns)
{ (void)game; (void)now_ns; return 0; }
int portable_live_game_event(PortableLiveGame *game, const HostEvent *event)
{ (void)game; (void)event; return 0; }
void portable_live_game_destroy(PortableLiveGame *game) { free(game); }
const char *portable_live_game_error(const PortableLiveGame *game)
{ (void)game; return "recovered core is not enabled in this build"; }
int portable_live_game_quit_requested(const PortableLiveGame *game)
{ (void)game; return 0; }
uint64_t portable_live_game_completed_ticks(const PortableLiveGame *game)
{ (void)game; return 0; }
int portable_live_game_needs_present(const PortableLiveGame *game)
{ (void)game; return 0; }
void portable_live_game_mark_presented(PortableLiveGame *game) { (void)game; }

#else

#include "picture_modal.h"
#include "scenario_modal.h"
#include "menu_modal.h"
#include "../../game/recovered/engine.h"
#include "../../game/timing.h"
#include "../../ui_model/input/input.h"
#include "../../ui_model/windows/game_view.h"
#include "../../ui_model/windows/overview_view.h"
#include "../../ui_model/menus/menu.h"
#include "../../ui_model/windows/open.h"
#include "../../ui_model/windows/operations.h"
#include "../../ui_model/windows/ribbon.h"
#include "../../ui_model/windows/control_render/control_input_from_session.h"
#include "../../ui_model/windows/control_preselect.h"
#include "../../ui_model/menus/render.h"
#include "../../ui_model/dialogs/end_game_view.h"
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
#include "../../ui_model/windows/history_render.h"
#endif

#include <stdio.h>
#include <string.h>
#include <stddef.h>

enum {
    LIVE_SCREEN_WIDTH = 640,
    LIVE_SCREEN_HEIGHT = 350,
    LIVE_PIT_NUMERATOR = 14318180,
    LIVE_PIT_DENOMINATOR = 12,
    LIVE_MAX_HELD_KEYS = 32,
    LIVE_SOURCE_EVENT_CAPACITY = 16,
    LIVE_DEFERRED_HOST_EVENT_CAPACITY = 32
};

struct PortableLiveGame {
    SimSession *session;
    PortableWindowRegistry *registry;
    PortableWindowRenderer *renderer;
    PortableFontSet *fonts;
    const PortableWindowTitlesStringSet *titles;
    PortableWindowTitleProjection *title_projection;
    Host *host;
    const HostPalette *host_palette;
    const PortablePalette *palette;
    SimSession *snapshot_session;
    SimRecoveredEngine engine;
    SimTimingClock clock;
    SimTimingScheduler scheduler;
    PortableWindowOpenScene windows;
    PortableWindowOpenResult open_result;
    PortableMenuBar menu;
    PortableRibbonState ribbons;
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
    PortableHistoryActiveResources history_resources;
    uint8_t history_input_active;
#endif
    HostEvent held_keys[LIVE_MAX_HELD_KEYS];
    size_t held_key_count;
    SimRecoveredEvent source_events[LIVE_SOURCE_EVENT_CAPACITY];
    size_t source_event_head;
    size_t source_event_count;
    SimRecoveredEvent previous_mouse_event;
    int32_t previous_mouse_event_tick;
    HostEvent deferred_host_events[LIVE_DEFERRED_HOST_EVENT_CAPACITY];
    size_t deferred_host_event_count;
    uint8_t source_wait_active;
    uint64_t next_source_event_poll_ns;
    int16_t cursor_x, cursor_y;
    uint8_t left_down;
    uint8_t dos_keyboard_flags;
    uint8_t clock_started;
    uint8_t dirty;
    uint8_t frame_pending;
    int quit_requested;
    uint8_t control_down;
    /* TU-private g_1B62/g_1B64 begin at one and survive NewGame. */
    int16_t mode_percent;
    int16_t caste_percent;
    uint8_t faulted;
    int16_t source_clip_window;
    int16_t source_clip_stack[16];
    uint8_t source_clip_depth;
    char error[192];
    uint64_t last_now_ns;
    uint64_t started_ns;
    uint8_t end_game_opened;
    uint8_t end_game_closed;
    uint8_t end_game_boundary_reached;
    uint8_t end_game_quit_seen;
    uint32_t end_game_open_tick;
    uint32_t end_game_close_tick;
    uint32_t end_game_wait_start;
    uint32_t end_game_wait_delay;
    int16_t end_game_last_key;
    int32_t end_game_score;
    uint8_t end_game_scenario_index;
    uint8_t end_game_level_index;
    int16_t end_game_window_rect[4];
    int16_t end_game_object_rects[12];
    uint64_t end_game_polls;
    uint64_t end_game_dialog_abort_polls;
    uint64_t end_game_song_done_polls;
    uint64_t end_game_song_requests;
    uint64_t end_game_rendered_frames;
    uint8_t end_game_modal_frame_saved;
    char end_game_boundary[64];
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    uint8_t end_game_test_called;
    int end_game_test_callback_result;
#ifdef SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC
    uint8_t newgame_202_action_called;
    uint8_t newgame_202_returned;
    int16_t newgame_202_action_status;
    int16_t newgame_202_selection_code;
    int16_t newgame_202_source_result;
    uint64_t gameover_callback_count;
    uint64_t gameover_entry_completed_ticks;
    uint8_t gameover_callback_completed;
    SimGameOverInput gameover_callback_input;
    SimRng gameover_callback_rng_before;
    SimRng gameover_callback_rng_after;
#endif
    uint64_t query_calls[SIM_RECOVERED_QUERY_BUTTON + 1];
    uint64_t effect_calls[SIM_RECOVERED_EFFECT_GRAPHICS_LINE + 1];
    uint64_t pause_action_calls;
    uint64_t pause_start_ticks;
    uint64_t pause_end_ticks;
    uint64_t pause_start_ns;
    uint64_t pause_duration_ns;
    uint64_t paused_update_calls;
    uint64_t speed_action_calls[4];
    uint64_t menu_item_state_calls;
    uint64_t menu_item_text_calls;
    uint64_t control_event_calls;
    uint16_t control_last_code;
    uint64_t scroll_action_calls;
    uint64_t edit_hotbox_clicks;
    uint64_t edit_events_delivered;
    uint64_t edit_double_clicks;
    uint64_t yellow_key_calls;
    uint64_t yellow_key_handled_calls;
    uint64_t yellow_key_unhandled_calls;
    uint64_t yellow_key_unhandled_unchanged_calls;
    int16_t yellow_key_last;
    int16_t yellow_key_last_result;
    uint64_t overview_render_calls;
    int16_t overview_mode;
    int16_t overview_image_rect[4];
    int16_t overview_cursor_rect[4];
    int16_t edit_goal_active_after_event;
    int16_t edit_goal_mode_after_event;
    int16_t edit_goal_x_after_event;
    int16_t edit_goal_y_after_event;
    int16_t edit_goal_plane_after_event;
    uint8_t edit_left_down_after_event;
#endif
};

static void set_error(PortableLiveGame *game, const char *message)
{
    if (game == NULL) return;
    if (message == NULL) message = "unknown live-game error";
    (void)snprintf(game->error, sizeof(game->error), "%s", message);
}

#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
    defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
static int live_test_scenario_202_enabled(void)
{
    return getenv("SIMANT_LIVE_NEWGAME_202_DIAGNOSTIC") != NULL ||
           getenv("SIMANT_LIVE_NATURAL_GAMEOVER_202_DIAGNOSTIC") != NULL;
}
#endif

static int redraw(PortableLiveGame *game);
static int redraw_snapshot_edit(PortableLiveGame *game);
static int apply_window_object_operation(PortableLiveGame *game,
                                         const SimRecoveredEffect *effect);
static int run_source_control(PortableLiveGame *game, int16_t x, int16_t y,
                              int *handled);
static int control_pointer_poll(void *context, SimSetupPoint *point);
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
static int run_source_history(PortableLiveGame *game, int16_t x, int16_t y,
                              int *handled);
static int draw_history_graph_effect(PortableLiveGame *game, int16_t graph,
                                     int16_t hilite, int16_t slot);
#endif

#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
static void trace_control_input(const char *kind, int a, int b, int c, int d)
{
    const char *path = getenv("SIMANT_LIVE_CONTROL_INPUT_TRACE");
    FILE *file;
    if (path == NULL || *path == '\0') return;
    file = fopen(path, "ab");
    if (file == NULL) return;
    (void)fprintf(file, "{\"kind\":\"%s\",\"values\":[%d,%d,%d,%d]}\n",
                  kind, a, b, c, d);
    (void)fclose(file);
}

#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
static int write_history_geometry(PortableLiveGame *game)
{
    const char *path = getenv("SIMANT_LIVE_HISTORY_GEOMETRY_REPORT");
    const PortableWindowRegistrySlot *slot = &game->registry->slots[0x15];
    FILE *file;
    unsigned i;
    if (path == NULL || *path == '\0') return 1;
    file = fopen(path, "wb");
    if (file == NULL) return 0;
    (void)fprintf(file, "{\"schema\":\"portable-live-history-geometry-v1\","
        "\"window_id\":5376,\"front_window\":%d,"
        "\"window_rect\":[%d,%d,%d,%d],\"objects\":[",
        game->windows.front_window_id, slot->window.rect.left, slot->window.rect.top,
        slot->window.rect.right, slot->window.rect.bottom);
    for (i = 0; slot->loaded && i < slot->window.count; ++i) {
        const PortableWindowObject *item = &slot->window.objects[i];
        (void)fprintf(file, "%s{\"object_id\":%u,\"type\":%u,\"flags\":%u,"
            "\"rect\":[%d,%d,%d,%d]}", i == 0 ? "" : ",", 0x1500u | i,
            item->type, item->flags, item->rect.left, item->rect.top,
            item->rect.right, item->rect.bottom);
    }
    (void)fprintf(file, "]}\n");
    return fclose(file) == 0;
}
#endif

static int write_control_geometry(PortableLiveGame *game)
{
    const char *path = getenv("SIMANT_LIVE_CONTROL_GEOMETRY_REPORT");
    FILE *file;
    unsigned window, object;
    if (path == NULL || *path == '\0') return 1;
    file = fopen(path, "wb");
    if (file == NULL) return 0;
    (void)fprintf(file, "{\"schema\":\"portable-live-control-geometry-v1\","
        "\"front_window\":%d,\"shared_triangle\":[%u,%u,%u],\"windows\":[",
        game->windows.front_window_id, game->engine.recovered.triWidth,
        game->engine.recovered.triHeight, game->engine.recovered.triWidthL);
    for (window = 18; window <= 19; ++window) {
        const PortableWindowRegistrySlot *slot = &game->registry->slots[window];
        const SimSetupRect *rect = window == 18 ?
            &game->session->setup_controls.mode_rect :
            &game->session->setup_controls.caste_rect;
        (void)fprintf(file, "%s{\"window_id\":%u,\"loaded\":%s,"
            "\"source_triangle_rect\":[%d,%d,%d,%d],\"objects\":[",
            window == 18 ? "" : ",", window << 8,
            slot->loaded ? "true" : "false", rect->left, rect->top,
            rect->right, rect->bottom);
        for (object = 0; slot->loaded && object < slot->window.count; ++object) {
            const PortableWindowObject *item = &slot->window.objects[object];
            (void)fprintf(file, "%s{\"object_id\":%u,\"type\":%u,"
                "\"flags\":%u,\"rect\":[%d,%d,%d,%d]}",
                object == 0 ? "" : ",", (window << 8) | object,
                item->type, item->flags, item->rect.left, item->rect.top,
                item->rect.right, item->rect.bottom);
        }
        (void)fprintf(file, "]}");
    }
    (void)fprintf(file, "]}\n");
    return fclose(file) == 0;
}
#endif

static int point_in_source_menu_bar(PortableLiveGame *game, int16_t x, int16_t y)
{
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[64];
    PortableMenuStatus status;
    size_t count = 0;
    if (game == NULL || !game->menu.loaded) return 0;
    status = portable_menu_build_draw_plan(&game->menu, 1,
        (PortableMenuRect){0, 0, LIVE_SCREEN_WIDTH, LIVE_SCREEN_HEIGHT},
        LIVE_SCREEN_WIDTH, 8, 14, 14, &layout, commands,
        sizeof(commands) / sizeof(commands[0]), &count);
    if (status != PORTABLE_MENU_OK) return 0;
    return x >= layout.bar_rect.left && x < layout.bar_rect.right &&
           y >= layout.bar_rect.top && y < layout.bar_rect.bottom;
}

static int enqueue_edit_hotbox(PortableLiveGame *game, int16_t x, int16_t y)
{
    PortableWindowRegistrySlot *slot;
    PortableWindowPoint point;
    SimRecoveredEvent *event;
    size_t tail;
    int hit;
    if (point_in_source_menu_bar(game, x, y)) {
        set_error(game, "source menu-bar mouse selection is not yet mapped");
        return 0;
    }
    if (game == NULL || !game->registry->slots[0].loaded ||
        !(game->windows.windows[0].flags & PORTABLE_WINDOW_OPEN) ||
        game->windows.front_window_id != 0)
        return 1;
    slot = &game->registry->slots[0];
    point.x = x;
    point.y = y;
    hit = portable_window_mouse_hit_test(&slot->window, point);
    if (hit < 0) return 1;
    if (hit != 4) {
        set_error(game, "selectable Edit-window object input is not yet mapped");
        return 0;
    }
    if (game->dos_keyboard_flags != 0) {
        set_error(game, "modified Edit object hotbox clicks are not yet mapped");
        return 0;
    }
    if (game->source_event_count >= LIVE_SOURCE_EVENT_CAPACITY) {
        set_error(game, "source Edit event queue capacity exceeded");
        return 0;
    }
    tail = (game->source_event_head + game->source_event_count) %
           LIVE_SOURCE_EVENT_CAPACITY;
    event = &game->source_events[tail];
    memset(event, 0, sizeof(*event));
    event->x4 = (int16_t)sim_timing_tick_count(&game->clock);
    event->modifiers = 0x0201; /* DOS INT 33h left-button press AX. */
    event->h = x;
    event->v = y;
    event->code = 4;
    event->xE = 0x0101;
    ++game->source_event_count;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    ++game->edit_hotbox_clicks;
#endif
    return 1;
}

static int reject_registered_right_hotbox(PortableLiveGame *game,
                                           int16_t x, int16_t y)
{
    PortableWindowRegistrySlot *slot;
    PortableWindowPoint point;
    if (point_in_source_menu_bar(game, x, y)) {
        set_error(game, "right-button source menu-bar input is not yet mapped");
        return 0;
    }
    if (game == NULL || !game->registry->slots[0].loaded ||
        !(game->windows.windows[0].flags & PORTABLE_WINDOW_OPEN) ||
        game->windows.front_window_id != 0)
        return 1;
    slot = &game->registry->slots[0];
    point.x = x;
    point.y = y;
    if (portable_window_mouse_hit_test(&slot->window, point) < 0) return 1;
    set_error(game, "right-button registered Edit hotbox input is not yet mapped");
    return 0;
}

static int pop_source_event(PortableLiveGame *game, SimRecoveredEvent *event)
{
    if (game == NULL || event == NULL || game->source_event_count == 0) return 0;
    *event = game->source_events[game->source_event_head];
    game->source_event_head = (game->source_event_head + 1) %
                              LIVE_SOURCE_EVENT_CAPACITY;
    --game->source_event_count;
    return 1;
}

static void coalesce_source_mouse_event(PortableLiveGame *game,
                                       SimRecoveredEvent *event)
{
    int32_t now = (int32_t)sim_timing_tick_count(&game->clock);
    if (event->code == game->previous_mouse_event.code &&
        (int32_t)((uint32_t)now - 10u) < game->previous_mouse_event_tick) {
        if (((uint16_t)(game->previous_mouse_event.modifiers ^
                        event->modifiers) & 0x0a00u) == 0) {
            event->modifiers = (int16_t)((uint16_t)event->modifiers & ~0x0a00u);
            if ((game->previous_mouse_event.modifiers & 0x0800) != 0)
                event->modifiers = (int16_t)((uint16_t)event->modifiers | 0x4000u);
            if ((game->previous_mouse_event.modifiers & 0x0200) != 0)
                event->modifiers = (int16_t)((uint16_t)event->modifiers | 0x2000u);
            game->previous_mouse_event_tick = -1;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
            ++game->edit_double_clicks;
#endif
            return;
        }
    }
    game->previous_mouse_event_tick = now;
    game->previous_mouse_event = *event;
}

static int pump_events_during_source_wait(PortableLiveGame *game,
                                          SimRecoveredEvent *source_event)
{
    HostEvent event;
    int polled;
    uint64_t now_ns = host_time_ns();
    if (now_ns < game->next_source_event_poll_ns) {
        if (pop_source_event(game, source_event)) return 1;
        host_wait_ms(1);
        return 0;
    }
    game->next_source_event_poll_ns = now_ns + 1000000ull;
    while ((polled = host_poll_event(game->host, &event)) > 0) {
        switch (event.kind) {
        case HOST_EVENT_QUIT:
            game->quit_requested = 1;
            break;
        case HOST_EVENT_MOUSE_MOVE:
            game->cursor_x = event.x;
            game->cursor_y = event.y;
            break;
        case HOST_EVENT_MOUSE_DOWN:
            if (event.button == 1 && !game->left_down) {
                game->cursor_x = event.x;
                game->cursor_y = event.y;
                game->left_down = 1;
                if (!enqueue_edit_hotbox(game, event.x, event.y)) return 0;
            } else if (event.button == 3 &&
                       !reject_registered_right_hotbox(game, event.x, event.y)) {
                return 0;
            }
            break;
        case HOST_EVENT_MOUSE_UP:
            if (event.button == 1) game->left_down = 0;
            game->cursor_x = event.x;
            game->cursor_y = event.y;
            break;
        case HOST_EVENT_KEY_DOWN:
        case HOST_EVENT_KEY_UP:
            /* Source root:m218D win_GetEvent consumes the event ring and
             * does not poll the BIOS keyboard. Defer these host commands
             * until processEdit returns instead of injecting them into its
             * Event stream or re-entering the active recovered call. */
            game->dos_keyboard_flags = event.modifiers;
            if ((event.key >> 8) == 0x1d)
                game->control_down = (event.modifiers & 4u) != 0;
            if (game->deferred_host_event_count >=
                    LIVE_DEFERRED_HOST_EVENT_CAPACITY) {
                set_error(game, "host event backlog exceeded during source input wait");
                return 0;
            }
            game->deferred_host_events[game->deferred_host_event_count++] = event;
            break;
        default:
            break;
        }
        if (pop_source_event(game, source_event)) return 1;
    }
    if (polled < 0) {
        set_error(game, "SDL event conversion failed during source input wait");
        return 0;
    }
    if (pop_source_event(game, source_event)) return 1;
    host_wait_ms(1);
    return 0;
}

static int dispatch_deferred_host_events(PortableLiveGame *game)
{
    size_t i;
    HostEvent events[LIVE_DEFERRED_HOST_EVENT_CAPACITY];
    size_t count = game->deferred_host_event_count;
    if (count == 0) return 1;
    memcpy(events, game->deferred_host_events, count * sizeof(events[0]));
    game->deferred_host_event_count = 0;
    for (i = 0; i < count; ++i) {
        if (!portable_live_game_event(game, &events[i])) return 0;
    }
    return 1;
}

static int process_source_edit_event(PortableLiveGame *game,
                                     SimRecoveredEvent *event)
{
    SimRecoveredEngineStatus status;
    if (game == NULL || event == NULL || game->source_wait_active) return 0;
    coalesce_source_mouse_event(game, event);
    status = sim_recovered_engine_process_edit_event(&game->engine, event,
                                                      NULL);
    if (status != SIM_RECOVERED_ENGINE_OK) {
        set_error(game, game->engine.failed_service != NULL ?
            game->engine.failed_service :
            sim_recovered_engine_status_string(status));
        game->faulted = 1;
        return 0;
    }
    game->dirty = 1;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    ++game->edit_events_delivered;
    game->edit_goal_active_after_event = game->engine.recovered.fd_50F6_0AA0;
    game->edit_goal_mode_after_event = game->engine.recovered.fd_50F6_0A8E;
    game->edit_goal_x_after_event = game->engine.recovered.fd_50F6_0AD6;
    game->edit_goal_y_after_event = game->engine.recovered.fd_50F6_0AE8;
    game->edit_goal_plane_after_event = game->engine.recovered.fd_50F6_0AF8;
    game->edit_left_down_after_event = game->left_down;
#endif
    if (!dispatch_deferred_host_events(game)) return 0;
    return redraw(game);
}

static int advance_clock_to(PortableLiveGame *game, uint64_t now_ns)
{
    uint64_t elapsed;
    if (!game->clock_started) {
        game->last_now_ns = now_ns;
        game->clock_started = 1;
        return 1;
    }
    elapsed = now_ns >= game->last_now_ns ? now_ns - game->last_now_ns : 0;
    if (sim_timing_advance_nanoseconds(&game->clock, elapsed) != SIM_TIMING_OK)
        return 0;
    if (now_ns >= game->last_now_ns) game->last_now_ns = now_ns;
    return 1;
}

static int tick_count_provider(void *context, int32_t *value)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    if (game == NULL || value == NULL ||
        !advance_clock_to(game, host_time_ns())) return 0;
    *value = (int32_t)sim_timing_tick_count(&game->clock);
    return 1;
}

static uint32_t modal_tick_count_provider(void *context)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    if (game == NULL || !advance_clock_to(game, host_time_ns())) return 0;
    return sim_timing_tick_count(&game->clock);
}

static int32_t ribbon_tick_provider(void *context)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    if (game == NULL || !advance_clock_to(game, host_time_ns())) {
        set_error(game, "source ribbon TickCount provider failed");
        return 0;
    }
    return (int32_t)sim_timing_tick_count(&game->clock);
}

static int song_done_provider(void *context)
{
    (void)context;
    /* The recovered adapter disables the audio driver, so the exact source
     * audio gate never consults this provider. Keep a deterministic valid
     * callback for the mandatory engine interface. */
    return 1;
}

static int host_query(void *context, SimRecoveredQuery query,
                      const uintptr_t *arguments, uint8_t argument_count,
                      int32_t *value)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    uint16_t id;
    uint16_t index;
    if (game == NULL || value == NULL) return 0;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    if (query > 0 && query <= SIM_RECOVERED_QUERY_BUTTON)
        ++game->query_calls[query];
#endif
    *value = 0;
    switch (query) {
    case SIM_RECOVERED_QUERY_WINDOW_OPEN:
        if (arguments == NULL || argument_count != 1) return 0;
        id = (uint16_t)arguments[0];
        index = id >> 8;
        if ((id & 0xffu) != 0 || index >= PORTABLE_WINDOW_REGISTRY_SLOTS ||
            index >= game->registry->window_count)
            return 0;
        *value = game->registry->slots[index].loaded &&
            (game->windows.windows[index].flags & PORTABLE_WINDOW_OPEN) != 0;
        return 1;
    case SIM_RECOVERED_QUERY_WINDOW_IN_FRONT:
        if (arguments == NULL || argument_count != 1) return 0;
        *value = game->windows.front_window_id == (int16_t)arguments[0];
        return 1;
    case SIM_RECOVERED_QUERY_WINDOW_EVENTS:
        /* SDL keyboard commands are consumed by the source key-command
         * projection; no unverified SDL-to-DOS window-event conversion is
         * inserted into the original window queue. */
        if (argument_count != 0) return 0;
        *value = 0;
        return 1;
    case SIM_RECOVERED_QUERY_STILL_DOWN:
        if (argument_count != 0) return 0;
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
        if (game->history_input_active) {
            SimSetupPoint point;
            if (!control_pointer_poll(game, &point)) return 0;
        }
#endif
        *value = game->left_down != 0;
        return 1;
    case SIM_RECOVERED_QUERY_BUTTON:
        if (argument_count != 0) return 0;
        *value = game->left_down != 0;
        return 1;
    case SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS:
        if (argument_count != 0) return 0;
        *value = game->dos_keyboard_flags;
        return 1;
    case SIM_RECOVERED_QUERY_DRIVER_COLOR:
        if (arguments == NULL || argument_count != 1 || arguments[0] > UINT16_MAX ||
            game->registry->profile_id != 0) return 0;
        /* The 640x350 EGA driver retains g_41C0's identity table. Only the
         * historical 320x200 CGA/low-resolution initializers replace it.
         * f_1B4E_000D preserves the word's upper bits and maps its low nibble. */
        *value = (int32_t)arguments[0];
        return 1;
    case SIM_RECOVERED_QUERY_DIALOG_ABORT_OR_CONTINUE:
        if (argument_count != 0) return 0;
        set_error(game, "source DialogAbortOrCont state is not modeled");
        return 0;
    case SIM_RECOVERED_QUERY_GET_EVENT:
        if (arguments == NULL || argument_count != 1 || arguments[0] == 0)
            return 0;
        {
            SimRecoveredEvent event;
            int available = pop_source_event(game, &event);
            if (!available) {
                game->source_wait_active = 1;
                available = pump_events_during_source_wait(game, &event);
                game->source_wait_active = 0;
            }
            if (available < 0) return 0;
            if (available) {
                coalesce_source_mouse_event(game, &event);
                memcpy((void *)arguments[0], &event, sizeof(event));
                *value = 1;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
                ++game->edit_events_delivered;
#endif
            }
        }
        return 1;
    case SIM_RECOVERED_QUERY_GET_OBJECT_RECT: {
        PortableWindowRect rect;
        int16_t *out;
        if (arguments == NULL || argument_count != 2) return 0;
        out = (int16_t *)arguments[1];
        if (out == NULL || portable_window_registry_get_object_rect(
                game->registry, (uint16_t)arguments[0], &rect) !=
                PORTABLE_WINDOW_REGISTRY_OK)
            return 0;
        _Static_assert(sizeof(PortableWindowRect) == 4u * sizeof(int16_t),
                       "source Rect must remain four words");
        memcpy(out, &rect, sizeof(rect));
        return 1;
    }
    default:
        return 0;
    }
}

static int run_picture_modal(PortableLiveGame *game,
                             const SimRecoveredEffect *effect)
{
    PortablePictureDialogRequest request;
    PortablePictureModalStatus status;
    if (game == NULL || effect == NULL || game->session == NULL ||
        game->host == NULL || game->palette == NULL || game->fonts == NULL ||
        game->renderer == NULL)
        return 0;
    request.picture_id = (int16_t)(intptr_t)effect->arguments[0];
    request.string_object_id = (int16_t)(intptr_t)effect->arguments[1];
    request.force = (uint8_t)(effect->arguments[2] != 0);
    request.strings_enabled =
        game->engine.recovered.fd_3D57_07A8[3] != 0;
    request.screen_width = LIVE_SCREEN_WIDTH;
    request.screen_height = LIVE_SCREEN_HEIGHT;
    status = portable_picture_modal_run_clocked(
        game->host, game->palette, game->fonts, game->renderer,
        &game->session->shared_database, game->session->window_database,
        request, modal_tick_count_provider, game, &game->quit_requested);
    if (status == PORTABLE_PICTURE_MODAL_SUPPRESSED) return 1;
    if (status == PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY ||
        status == PORTABLE_PICTURE_MODAL_DISMISSED_BY_WINDOW_CLICK ||
        status == PORTABLE_PICTURE_MODAL_DISMISSED_BY_SOURCE_TIMEOUT) {
        game->dirty = 1;
        return 1;
    }
    set_error(game, portable_picture_modal_status_string(status));
    return 0;
}

static int apply_ribbon_message(PortableLiveGame *game,
                                const SimRecoveredEffect *effect)
{
    PortableRibbonEditResult result;
    PortableRibbonStatus status;
    const void *message;
    int32_t duration;
    int16_t mode;
    if (game == NULL || effect == NULL) return 0;
    message = (const void *)effect->arguments[0];
    duration = (int32_t)(intptr_t)effect->arguments[1];
    mode = (int16_t)(intptr_t)effect->arguments[2];
    status = portable_ribbon_edit_message(&game->ribbons,
        &game->session->advice, message, duration, mode,
        game->engine.recovered.fd_3D57_07A8[4] != 0,
        ribbon_tick_provider, game, &result);
    if (status != PORTABLE_RIBBON_OK) {
        set_error(game, portable_ribbon_status_string(status));
        return 0;
    }
    if (result.applied && (result.edit_pointer_changed ||
                           result.map_pointer_changed || message == NULL))
        game->dirty = 1;
    return 1;
}

static int host_effect(void *context, const SimRecoveredEffect *effect)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    if (game == NULL || effect == NULL) return 0;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    if (effect->kind > 0 && effect->kind <= SIM_RECOVERED_EFFECT_GRAPHICS_LINE)
        ++game->effect_calls[effect->kind];
#endif
    switch (effect->kind) {
    case SIM_RECOVERED_EFFECT_MAP_CELL_INVALIDATE:
        if ((int16_t)(intptr_t)effect->arguments[0] == game->session->world.map_plane)
            game->dirty = 1;
        return 1;
    case SIM_RECOVERED_EFFECT_NEST_MAP_INVALIDATE:
        game->dirty = 1;
        return 1;
    case SIM_RECOVERED_EFFECT_PICTURE_STRING_DIALOG:
        return run_picture_modal(game, effect);
    case SIM_RECOVERED_EFFECT_EDIT_MESSAGE:
        return apply_ribbon_message(game, effect);
    case SIM_RECOVERED_EFFECT_DEFAULT_WIND_PROMPT:
        return apply_ribbon_message(game, effect);
    case SIM_RECOVERED_EFFECT_ALARM_SELECTION:
        set_error(game, "source alarm-selection UI is not available");
        return 0;
    case SIM_RECOVERED_EFFECT_WINDOW_OPERATION:
        if ((SimRecoveredWindowOperation)(intptr_t)effect->arguments[0] ==
                SIM_RECOVERED_WINDOW_UPDATE_EDIT)
            return redraw_snapshot_edit(game);
        return apply_window_object_operation(game, effect);
    default:
        set_error(game, "unsupported recovered host effect");
        return 0;
    }
}

static int refresh_titles(PortableLiveGame *game, const SimGameWorld *world)
{
    PortableWindowTitleScene scene;
    PortableWindowTitlesStatus status;
    if (game == NULL || game->titles == NULL || game->title_projection == NULL)
        return 0;
    scene.scenario = world->scenario;
    scene.map_mode = world->selected_map_plane;
    scene.yard_mode = world->yard_mode;
    scene.edit_window_open =
        (game->windows.windows[0].flags & PORTABLE_WINDOW_OPEN) != 0;
    scene.map_window_open =
        (game->windows.windows[1].flags & PORTABLE_WINDOW_OPEN) != 0;
    scene.yard_window_open =
        (game->windows.windows[0x19].flags & PORTABLE_WINDOW_OPEN) != 0;
    status = portable_window_titles_update(game->titles, &scene,
                                            game->title_projection);
    if (status != PORTABLE_WINDOW_TITLES_OK) {
        set_error(game, portable_window_titles_status_string(status));
        return 0;
    }
    game->renderer->resolve_text = portable_window_titles_resolve_text;
    game->renderer->text_context = game->title_projection;
    return 1;
}

static int draw_open_window(PortableLiveGame *game, uint16_t index)
{
    PortableWindowRegistrySlot *slot;
    PortableWindowRegistryStatus status;
    int16_t no_args[4] = { 0, 0, 0, 0 };
    if (index >= game->registry->window_count ||
        !game->registry->slots[index].loaded) {
        set_error(game, "requested live window is not loaded");
        return 0;
    }
    slot = &game->registry->slots[index];
    if (!slot->recalculated) {
        status = portable_window_registry_recalculate(game->registry,
                    (int16_t)index, no_args);
        if (status != PORTABLE_WINDOW_REGISTRY_OK) {
            set_error(game, portable_window_registry_status_string(status));
            return 0;
        }
    }
    if (portable_window_draw_native(&slot->window, game->renderer) !=
        PORTABLE_RENDER_OK) {
        set_error(game, "open window contains an unsupported render object");
        return 0;
    }
    return 1;
}

static int32_t rect_min(int32_t a, int32_t b) { return a < b ? a : b; }
static int32_t rect_max(int32_t a, int32_t b) { return a > b ? a : b; }

static int subtract_exclusion(PortableRect *regions, size_t *region_count,
                              size_t capacity, PortableRect exclusion)
{
    PortableRect next[16];
    size_t next_count = 0;
    size_t i;
    if (regions == NULL || region_count == NULL || capacity > 16) return 0;
    for (i = 0; i < *region_count; ++i) {
        PortableRect source = regions[i];
        PortableRect hit = {
            rect_max(source.left, exclusion.left),
            rect_max(source.top, exclusion.top),
            rect_min(source.right, exclusion.right),
            rect_min(source.bottom, exclusion.bottom)
        };
        if (hit.left >= hit.right || hit.top >= hit.bottom) {
            if (next_count == capacity) return 0;
            next[next_count++] = source;
            continue;
        }
#define APPEND_REGION(l, t, r, b) do { \
    if ((l) < (r) && (t) < (b)) { \
        if (next_count == capacity) return 0; \
        next[next_count++] = (PortableRect){(l), (t), (r), (b)}; \
    } \
} while (0)
        APPEND_REGION(source.left, source.top, source.right, hit.top);
        APPEND_REGION(source.left, hit.bottom, source.right, source.bottom);
        APPEND_REGION(source.left, hit.top, hit.left, hit.bottom);
        APPEND_REGION(hit.right, hit.top, source.right, hit.bottom);
#undef APPEND_REGION
    }
    memcpy(regions, next, next_count * sizeof(*regions));
    *region_count = next_count;
    return 1;
}

static int render_game_view(PortableLiveGame *game,
                            const SimSession *scene_session,
                            const PortableGameView *view,
                            PortableGameViewRenderResult *aggregate,
                            const PortableRect *exclusions,
                            size_t exclusion_count)
{
    PortableFramebuffer *fb = game->renderer->framebuffer;
    PortableRect saved_clip = fb->clip;
    PortableRect regions[16];
    size_t region_count = 1, i;
    memset(aggregate, 0, sizeof(*aggregate));
    regions[0] = saved_clip;
    for (i = 0; i < exclusion_count; ++i) {
        if (!subtract_exclusion(regions, &region_count,
                                sizeof(regions) / sizeof(regions[0]),
                                exclusions[i])) {
            portable_framebuffer_set_clip(fb, saved_clip);
            set_error(game, "source ribbon clip exclusions exceed renderer capacity");
            return 0;
        }
    }
    for (i = 0; i < region_count; ++i) {
        PortableGameViewRenderResult one;
        portable_framebuffer_set_clip(fb, regions[i]);
        if (portable_game_view_render(&scene_session->world, view,
                &scene_session->tileset, fb, &one) != PORTABLE_GAME_VIEW_OK) {
            portable_framebuffer_set_clip(fb, saved_clip);
            set_error(game, "source game viewport render failed");
            return 0;
        }
        aggregate->cells_drawn += one.cells_drawn;
        aggregate->cells_with_life += one.cells_with_life;
    }
    portable_framebuffer_set_clip(fb, saved_clip);
    return 1;
}

static PortableRect rect_intersection(PortableRect a, PortableRect b)
{
    PortableRect result = {
        a.left > b.left ? a.left : b.left,
        a.top > b.top ? a.top : b.top,
        a.right < b.right ? a.right : b.right,
        a.bottom < b.bottom ? a.bottom : b.bottom
    };
    if (result.right < result.left) result.right = result.left;
    if (result.bottom < result.top) result.bottom = result.top;
    return result;
}

static int draw_map_overview(PortableLiveGame *game,
                             const SimSession *scene_session)
{
    PortableOverviewViewInput input;
    PortableOverviewView view;
    PortableOverviewViewStatus status;
    PortableFramebuffer *fb;
    PortableRect saved_clip, window_clip;
    const PortableWindowRect *window_rect;
    if (game == NULL || scene_session == NULL || game->renderer == NULL ||
        game->renderer->framebuffer == NULL) return 0;
    input.world = &scene_session->world;
    input.map_mode = scene_session->world.selected_map_plane;
    input.hardware_profile = game->registry->profile_id;
    input.map_window_open =
        (game->windows.windows[1].flags & PORTABLE_WINDOW_OPEN) != 0;
    if (!input.map_window_open) return 1;
    status = portable_overview_view_prepare(game->registry, &input, &view);
    if (status != PORTABLE_OVERVIEW_VIEW_OK) {
        set_error(game, portable_overview_view_status_string(status));
        return 0;
    }
    fb = game->renderer->framebuffer;
    saved_clip = fb->clip;
    status = portable_overview_view_render(&view, fb);
    if (status != PORTABLE_OVERVIEW_VIEW_OK) {
        portable_framebuffer_set_clip(fb, saved_clip);
        set_error(game, portable_overview_view_status_string(status));
        return 0;
    }
    window_rect = &game->registry->slots[1].window.rect;
    window_clip = (PortableRect){window_rect->left, window_rect->top,
                                 window_rect->right, window_rect->bottom};
    portable_framebuffer_set_clip(fb, rect_intersection(saved_clip, window_clip));
    status = portable_overview_view_render_cursor(&view, fb);
    portable_framebuffer_set_clip(fb, saved_clip);
    if (status != PORTABLE_OVERVIEW_VIEW_OK) {
        set_error(game, portable_overview_view_status_string(status));
        return 0;
    }
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    ++game->overview_render_calls;
    game->overview_mode = input.map_mode;
    game->overview_image_rect[0] = view.image_rect.left;
    game->overview_image_rect[1] = view.image_rect.top;
    game->overview_image_rect[2] = view.image_rect.right;
    game->overview_image_rect[3] = view.image_rect.bottom;
    game->overview_cursor_rect[0] = view.cursor_rect.left;
    game->overview_cursor_rect[1] = view.cursor_rect.top;
    game->overview_cursor_rect[2] = view.cursor_rect.right;
    game->overview_cursor_rect[3] = view.cursor_rect.bottom;
#endif
    return 1;
}

static int draw_control_window(PortableLiveGame *game, SimSession *scene_session,
                                SimSetupControlKind kind)
{
    SimControlRenderBinding binding;
    SimControlRecoveredVisualState visual;
    RecoveredState *source;
    unsigned index = (unsigned)kind;
    if (scene_session->controls[index].animation_resource !=
            game->session->controls[index].animation_resource ||
        scene_session->controls[index].animation_resource != NULL) {
        set_error(game, "control animation has no current host resource resolver");
        return 0;
    }
    source = malloc(sizeof(*source));
    if (source == NULL || !sim_recovered_engine_snapshot(&game->engine, source)) {
        free(source);
        set_error(game, "control render has no current source-state snapshot");
        return 0;
    }
    visual.mode_percent = game->mode_percent;
    visual.caste_percent = game->caste_percent;
    memcpy(visual.mode_population, source->fd_50F6_0B12,
           sizeof visual.mode_population);
    free(source);
    if (sim_control_render_binding_from_session(scene_session, game->renderer,
            kind, 3, &visual, NULL, NULL, &binding) != SIM_CONTROL_SESSION_INPUT_OK ||
        sim_control_render_raster(&binding.input, &binding.raster) !=
            PORTABLE_RENDER_OK) {
        set_error(game, "source control-window raster failed");
        return 0;
    }
    return 1;
}

#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
static int prepare_history_resources(PortableLiveGame *game)
{
    PortableWindowRect rect;
    PortableHistoryStatus status;
    if (!game->history_resources.ready) {
        status = portable_history_active_resources_load(&game->history_resources,
            &game->session->shared_database, game->registry, game->renderer);
        if (status != PORTABLE_HISTORY_OK) {
            set_error(game, portable_history_status_string(status));
            return 0;
        }
    }
    if (portable_window_registry_get_object_rect(game->registry, 0x150e, &rect) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        portable_history_active_resources_set_rect(&game->history_resources,
            &(PortableHistoryRect){rect.left, rect.top, rect.right, rect.bottom}) !=
            PORTABLE_HISTORY_OK) {
        set_error(game, "source History graph geometry is unavailable");
        return 0;
    }
    return 1;
}

static int draw_history_window(PortableLiveGame *game, const SimSession *scene_session)
{
    PortableHistoryUiSnapshot ui;
    PortableHistoryWindowInput input;
    PortableHistoryProviders providers;
    PortableHistoryRasterProviders raster;
    PortableHistoryCommand *commands;
    PortableHistoryStatus status;
    PortableFramebuffer *fb = game->renderer->framebuffer;
    PortableRect saved_clip = fb->clip;
    const PortableWindowRect *window_rect = &game->registry->slots[0x15].window.rect;
    int16_t shown_count;
    size_t command_count = 0;
    const size_t capacity = PORTABLE_HISTORY_MAX_COMMANDS * 4u + 1u;
    if (!prepare_history_resources(game) ||
        !sim_recovered_engine_history_ui_snapshot(&game->engine, &ui, &shown_count)) {
        set_error(game, "source History UI snapshot is unavailable");
        return 0;
    }
    status = portable_history_bind_window(&input, scene_session->setup_state.history_series,
        scene_session->setup_state.history_start, scene_session->setup_state.graph_selection,
        3, &ui, &game->history_resources.labels);
    if (status != PORTABLE_HISTORY_OK) {
        set_error(game, portable_history_status_string(status));
        return 0;
    }
    commands = malloc(capacity * sizeof(*commands));
    if (commands == NULL) {
        set_error(game, "could not allocate History rendering commands");
        return 0;
    }
    portable_history_active_providers(&game->history_resources, &providers);
    portable_history_active_raster_providers(&game->history_resources, fb, &raster);
    status = portable_history_render_window(&input, &providers, commands, capacity,
                                            &command_count);
    portable_framebuffer_set_clip(fb, rect_intersection(saved_clip,
        (PortableRect){window_rect->left, window_rect->top, window_rect->right, window_rect->bottom}));
    if (status == PORTABLE_HISTORY_OK)
        status = portable_history_rasterize(commands, command_count, &raster);
    portable_framebuffer_set_clip(fb, saved_clip);
    free(commands);
    if (status != PORTABLE_HISTORY_OK) {
        set_error(game, portable_history_status_string(status));
        return 0;
    }
    return 1;
}

static int draw_history_graph_effect(PortableLiveGame *game, int16_t graph,
                                     int16_t hilite, int16_t slot)
{
    RecoveredState snapshot;
    PortableHistoryUiSnapshot ui;
    PortableHistoryInput input;
    PortableHistoryProviders providers;
    PortableHistoryRasterProviders raster;
    PortableHistoryCommand commands[PORTABLE_HISTORY_MAX_COMMANDS];
    PortableHistoryStatus status;
    PortableFramebuffer *fb = game->renderer->framebuffer;
    PortableRect saved_clip = fb->clip;
    const PortableWindowRect *window_rect = &game->registry->slots[0x15].window.rect;
    int16_t shown_count;
    size_t command_count = 0;
    if (game->source_clip_window != 0x1500 || !prepare_history_resources(game) ||
        !sim_recovered_engine_snapshot(&game->engine, &snapshot) ||
        sim_session_from_recovered_state(game->snapshot_session, &snapshot) != SIM_RECOVERED_BRIDGE_OK ||
        !sim_recovered_engine_history_ui_snapshot(&game->engine, &ui, &shown_count)) {
        set_error(game, "source History drawing context is unavailable");
        return 0;
    }
    status = portable_history_bind_session(&input,
        game->snapshot_session->setup_state.history_series,
        game->snapshot_session->setup_state.history_start,
        game->snapshot_session->setup_state.graph_selection,
        graph, hilite, slot, &ui, &game->history_resources.labels);
    portable_history_active_providers(&game->history_resources, &providers);
    portable_history_active_raster_providers(&game->history_resources, fb, &raster);
    if (status == PORTABLE_HISTORY_OK)
        status = portable_history_render_graph(&input, &providers, commands,
            PORTABLE_HISTORY_MAX_COMMANDS, &command_count);
    /* Background updates are presented by the complete z-order pass. Keep
     * foreground highlighting synchronous across the source StillDown wait. */
    if (status == PORTABLE_HISTORY_OK && game->windows.front_window_id == 0x1500) {
        portable_framebuffer_set_clip(fb, rect_intersection(saved_clip,
            (PortableRect){window_rect->left, window_rect->top, window_rect->right, window_rect->bottom}));
        status = portable_history_rasterize(commands, command_count, &raster);
        portable_framebuffer_set_clip(fb, saved_clip);
        if (status == PORTABLE_HISTORY_OK &&
            !host_present(game->host, fb->pixels, fb->stride, game->host_palette)) {
            set_error(game, "SDL History graph presentation failed");
            return 0;
        }
    }
    if (status != PORTABLE_HISTORY_OK) {
        set_error(game, portable_history_status_string(status));
        return 0;
    }
    game->dirty = 1;
    game->frame_pending = 1;
    return 1;
}
#endif

static int redraw_scene(PortableLiveGame *game, SimSession *scene_session)
{
    PortableGameViewState state;
    PortableGameView view;
    PortableGameViewRenderResult result;
    PortableGameViewStatus status;
    PortableFramebuffer *fb;
    int order_index;
    if (game == NULL || scene_session == NULL || game->renderer == NULL ||
        game->renderer->framebuffer == NULL)
        return 0;
    fb = game->renderer->framebuffer;
    if (fb->pixels == NULL || fb->width != LIVE_SCREEN_WIDTH ||
        fb->height != LIVE_SCREEN_HEIGHT || fb->stride < (size_t)fb->width) {
        set_error(game, "live framebuffer must be 640x350 indexed EGA");
        return 0;
    }
    if (!refresh_titles(game, &scene_session->world)) return 0;
    state.ega_profile = game->registry->profile_id;
    state.pheromone_mode = scene_session->world.source_state_07be;
    state.animation_base = scene_session->world.source_state_049a;
    state.queen_frame = scene_session->world.me_direction;
    state.young_frame = 0;
    state.caste_frame = scene_session->world.me_type;
    status = portable_game_view_at(game->registry, &state,
                 scene_session->world.map_plane,
                 scene_session->world.map_view_x,
                 scene_session->world.map_view_y, &view);
    if (status != PORTABLE_GAME_VIEW_OK) {
        set_error(game, portable_game_view_status_string(status));
        return 0;
    }
    memset(fb->pixels, 0, (size_t)fb->stride * fb->height);
    portable_framebuffer_set_clip(fb, (PortableRect){0, 0, fb->width, fb->height});

    /* The source order list is front-to-back. Paint it back-to-front so the
     * actual front window remains visible; the map cells are the Edit
     * viewport contents and are clipped over its base surface afterwards. */
    for (order_index = (int)game->windows.open_count - 1;
         order_index >= 0; --order_index) {
        uint16_t index = (uint16_t)game->windows.order[order_index] >> 8;
        if (!draw_open_window(game, index)) return 0;
        if (index == 1 && !draw_map_overview(game, scene_session)) return 0;
        if (index == 0 && !render_game_view(game, scene_session, &view,
                                           &result, NULL, 0)) return 0;
        if (index == 0x12 && !draw_control_window(game, scene_session,
                                                SIM_SETUP_MODE_CONTROL)) return 0;
        if (index == 0x13 && !draw_control_window(game, scene_session,
                                                SIM_SETUP_CASTE_CONTROL)) return 0;
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
        if (index == 0x15 && !draw_history_window(game, scene_session)) return 0;
#endif
        /* Paint each ribbon with its owning window. Front windows then cover
         * both the viewport and its ribbon during the same z-order pass. */
        if (index == 0 || index == 1 || index == 0x19) {
            PortableRibbonTarget target = index == 0
                ? PORTABLE_RIBBON_EDIT_SURFACE
                : index == 1 ? PORTABLE_RIBBON_MAP : PORTABLE_RIBBON_YARD;
            PortableRibbonRenderResult ribbon_result;
            int visible = 1;
            if (target == PORTABLE_RIBBON_YARD &&
                scene_session->world.queens_black <= 1)
                visible = 0;
            PortableRibbonStatus ribbon_status = portable_ribbon_render_current(
                &game->ribbons, &scene_session->advice, target,
                game->registry, game->renderer, visible,
                ribbon_tick_provider, game, &ribbon_result);
            if (ribbon_status != PORTABLE_RIBBON_OK) {
                set_error(game, portable_ribbon_status_string(ribbon_status));
                return 0;
            }
            portable_ribbon_clear_dirty(&game->ribbons, target);
        }
    }
    if (game->menu.loaded) {
        PortableMenuRasterColors colors;
        PortableMenuLayout layout;
        PortableMenuDrawCommand commands[64];
        size_t command_count = 0;
        PortableRenderStatus render_status;
        PortableMenuStatus menu_status;
        if (game->registry->profile_id != 0 || game->renderer->bios_fonts == NULL) {
            set_error(game, "menu bar raster is only verified for EGA profile 0");
            return 0;
        }
        if (portable_menu_raster_colors_for_width(LIVE_SCREEN_WIDTH, &colors) !=
                PORTABLE_RENDER_OK) {
            set_error(game, "source menu raster colors could not be selected");
            return 0;
        }
        menu_status = portable_menu_build_draw_plan(&game->menu, 1,
            (PortableMenuRect){0, 0, LIVE_SCREEN_WIDTH, LIVE_SCREEN_HEIGHT},
            LIVE_SCREEN_WIDTH, 8, 14, 14, &layout, commands,
            sizeof(commands) / sizeof(commands[0]), &command_count);
        if (menu_status != PORTABLE_MENU_OK) {
            set_error(game, portable_menu_status_string(menu_status));
            return 0;
        }
        portable_framebuffer_set_clip(fb,
            (PortableRect){0, 0, fb->width, fb->height});
        render_status = portable_menu_render_draw_plan(fb,
            &game->renderer->bios_fonts->font_8x14, &colors,
            commands, command_count);
        if (render_status != PORTABLE_RENDER_OK) {
            set_error(game, "source menu draw plan is unsupported by the raster renderer");
            return 0;
        }
    }
    portable_framebuffer_set_clip(fb, (PortableRect){0, 0, fb->width, fb->height});
    game->dirty = 0;
    game->frame_pending = 1;
    return 1;
}

static int redraw(PortableLiveGame *game)
{
    return game != NULL ? redraw_scene(game, game->session) : 0;
}

/* A modal consumes release edges itself. Reconcile observed host input before
 * returning to processEdit, without discarding keys that remain held. */
static int reconcile_modal_input(PortableLiveGame *game)
{
    HostInputState state;
    size_t i = 0;
    if (!host_get_input_state(game->host, &state)) {
        set_error(game, "could not reconcile input after source modal");
        return 0;
    }
    game->cursor_x = state.x;
    game->cursor_y = state.y;
    game->left_down = state.left_button_down;
    game->dos_keyboard_flags = state.dos_modifiers;
    game->control_down = (state.dos_modifiers & 4u) != 0;
    while (i < game->held_key_count) {
        int down;
        uint8_t scan = (uint8_t)(game->held_keys[i].key >> 8);
        if (!host_is_dos_scan_down(game->host, scan, &down)) {
            set_error(game, "could not reconcile held key after source modal");
            return 0;
        }
        if (down) {
            game->held_keys[i].modifiers = state.dos_modifiers;
            ++i;
        } else {
            game->held_keys[i] = game->held_keys[--game->held_key_count];
        }
    }
    return 1;
}

static int run_source_menu(PortableLiveGame *game, int16_t x, int16_t y)
{
    PortableMenuRasterColors colors;
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[64];
    PortableMenuModalRequest request;
    PortableMenuModalResult result;
    PortableMenuModalStatus status;
    PortableFramebuffer *fb = game->renderer->framebuffer;
    size_t count = 0;
    int title;
    if (game->registry->profile_id != 0 || game->renderer->bios_fonts == NULL ||
        portable_menu_raster_colors_for_width(LIVE_SCREEN_WIDTH, &colors) !=
            PORTABLE_RENDER_OK ||
        portable_menu_build_draw_plan(&game->menu, 1,
            (PortableMenuRect){0, 0, LIVE_SCREEN_WIDTH, LIVE_SCREEN_HEIGHT},
            LIVE_SCREEN_WIDTH, 8, 14, 14, &layout, commands,
            sizeof(commands) / sizeof(commands[0]), &count) != PORTABLE_MENU_OK) {
        set_error(game, "source menu layout is unavailable");
        return 0;
    }
    title = portable_menu_title_hit(&game->menu, &layout, x, y);
    if (title < 0) return 1;
    memset(&request, 0, sizeof(request));
    request.menu = &game->menu;
    request.layout = &layout;
    request.framebuffer = fb;
    request.font = &game->renderer->bios_fonts->font_8x14;
    request.host_palette = game->host_palette;
    request.screen_width = LIVE_SCREEN_WIDTH;
    request.screen_height = LIVE_SCREEN_HEIGHT;
    request.line_height = 14;
    request.char_width = 8;
    request.source_g5fea = 7;
    request.source_g5fec = 14;
    request.source_g5fee = 12;
    request.quit_flag = &game->quit_requested;
    request.initial_x = x;
    request.initial_y = y;
    request.initial_left_button_down = 1;
    for (;;) {
        request.menu_index = (size_t)title;
        if (!redraw(game) || portable_menu_render_active_title(fb,
                request.font, &colors, &game->menu, &layout,
                request.menu_index) != PORTABLE_RENDER_OK) {
            set_error(game, "source active menu title could not be rendered");
            return 0;
        }
        status = portable_menu_modal_run(game->host, &request, &result);
        if (!reconcile_modal_input(game)) return 0;
        if (status != PORTABLE_MENU_MODAL_PHYSICAL_TITLE_EVENT) break;
        if (!result.physical_title_index_valid) {
            set_error(game, "menu title replacement has no title identity");
            return 0;
        }
        /* Host title replacement is an explicit host boundary; it does not
         * synthesize the DOS window event's unknown xE value. */
        title = result.physical_title_index;
        request.initial_x = result.physical_title_x;
        request.initial_y = result.physical_title_y;
        request.initial_left_button_down = game->left_down;
    }
    game->scheduler.initialized = 0;
    if (status == PORTABLE_MENU_MODAL_COMMAND) {
        SimRecoveredEngineStatus action_status =
            sim_recovered_engine_proc_menu_command(&game->engine,
                                                  (uint16_t)result.command_id);
        if (action_status != SIM_RECOVERED_ENGINE_OK) {
            set_error(game, game->engine.failed_service != NULL ?
                game->engine.failed_service :
                sim_recovered_engine_status_string(action_status));
            return 0;
        }
        if (!reconcile_modal_input(game)) return 0;
        switch (game->engine.recovered.fd_55B3_2CBC) {
        case 4: set_error(game, "source LoadGame host file service is unavailable"); return 0;
        case 5: set_error(game, "source SaveGame host file service is unavailable"); return 0;
        case 6: set_error(game, "source SaveAs host file service is unavailable"); return 0;
        case 8: set_error(game, "source MenuQuit continuation is unavailable"); return 0;
        default: break;
        }
    } else if (status != PORTABLE_MENU_MODAL_RETURNED &&
               status != PORTABLE_MENU_MODAL_QUIT) {
        set_error(game, portable_menu_modal_status_string(status));
        return 0;
    }
    return redraw(game);
}

typedef struct LiveEndGameBinding {
    PortableLiveGame *game;
    PortableEndGameView *view;
} LiveEndGameBinding;

static int end_game_present(PortableLiveGame *game,
                            const PortableEndGameView *view)
{
    PortableFramebuffer *fb;
    if (game == NULL || view == NULL || game->renderer == NULL ||
        game->renderer->framebuffer == NULL || game->host == NULL)
        return 0;
    if (portable_end_game_view_render(view, game->registry, &game->windows,
            game->fonts, game->renderer) != PORTABLE_END_GAME_VIEW_OK) {
        set_error(game, "source EndGame window render failed");
        return 0;
    }
    fb = game->renderer->framebuffer;
    if (!host_present(game->host, fb->pixels, fb->stride, game->host_palette)) {
        set_error(game, "SDL presentation failed during source EndGame window");
        return 0;
    }
    game->frame_pending = 0;
    ++game->end_game_rendered_frames;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    {
        const char *frame_path = getenv("SIMANT_LIVE_END_GAME_FRAME_REPORT");
        if (frame_path != NULL && frame_path[0] != '\0')
            game->end_game_modal_frame_saved =
                (uint8_t)host_save_frame(game->host, frame_path);
    }
#endif
#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
    defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
    if (live_test_scenario_202_enabled()) {
        const char *ready_path = getenv("SIMANT_LIVE_ENDGAME_READY");
        if (ready_path != NULL && ready_path[0] != '\0') {
            FILE *ready = fopen(ready_path, "wb");
            if (ready == NULL) {
                set_error(game, "could not publish EndGame test readiness");
                return 0;
            }
            (void)fputs("active\n", ready);
            (void)fclose(ready);
        }
    }
#endif
    return 1;
}

static int end_game_begin_song(void *context, int16_t song, int16_t arg)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    if (binding == NULL || binding->game == NULL) return 0;
    ++binding->game->end_game_song_requests;
    /* Route through the original root:m00DF gate. The recovered audio binding
     * observes driver_ready==0 and disabled preferences exactly as source does. */
    myBeginSong(song, arg);
    return 1;
}

static int end_game_open_window(void *context, int16_t window_id)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    PortableWindowOpenResult result;
    PortableWindowOpenStatus open_status;
    static const int16_t args[4] = {0, 0, 0, 0};
    const PortableWindowRect menu_rect = {0, 0, LIVE_SCREEN_WIDTH, 0};
    if (binding == NULL || binding->game == NULL || binding->view == NULL ||
        window_id != 0x0400)
        return 0;
    game = binding->game;
    open_status = portable_window_open_apply(game->registry, &game->windows,
            window_id, args, LIVE_SCREEN_WIDTH, LIVE_SCREEN_HEIGHT,
            &menu_rect, &result);
    if (open_status != PORTABLE_WINDOW_OPEN_OK ||
        game->windows.front_window_id != window_id ||
        !portable_end_game_view_note_open(binding->view, window_id)) {
        (void)snprintf(game->error, sizeof(game->error),
            "source win_Open rejected EndGame window 0x0400 (%s, loaded=%u, front=%d)",
            portable_window_open_status_string(open_status),
            game->registry->slots[4].loaded,
            game->windows.front_window_id);
        return 0;
    }
    game->end_game_opened = 1;
    game->end_game_open_tick = sim_timing_tick_count(&game->clock);
    game->end_game_window_rect[0] = game->registry->slots[4].window.rect.left;
    game->end_game_window_rect[1] = game->registry->slots[4].window.rect.top;
    game->end_game_window_rect[2] = game->registry->slots[4].window.rect.right;
    game->end_game_window_rect[3] = game->registry->slots[4].window.rect.bottom;
    {
        static const uint8_t objects[] = {2, 3, 4};
        size_t i;
        for (i = 0; i < sizeof(objects); ++i) {
            const PortableWindowRect rect =
                game->registry->slots[4].window.objects[objects[i]].rect;
            game->end_game_object_rects[i * 4u + 0u] = rect.left;
            game->end_game_object_rects[i * 4u + 1u] = rect.top;
            game->end_game_object_rects[i * 4u + 2u] = rect.right;
            game->end_game_object_rects[i * 4u + 3u] = rect.bottom;
        }
    }
    game->dirty = 1;
    return 1;
}

static int end_game_set_font(void *context, int16_t font_id)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    return binding != NULL && binding->view != NULL &&
           portable_end_game_view_set_font(binding->view, font_id);
}

static int end_game_set_resource_text(void *context, int16_t object_id,
                                      int16_t resource_id, int16_t index)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    return binding != NULL && binding->view != NULL &&
        portable_end_game_view_set_resource_text(binding->view, object_id,
                                                  resource_id, index);
}

static int end_game_set_score_text(void *context, int16_t object_id,
                                   int32_t score)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    return binding != NULL && binding->view != NULL &&
        portable_end_game_view_set_score_text(binding->view, object_id, score);
}

static int end_game_dialog_wait_init(void *context, int16_t seconds)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    int32_t tick;
    if (binding == NULL || binding->game == NULL || seconds < 0) return 0;
    game = binding->game;
    /* Source DialogWaitInit drains StillDown before sampling TickCount. */
    while (game->left_down && !game->quit_requested) {
        HostEvent event;
        int polled = host_poll_event(game->host, &event);
        if (polled < 0) return 0;
        if (polled == 0) host_wait_ms(1);
        else if (event.kind == HOST_EVENT_MOUSE_UP && event.button == 1)
            game->left_down = 0;
        else if (event.kind == HOST_EVENT_QUIT)
            game->quit_requested = 1;
    }
    if (game->quit_requested || !tick_count_provider(game, &tick)) return 0;
    game->end_game_wait_start = (uint32_t)tick;
    game->end_game_wait_delay = (uint32_t)(uint16_t)seconds * 18u;
    return 1;
}

static int end_game_window_is_open(void *context, int16_t window_id,
                                   int *is_open)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    uint16_t index;
    if (binding == NULL || binding->game == NULL || is_open == NULL ||
        window_id != 0x0400)
        return 0;
    game = binding->game;
    index = (uint16_t)window_id >> 8;
    if (index >= game->registry->window_count ||
        !game->registry->slots[index].loaded)
        return 0;
    *is_open = (game->windows.windows[index].flags & PORTABLE_WINDOW_OPEN) != 0;
    return 1;
}

static int end_game_window_events(void *context, int *has_events)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    HostEvent event;
    int polled;
    if (binding == NULL || binding->game == NULL || has_events == NULL)
        return 0;
    game = binding->game;
    ++game->end_game_polls;
    *has_events = 0;
    while ((polled = host_poll_event(game->host, &event)) > 0) {
        if (event.kind == HOST_EVENT_QUIT) {
            game->quit_requested = 1;
            game->end_game_quit_seen = 1;
            *has_events = 1;
        } else if (event.kind == HOST_EVENT_MOUSE_MOVE) {
            game->cursor_x = event.x;
            game->cursor_y = event.y;
        } else if (event.kind == HOST_EVENT_MOUSE_DOWN && event.button == 1) {
            game->left_down = 1;
            game->cursor_x = event.x;
            game->cursor_y = event.y;
        } else if (event.kind == HOST_EVENT_MOUSE_UP && event.button == 1) {
            game->left_down = 0;
            game->cursor_x = event.x;
            game->cursor_y = event.y;
        } else if (event.kind == HOST_EVENT_KEY_DOWN) {
            int16_t logical_key;
            PortableInputStatus key_status = portable_input_decode_bios_key(
                event.key, &logical_key);
            if (key_status == PORTABLE_INPUT_OK && logical_key != 0) {
                game->end_game_last_key = logical_key;
                *has_events = 1;
            } else if (key_status != PORTABLE_INPUT_OK &&
                     key_status != PORTABLE_INPUT_MODIFIER_ONLY &&
                     key_status != PORTABLE_INPUT_NO_KEY) {
                set_error(game, "EndGame received an invalid BIOS key word");
                return 0;
            }
        }
    }
    if (polled < 0) {
        set_error(game, "SDL event polling failed during EndGame modal loop");
        return 0;
    }
    return 1;
}

static int32_t end_game_signed_tick(uint32_t bits)
{
    if (bits <= INT32_MAX) return (int32_t)bits;
    return (int32_t)((int64_t)bits - INT64_C(4294967296));
}

static int end_game_waited_enough(PortableLiveGame *game)
{
    int32_t first, second, reset, start, deadline;
    int result;
    start = end_game_signed_tick(game->end_game_wait_start);
    deadline = end_game_signed_tick(game->end_game_wait_start +
                                    game->end_game_wait_delay);
    if (!tick_count_provider(game, &first)) return -1;
    if (first < start) {
        result = 1;
    } else {
        if (!tick_count_provider(game, &second)) return -1;
        result = deadline <= second;
    }
    if (result) {
        if (!tick_count_provider(game, &reset)) return -1;
        game->end_game_wait_start = (uint32_t)reset;
    }
    return result;
}

static int end_game_dialog_abort_or_continue(void *context,
                                             int *requested_close)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    int waited;
    if (binding == NULL || binding->game == NULL || requested_close == NULL)
        return 0;
    game = binding->game;
    ++game->end_game_dialog_abort_polls;
    waited = end_game_waited_enough(game);
    if (waited < 0) {
        set_error(game, "source DialogWait TickCount provider failed");
        return 0;
    }
    *requested_close = waited != 0 || game->end_game_last_key != 0;
    game->end_game_last_key = 0;
    if (!*requested_close) host_wait_ms(1);
    return 1;
}

static int end_game_close_window(void *context, int16_t window_id)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    PortableWindowOpenResult result;
    PortableFramebuffer *fb;
    if (binding == NULL || binding->game == NULL || window_id != 0x0400)
        return 0;
    game = binding->game;
    if (portable_window_close_apply(game->registry, &game->windows, window_id,
                                    &result) != PORTABLE_WINDOW_OPEN_OK) {
        set_error(game, "source win_Close rejected EndGame window 0x0400");
        return 0;
    }
    game->end_game_closed = 1;
    game->end_game_close_tick = sim_timing_tick_count(&game->clock);
    game->dirty = 1;
    if (!redraw(game)) return 0;
    fb = game->renderer->framebuffer;
    if (!host_present(game->host, fb->pixels, fb->stride, game->host_palette)) {
        set_error(game, "SDL presentation failed after source EndGame close");
        return 0;
    }
    game->frame_pending = 0;
    return 1;
}

static int end_game_song_done(void *context, int *is_done)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    if (binding == NULL || binding->game == NULL || is_done == NULL) return 0;
    ++binding->game->end_game_song_done_polls;
    /* mySongIsDone follows the original driver/options gate; with no audio
     * driver its source result is true, which the modal flow must observe. */
    *is_done = mySongIsDone() != 0;
    return 1;
}

#ifdef SIMANT_ENABLE_NEW_GAME_NEXT5
static int live_scenario_select_provider(void *context, int16_t flag,
                                         int16_t *dos_result)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    PortableScenarioModalRequest request;
    PortableScenarioModalStatus status;
    uint16_t selected = 0;
    if (game == NULL || dos_result == NULL || flag != 0 || game->faulted) {
        if (game != NULL)
            set_error(game, "source DoScenario received an unsupported live flag");
        return 0;
    }
    memset(&request, 0, sizeof(request));
    request.registry = game->registry;
    request.open_scene = &game->windows;
    request.palette = game->palette;
    request.fonts = game->fonts;
    request.renderer = game->renderer;
    request.screen_width = LIVE_SCREEN_WIDTH;
    request.screen_height = LIVE_SCREEN_HEIGHT;
    request.menu_rect = (PortableWindowRect){0, 0, LIVE_SCREEN_WIDTH, 0};
    request.tick_count = modal_tick_count_provider;
    request.clock_context = game;
    request.quit_flag = &game->quit_requested;
#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
    defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
    if (live_test_scenario_202_enabled()) {
        const char *ready_path = getenv("SIMANT_LIVE_SCENARIO_READY");
        if (ready_path != NULL && ready_path[0] != '\0') {
            FILE *ready = fopen(ready_path, "wb");
            if (ready == NULL) {
                set_error(game, "could not publish scenario-modal test readiness");
                return 0;
            }
            (void)fputs("active\n", ready);
            (void)fclose(ready);
        }
    }
#endif
    status = portable_scenario_modal_run(game->host, &request, &selected);
#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
    defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
    if (live_test_scenario_202_enabled()) {
        const char *ready_path = getenv("SIMANT_LIVE_SCENARIO_READY");
        if (ready_path != NULL && ready_path[0] != '\0') (void)remove(ready_path);
    }
#endif
    if (status == PORTABLE_SCENARIO_MODAL_SELECTED ||
        status == PORTABLE_SCENARIO_MODAL_CANCELLED) {
        if (selected < 0x0202 || selected > 0x0207) {
            set_error(game, "source DoScenario returned an invalid result code");
            return 0;
        }
#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
    defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
        if (live_test_scenario_202_enabled())
            game->newgame_202_selection_code = (int16_t)selected;
#endif
        *dos_result = (int16_t)selected;
        return 1;
    }
    set_error(game, portable_scenario_modal_status_string(status));
    return 0;
}

static int end_game_new_game(void *context, int16_t option,
                             int16_t *result)
{
    LiveEndGameBinding *binding = (LiveEndGameBinding *)context;
    PortableLiveGame *game;
    if (binding == NULL || binding->game == NULL || binding->view == NULL ||
        result == NULL || option != 0)
        return 0;
    game = binding->game;
    /* EndGame's view owns copied SHARED records. Release them before entering
     * source NewGame because a recovered host rejection longjmps past C frames. */
    portable_end_game_view_release(binding->view);
    if (!sim_recovered_engine_new_game_from_modal(&game->engine, option,
                                                   result)) {
        set_error(game, "source NewGame(option=0) continuation is unavailable");
        return 0;
    }
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
#ifdef SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC
    if (live_test_scenario_202_enabled()) {
        game->newgame_202_returned = 1;
        game->newgame_202_source_result = *result;
    }
#endif
#endif
    return 1;
}
#endif

static int live_end_game_provider(void *context, const SimGameOverInput *input,
                                  SimRng *rng)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    PortableEndGameView view;
    SimEndGameFlow flow;
    SimEndGameFlowHost flow_host;
    LiveEndGameBinding binding;
    SimEndGameFlowStatus flow_status;
    SimGameOverResult summary;
    if (game == NULL || input == NULL || rng == NULL || game->faulted ||
        game->end_game_opened || game->session == NULL || game->host == NULL ||
        game->palette == NULL || game->fonts == NULL ||
        game->renderer == NULL || game->registry == NULL) {
        if (game != NULL) set_error(game, "invalid or repeated source EndGame callback");
        return 0;
    }
    #if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
        defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
    if (live_test_scenario_202_enabled()) {
        ++game->gameover_callback_count;
        game->gameover_entry_completed_ticks = game->engine.completed_ticks;
        game->gameover_callback_input = *input;
        game->gameover_callback_rng_before = *rng;
        game->gameover_callback_completed = 0;
    }
    #endif
    portable_end_game_view_init(&view);
    binding.game = game;
    binding.view = &view;
    memset(&flow_host, 0, sizeof(flow_host));
    flow_host.context = &binding;
    flow_host.begin_song = end_game_begin_song;
    flow_host.open_window = end_game_open_window;
    flow_host.set_font = end_game_set_font;
    flow_host.set_resource_text = end_game_set_resource_text;
    flow_host.set_score_text = end_game_set_score_text;
    flow_host.dialog_wait_init = end_game_dialog_wait_init;
    flow_host.window_is_open = end_game_window_is_open;
    flow_host.window_events = end_game_window_events;
    flow_host.dialog_abort_or_continue = end_game_dialog_abort_or_continue;
    flow_host.close_window = end_game_close_window;
    flow_host.song_done = end_game_song_done;
#ifdef SIMANT_ENABLE_NEW_GAME_NEXT5
    flow_host.new_game = end_game_new_game;
#endif
    /* NewGame is exposed only by the guarded next5 source continuation.
     * MenuQuit remains absent and therefore fails closed if NewGame returns
     * its source negative result. */
    if (sim_game_over_calculate(input, &summary) != SIM_GAME_OVER_OK ||
        portable_end_game_view_prepare(&view, &game->session->shared_database,
            &summary, LIVE_SCREEN_WIDTH) != PORTABLE_END_GAME_VIEW_OK) {
        set_error(game, "source EndGame view could not load real string resources");
        portable_end_game_view_release(&view);
        return 0;
    }
    flow_status = sim_end_game_flow_begin(&flow, input, rng, &flow_host);
    if (flow_status != SIM_END_GAME_FLOW_OK) {
        if (game->error[0] == '\0')
            set_error(game, flow.failed_service != NULL ? flow.failed_service :
                sim_end_game_flow_status_string(flow_status));
        goto done;
    }
    game->end_game_score = flow.summary.score;
    game->end_game_scenario_index = (uint8_t)flow.summary.scenario_index;
    game->end_game_level_index = flow.summary.level_index;
    if (!end_game_present(game, &view)) goto done;
    while (flow.phase == SIM_END_GAME_FLOW_WAIT_WINDOW) {
        flow_status = sim_end_game_flow_step(&flow);
        if (flow_status != SIM_END_GAME_FLOW_OK) break;
        if (game->quit_requested) break;
    }
    if (flow.phase == SIM_END_GAME_FLOW_FAILED && flow.failed_service != NULL &&
        strcmp(flow.failed_service, "NewGame") == 0 && game->end_game_closed) {
        game->end_game_boundary_reached = 1;
        (void)snprintf(game->end_game_boundary,
            sizeof(game->end_game_boundary), "NewGame(option=0)");
        set_error(game, "EndGame closed; unsupported NewGame continuation");
    } else if (flow.phase == SIM_END_GAME_FLOW_COMPLETE &&
               flow.outcome == SIM_END_GAME_FLOW_NEW_GAME_RETURNED) {
        /* A true result means the actual recovered NewGame returned normally.
         * Clear only host modal bookkeeping so a later source EndGame is legal. */
        game->end_game_opened = 0;
        game->end_game_closed = 0;
        game->end_game_boundary_reached = 0;
        game->end_game_boundary[0] = '\0';
        #if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
            defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
        if (live_test_scenario_202_enabled()) {
            game->gameover_callback_rng_after = *rng;
            game->gameover_callback_completed = 1;
        }
        #endif
        portable_end_game_view_release(&view);
        return 1;
    } else {
        set_error(game, flow.failed_service != NULL ? flow.failed_service :
            sim_end_game_flow_status_string(flow_status));
    }
done:
    if (game->end_game_opened && !game->end_game_closed) {
        int is_open = 0;
        if (end_game_window_is_open(&binding, 0x0400, &is_open) && is_open)
            (void)end_game_close_window(&binding, 0x0400);
    }
    portable_end_game_view_release(&view);
    return 0;
}

static int redraw_snapshot_edit(PortableLiveGame *game)
{
    RecoveredState snapshot;
    SimRecoveredBridgeStatus bridge_status;
    PortableFramebuffer *fb;
    if (game == NULL || game->snapshot_session == NULL ||
        !sim_recovered_engine_snapshot(&game->engine, &snapshot)) {
        set_error(game, "source edit update has no active recovered-state snapshot");
        return 0;
    }
    bridge_status = sim_session_from_recovered_state(game->snapshot_session,
                                                       &snapshot);
    if (bridge_status != SIM_RECOVERED_BRIDGE_OK) {
        set_error(game, "source edit update snapshot could not project its live world");
        return 0;
    }
    if (!redraw_scene(game, game->snapshot_session)) return 0;
    fb = game->renderer->framebuffer;
    if (!host_present(game->host, fb->pixels, fb->stride, game->host_palette)) {
        set_error(game, "SDL presentation failed during source edit update");
        return 0;
    }
    game->frame_pending = 0;
    return 1;
}

static int object_effect_sink(void *context,
                              const PortableObjectEffect *effect)
{
    PortableLiveGame *game = (PortableLiveGame *)context;
    if (game == NULL || effect == NULL) return 0;
    switch (effect->kind) {
    case PORTABLE_OBJECT_INVERT:
    case PORTABLE_OBJECT_DRAW:
    case PORTABLE_OBJECT_DRAW_BITMAP:
        /* Re-rendering the complete loaded window stack applies the mutated
         * object state and its real clipping/occlusion synchronously. */
        return redraw_snapshot_edit(game);
    case PORTABLE_OBJECT_ADD_PROXIMITY:
    case PORTABLE_OBJECT_REMOVE_PROXIMITY:
        set_error(game, "source proximity event queue is not modeled");
        return 0;
    }
    set_error(game, "unknown source object effect");
    return 0;
}

static int seed_new_window_state(PortableLiveGame *game, uint16_t index)
{
    PortableWindowRegistrySlot *slot;
    PortableWindowObject *frame;
    if (game == NULL || index >= game->registry->window_count ||
        index >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return 0;
    slot = &game->registry->slots[index];
    if (!slot->loaded || slot->window.count == 0) return 0;
    frame = &slot->window.objects[0];
    game->windows.windows[index].flags = (uint16_t)(
        slot->window.flags & ~PORTABLE_WINDOW_OPEN);
    game->windows.windows[index].origin.left = frame->offsets[0];
    game->windows.windows[index].origin.top = frame->offsets[1];
    game->windows.windows[index].origin.right = frame->offsets[2];
    game->windows.windows[index].origin.bottom = frame->offsets[3];
    game->windows.windows[index].has_saved_origin = 0;
    return 1;
}

static int apply_source_window_open(PortableLiveGame *game, int16_t window_id)
{
    static const int16_t zero_args[4] = {0, 0, 0, 0};
    const PortableWindowRect menu_rect = {0, 0, LIVE_SCREEN_WIDTH, 0};
    PortableWindowOpenResult result;
    PortableWindowOpenStatus status;
    PortableWindowRegistrySlot *slot;
    uint16_t index;
    uint16_t object;
    int was_loaded;
    if (window_id < 0 || (window_id & 0xff) != 0 ||
        (uint16_t)window_id >= (PORTABLE_WINDOW_REGISTRY_SLOTS << 8)) {
        set_error(game, "source win_Open received an invalid window ID");
        return 0;
    }
    index = (uint16_t)window_id >> 8;
    if (index >= game->registry->window_count) {
        set_error(game, "source win_Open window ID exceeds registry count");
        return 0;
    }
    was_loaded = game->registry->slots[index].loaded != 0;
    if (portable_window_registry_load(game->registry, (int16_t)index) !=
            PORTABLE_WINDOW_REGISTRY_OK) {
        set_error(game, "source win_Open could not load its resource");
        return 0;
    }
    slot = &game->registry->slots[index];
    if (!was_loaded && !seed_new_window_state(game, index)) {
        set_error(game, "source win_Open could not initialize loaded window state");
        return 0;
    }
    /* win_Open has a variadic ABI. Its recovered callers expose no argument
     * words here, so accept only resources whose geometry does not consume
     * mode-5 caller-stack values; all other geometry fails closed. */
    for (object = 0; object < slot->window.count; ++object) {
        unsigned axis;
        for (axis = 0; axis < 4; ++axis) {
            if (slot->window.objects[object].modes[axis] == 5) {
                set_error(game, "source win_Open needs unavailable variadic geometry words");
                return 0;
            }
        }
    }
    status = portable_window_open_apply(game->registry, &game->windows,
        window_id, zero_args, LIVE_SCREEN_WIDTH, LIVE_SCREEN_HEIGHT,
        &menu_rect, &result);
    if (status != PORTABLE_WINDOW_OPEN_OK) {
        set_error(game, portable_window_open_status_string(status));
        return 0;
    }
#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && defined(SIMANT_ENABLE_HISTORY_UI_NEXT10)
    if (window_id == 0x1500 && !write_history_geometry(game)) {
        set_error(game, "could not record live History geometry");
        return 0;
    }
#endif
    if (!result.already_front && !redraw_snapshot_edit(game)) return 0;
    game->dirty = 1;
    return 1;
}

static int apply_source_window_close(PortableLiveGame *game, int16_t window_id)
{
    PortableWindowOpenResult result;
    PortableWindowOpenStatus status;
    uint16_t index;
    if (window_id < 0 || (window_id & 0xff) != 0 ||
        (uint16_t)window_id >= (PORTABLE_WINDOW_REGISTRY_SLOTS << 8)) {
        set_error(game, "source win_Close received an invalid window ID");
        return 0;
    }
    index = (uint16_t)window_id >> 8;
    if (index >= game->registry->window_count) {
        set_error(game, "source win_Close window ID exceeds registry count");
        return 0;
    }
    if (!game->registry->slots[index].loaded &&
        portable_window_registry_load(game->registry, (int16_t)index) !=
            PORTABLE_WINDOW_REGISTRY_OK) {
        set_error(game, "source win_Close could not load its resource");
        return 0;
    }
    if ((game->windows.windows[index].flags & PORTABLE_WINDOW_OPEN) == 0)
        return 1;
    status = portable_window_close_apply(game->registry, &game->windows,
                                         window_id, &result);
    if (status != PORTABLE_WINDOW_OPEN_OK) {
        set_error(game, portable_window_open_status_string(status));
        return 0;
    }
    if (!redraw_snapshot_edit(game)) return 0;
    game->dirty = 1;
    return 1;
}

static int refresh_edit_title_from_source(PortableLiveGame *game,
                                          uint16_t object_id,
                                          int16_t source_scenario)
{
    RecoveredState snapshot;
    if (object_id != 1 || source_scenario < 0 || source_scenario > 3 ||
        game->snapshot_session == NULL ||
        !sim_recovered_engine_snapshot(&game->engine, &snapshot) ||
        sim_session_from_recovered_state(game->snapshot_session, &snapshot) !=
            SIM_RECOVERED_BRIDGE_OK ||
        game->snapshot_session->world.scenario != source_scenario) {
        set_error(game, "source SetEditWinTitle context is unavailable or inconsistent");
        return 0;
    }
    if (!refresh_titles(game, &game->snapshot_session->world)) return 0;
    game->dirty = 1;
    return 1;
}

static int refresh_map_titles_from_source(PortableLiveGame *game)
{
    RecoveredState snapshot;
    int map_open, yard_open;
    if (game == NULL || game->snapshot_session == NULL ||
        !sim_recovered_engine_snapshot(&game->engine, &snapshot) ||
        sim_session_from_recovered_state(game->snapshot_session, &snapshot) !=
            SIM_RECOVERED_BRIDGE_OK ||
        !refresh_titles(game, &game->snapshot_session->world)) {
        set_error(game, "source SetMapTitle context is unavailable");
        return 0;
    }
    map_open = (game->windows.windows[1].flags & PORTABLE_WINDOW_OPEN) != 0;
    yard_open = (game->windows.windows[0x19].flags & PORTABLE_WINDOW_OPEN) != 0;
    if (map_open || (!map_open && yard_open))
        return redraw_snapshot_edit(game);
    game->dirty = 1;
    return 1;
}

static int apply_window_object_operation(PortableLiveGame *game,
                                         const SimRecoveredEffect *effect)
{
    PortableObjectContext object_context;
    PortableObjectStatus status;
    SimRecoveredWindowOperation operation;
    uint16_t object_id;
    int16_t source_value;
    if (game == NULL || effect == NULL) return 0;
    memset(&object_context, 0, sizeof(object_context));
    object_context.registry = game->registry;
    object_context.effect = object_effect_sink;
    object_context.context = game;
    operation = (SimRecoveredWindowOperation)(intptr_t)effect->arguments[0];
    object_id = (uint16_t)(int16_t)(intptr_t)effect->arguments[1];
    source_value = (int16_t)(intptr_t)effect->arguments[2];
    switch (operation) {
    case SIM_RECOVERED_WINDOW_OPEN:
        return apply_source_window_open(game, (int16_t)object_id);
    case SIM_RECOVERED_WINDOW_CLOSE:
        return apply_source_window_close(game, (int16_t)object_id);
    case SIM_RECOVERED_WINDOW_FLUSH_EVENTS:
        game->source_event_head = 0;
        game->source_event_count = 0;
        game->previous_mouse_event_tick = 0;
        memset(&game->previous_mouse_event, 0,
               sizeof(game->previous_mouse_event));
        return 1;
    case SIM_RECOVERED_WINDOW_CLIP_PUSH:
        if (game->source_clip_depth >=
                sizeof(game->source_clip_stack) /
                sizeof(game->source_clip_stack[0])) {
            set_error(game, "source clip stack capacity exceeded");
            return 0;
        }
        game->source_clip_stack[game->source_clip_depth++] =
            game->source_clip_window;
        return 1;
    case SIM_RECOVERED_WINDOW_CLIP_POP:
        if (game->source_clip_depth == 0) {
            set_error(game, "source clip pop has no matching push");
            return 0;
        }
        game->source_clip_window =
            game->source_clip_stack[--game->source_clip_depth];
        return 1;
    case SIM_RECOVERED_WINDOW_DRAW_OBJECT:
        if ((object_id >> 8) >= game->registry->window_count ||
            !game->registry->slots[object_id >> 8].loaded ||
            (object_id & 0xffu) >=
                game->registry->slots[object_id >> 8].window.count) {
            set_error(game, "source win_DrawObjectNum object is not loaded");
            return 0;
        }
        return redraw_snapshot_edit(game);
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
    case SIM_RECOVERED_WINDOW_FILL_OBJECT: {
        PortableFramebuffer *fb = game->renderer->framebuffer;
        PortableRect saved_clip = fb->clip;
        PortableHistoryRasterProviders raster;
        uint8_t color;
        if (object_id != 0x150e || source_value != 0 ||
            game->source_clip_window != 0x1500 || !prepare_history_resources(game)) {
            set_error(game, "source fill-object contract is unavailable");
            return 0;
        }
        portable_history_active_raster_providers(&game->history_resources, fb, &raster);
        if (!raster.resolve_color(raster.context, source_value, &color)) return 0;
        if (game->windows.front_window_id == 0x1500) {
            const PortableWindowRect *rect = &game->registry->slots[0x15].window.rect;
            portable_framebuffer_set_clip(fb, rect_intersection(saved_clip,
                (PortableRect){rect->left, rect->top, rect->right, rect->bottom}));
            if (!raster.fill_object(raster.context, object_id, source_value, color)) {
                portable_framebuffer_set_clip(fb, saved_clip);
                return 0;
            }
            portable_framebuffer_set_clip(fb, saved_clip);
        }
        game->dirty = 1;
        game->frame_pending = 1;
        return 1;
    }
    case SIM_RECOVERED_WINDOW_DRAW_HISTORY_GRAPH:
        return draw_history_graph_effect(game,
            (int16_t)(intptr_t)effect->arguments[1],
            (int16_t)(intptr_t)effect->arguments[2],
            (int16_t)(intptr_t)effect->arguments[3]);
#endif
    case SIM_RECOVERED_WINDOW_UPDATE_EDIT_IF_OPEN:
        /* root:m0250 UpdateEdit checks win_IsWinOpen(0), clips to the Edit
         * window, draws its current view/graphs, then turns clipping off. */
        if ((game->windows.windows[0].flags & PORTABLE_WINDOW_OPEN) == 0)
            return 1;
        game->source_clip_window = 0;
        if (!redraw_snapshot_edit(game)) return 0;
        game->source_clip_window = PORTABLE_WINDOW_OPEN_NONE;
        game->dirty = 1;
        return 1;
    case SIM_RECOVERED_WINDOW_SET_EDIT_TITLE_FROM_SCENARIO:
        return refresh_edit_title_from_source(game, object_id, source_value);
    case SIM_RECOVERED_WINDOW_SET_MAP_TITLE:
        return refresh_map_titles_from_source(game);
    case SIM_RECOVERED_WINDOW_DRAW_EDIT_TITLE_OBJECT:
        if (object_id != 1 || game->source_clip_window != 0 ||
            !(game->windows.windows[0].flags & PORTABLE_WINDOW_OPEN)) {
            set_error(game, "source edit-title draw lacks its window-0 clip context");
            return 0;
        }
        return redraw_snapshot_edit(game);
    case SIM_RECOVERED_WINDOW_SWAP:
        set_error(game, "source win_Swap trailing geometry arguments are unavailable");
        return 0;
    default:
        break;
    }
    if ((object_id >> 8) >= PORTABLE_WINDOW_REGISTRY_SLOTS) {
        set_error(game, "source object operation names an invalid window");
        return 0;
    }
    object_context.window_open =
        (game->windows.windows[object_id >> 8].flags &
         PORTABLE_WINDOW_OPEN) != 0;
    object_context.window_in_front = game->windows.front_window_id ==
                                     (int16_t)(object_id & 0xff00u);
    switch (operation) {
    case SIM_RECOVERED_WINDOW_CLIP_OFF:
        game->source_clip_window = PORTABLE_WINDOW_OPEN_NONE;
        game->dirty = 1;
        return 1;
    case SIM_RECOVERED_WINDOW_CLIP_SET:
        source_value = (int16_t)(intptr_t)effect->arguments[1];
        if (source_value < 0 || (source_value & 0xff) != 0 ||
            (uint16_t)(source_value >> 8) >= game->registry->window_count) {
            set_error(game, "source clip window is invalid");
            return 0;
        }
        game->source_clip_window = source_value;
        return 1;
    case SIM_RECOVERED_WINDOW_MAKE_SELECTED:
        status = portable_object_set_selected(&object_context, object_id, 1);
        break;
    case SIM_RECOVERED_WINDOW_MAKE_UNSELECTED:
        status = portable_object_set_selected(&object_context, object_id, 0);
        break;
    case SIM_RECOVERED_WINDOW_MAKE_VISIBLE:
        status = portable_object_set_visible(&object_context, object_id, 1);
        break;
    case SIM_RECOVERED_WINDOW_MAKE_INVISIBLE:
        status = portable_object_set_visible(&object_context, object_id, 0);
        break;
    case SIM_RECOVERED_WINDOW_SET_SELECTED_STATE:
        if (source_value != 0 && source_value != 1) {
            set_error(game, "source selected-state value is outside 0/1");
            return 0;
        }
        status = portable_object_set_selected(&object_context, object_id,
                                              source_value);
        break;
    case SIM_RECOVERED_WINDOW_INVALIDATE_MAP:
        /* InvalEuMap only marks its source cache entries invalid. The native
         * view is rebuilt at the later source UpdateEdit/presentation point. */
        game->dirty = 1;
        return 1;
    case SIM_RECOVERED_WINDOW_UNSELECT_GROUP:
        if (source_value < 0 || source_value > UINT8_MAX) {
            set_error(game, "source object group is outside its byte range");
            return 0;
        }
        status = portable_object_group_selected(&object_context, object_id,
                                                (uint8_t)source_value, 0);
        break;
    case SIM_RECOVERED_WINDOW_SET_BITMAP:
        status = portable_object_set_bitmap(game->registry, object_id,
                                            source_value);
        break;
    case SIM_RECOVERED_WINDOW_SET_MENU_ITEM_STATE:
        source_value = (int16_t)(intptr_t)effect->arguments[1];
        status = PORTABLE_OBJECT_OK;
        {
            PortableMenuStatus menu_status = portable_menu_set_item_state(
                &game->menu, source_value,
                (uint8_t)(uint16_t)(intptr_t)effect->arguments[2]);
            if (menu_status != PORTABLE_MENU_OK) {
                set_error(game, portable_menu_status_string(menu_status));
                return 0;
            }
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
            ++game->menu_item_state_calls;
#endif
        }
        game->dirty = 1;
        return 1;
    case SIM_RECOVERED_WINDOW_SET_MENU_ITEM_TEXT:
        source_value = (int16_t)(intptr_t)effect->arguments[1];
        if (effect->arguments[2] == 0) {
            set_error(game, "source menu text pointer is null");
            return 0;
        }
        {
            PortableMenuStatus menu_status = portable_menu_set_text_by_id(
                &game->menu, source_value,
                (const char *)effect->arguments[2]);
            if (menu_status != PORTABLE_MENU_OK) {
                set_error(game, portable_menu_status_string(menu_status));
                return 0;
            }
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
            ++game->menu_item_text_calls;
#endif
        }
        game->dirty = 1;
        return 1;
    default:
        set_error(game, "source object operation has no live implementation");
        return 0;
    }
    if (status != PORTABLE_OBJECT_OK) {
        if (game->error[0] == '\0')
            set_error(game, "source object state mutation was rejected");
        return 0;
    }
    game->dirty = 1;
    return 1;
}

/* Synchronous control providers run inside the recovered binding boundary.
 * State is published by control_adapter before each callback. Rendering uses
 * a new snapshot so intermediate source writes are visible immediately. */
static int control_window_operation(PortableLiveGame *game,
                                    SimRecoveredWindowOperation operation,
                                    uint16_t object_id)
{
    SimRecoveredEffect effect;
    memset(&effect, 0, sizeof(effect));
    effect.kind = SIM_RECOVERED_EFFECT_WINDOW_OPERATION;
    effect.arguments[0] = (uintptr_t)operation;
    effect.arguments[1] = object_id;
    return apply_window_object_operation(game, &effect);
}

static int control_clip_set(void *context, uint16_t window_id)
{
    return control_window_operation(context, SIM_RECOVERED_WINDOW_CLIP_SET,
                                     window_id);
}

static int control_clip_off(void *context)
{
    return control_window_operation(context, SIM_RECOVERED_WINDOW_CLIP_OFF, 0);
}

static int control_help(void *context, uint16_t help_context)
{
    (void)help_context;
    set_error(context, "source control DoWinHelp host service is unavailable");
    return 0;
}

static int control_group_visible(void *context, uint16_t window_id,
                                 uint8_t group, int visible)
{
    PortableLiveGame *game = context;
    PortableObjectContext objects;
    PortableObjectStatus status;
    memset(&objects, 0, sizeof(objects));
    objects.registry = game->registry;
    objects.window_open = (game->windows.windows[window_id >> 8].flags &
                           PORTABLE_WINDOW_OPEN) != 0;
    objects.window_in_front = game->windows.front_window_id == (int16_t)window_id;
    objects.effect = object_effect_sink;
    objects.context = game;
    status = portable_object_group_visible(&objects, window_id, group, visible);
    if (status != PORTABLE_OBJECT_OK) {
        set_error(game, "source control group visibility mutation failed");
        return 0;
    }
    return 1;
}

static int control_select(void *context, uint16_t object_id)
{
    return control_window_operation(context, SIM_RECOVERED_WINDOW_MAKE_SELECTED,
                                     object_id);
}

static int control_rect(void *context, uint16_t object_id, SimSetupRect *rect)
{
    PortableLiveGame *game = context;
    PortableWindowRect loaded;
    if (rect == NULL || portable_window_registry_get_object_rect(game->registry,
            object_id, &loaded) != PORTABLE_WINDOW_REGISTRY_OK) {
        set_error(game, "source control object rectangle is unavailable");
        return 0;
    }
    rect->left = loaded.left; rect->top = loaded.top;
    rect->right = loaded.right; rect->bottom = loaded.bottom;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    trace_control_input("rect", loaded.left, loaded.top, loaded.right, loaded.bottom);
#endif
    return 1;
}

static int control_draw(void *context, SimSetupControlKind kind, uint16_t flags,
                         const SimSetupControls *controls, int16_t percent)
{
    PortableLiveGame *game = context;
    int16_t window_id = kind == SIM_SETUP_MODE_CONTROL ? 0x1200 : 0x1300;
    if (flags != 3 || controls != &game->session->setup_controls ||
        game->source_clip_window != window_id) {
        set_error(game, "source control draw lacks its active window state");
        return 0;
    }
    if (kind == SIM_SETUP_MODE_CONTROL) game->mode_percent = percent;
    else game->caste_percent = percent;
    return redraw_snapshot_edit(game);
}

static int control_pointer_poll(void *context, SimSetupPoint *point)
{
    PortableLiveGame *game = context;
    HostEvent event;
    int polled = host_poll_event(game->host, &event);
    if (polled < 0) {
        set_error(game, "SDL event conversion failed during control drag");
        return 0;
    }
    if (polled == 0) host_wait_ms(1);
    else if (event.kind == HOST_EVENT_QUIT) {
        game->quit_requested = 1;
        game->left_down = 0;
    } else if (event.kind == HOST_EVENT_MOUSE_MOVE ||
               ((event.kind == HOST_EVENT_MOUSE_UP ||
                 event.kind == HOST_EVENT_MOUSE_DOWN) && event.button == 1)) {
        game->cursor_x = event.x; game->cursor_y = event.y;
        if (event.kind == HOST_EVENT_MOUSE_UP) game->left_down = 0;
        else if (event.kind == HOST_EVENT_MOUSE_DOWN) game->left_down = 1;
    } else if (event.kind != HOST_EVENT_NONE) {
        if (game->deferred_host_event_count >= LIVE_DEFERRED_HOST_EVENT_CAPACITY) {
            set_error(game, "host event backlog exceeded during control drag");
            return 0;
        }
        game->deferred_host_events[game->deferred_host_event_count++] = event;
    }
    point->x = game->cursor_x; point->y = game->cursor_y;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    trace_control_input("poll", point->x, point->y, game->left_down, polled);
#endif
    return 1;
}

static int control_still_down(void *context, int *down)
{
    *down = ((PortableLiveGame *)context)->left_down;
    return 1;
}

static int control_clip_push(void *context)
{ return control_window_operation(context, SIM_RECOVERED_WINDOW_CLIP_PUSH, 0); }

static int control_top_clip(void *context)
{
    PortableLiveGame *game = context;
    return control_clip_set(game, (uint16_t)game->windows.front_window_id);
}

static int control_clip_pop(void *context)
{ return control_window_operation(context, SIM_RECOVERED_WINDOW_CLIP_POP, 0); }

static int control_selected_state(void *context, uint16_t object_id, int selected)
{
    SimRecoveredEffect effect;
    memset(&effect, 0, sizeof(effect));
    effect.kind = SIM_RECOVERED_EFFECT_WINDOW_OPERATION;
    effect.arguments[0] = SIM_RECOVERED_WINDOW_SET_SELECTED_STATE;
    effect.arguments[1] = object_id;
    effect.arguments[2] = (uintptr_t)selected;
    return apply_window_object_operation(context, &effect);
}

static int control_wait_ticks(void *context, uint16_t ticks)
{
    PortableLiveGame *game = context;
    uint32_t start;
    if (!advance_clock_to(game, host_time_ns())) return 0;
    start = sim_timing_tick_count(&game->clock);
    while ((uint32_t)(sim_timing_tick_count(&game->clock) - start) < ticks) {
        host_wait_ms(1);
        if (!advance_clock_to(game, host_time_ns())) return 0;
    }
    return 1;
}

static int run_source_control(PortableLiveGame *game, int16_t x, int16_t y,
                              int *handled)
{
    int16_t window_id = game->windows.front_window_id;
    PortableWindowRegistrySlot *slot;
    SimControlEventPrivateState private_state;
    SimControlEventProvider provider;
    SimControlEventMessage message;
    SimRecoveredEngineStatus status;
    int hit;
    *handled = 0;
    if (window_id != 0x1200 && window_id != 0x1300) return 1;
    slot = &game->registry->slots[(uint16_t)window_id >> 8];
    if (!slot->loaded || !(game->windows.windows[(uint16_t)window_id >> 8].flags &
                           PORTABLE_WINDOW_OPEN)) return 1;
    hit = portable_window_mouse_hit_test(&slot->window, (PortableWindowPoint){x, y});
    if (hit < 0) return 1;
    *handled = 1;
    if ((hit < 3 || slot->window.objects[hit].type != 1) &&
        !(hit == 2 && slot->window.objects[hit].type == 6 &&
          !(slot->window.objects[hit].flags & 0x800u))) {
        set_error(game, "source control frame/close dispatch is unavailable");
        return 0;
    }
    if (slot->window.objects[hit].type == 1) {
        PortableControlPreselectCallbacks preselect = {
            control_clip_push, control_top_clip, control_selected_state,
            control_wait_ticks, control_clip_pop, game};
        if (portable_control_preselect(game->registry,
                (uint16_t)(window_id | hit), &preselect) !=
                PORTABLE_CONTROL_PRESELECT_OK) {
            if (game->error[0] == '\0')
                set_error(game, "source control button preselection failed");
            return 0;
        }
    }
    memset(&provider, 0, sizeof(provider));
    provider.clip_set_window = control_clip_set;
    provider.clip_off = control_clip_off;
    provider.help = control_help;
    provider.set_group_visible = control_group_visible;
    provider.select_object = control_select;
    provider.get_object_rect = control_rect;
    provider.draw_control = control_draw;
    provider.pointer_poll = control_pointer_poll;
    provider.still_down = control_still_down;
    provider.context = game;
    memset(&private_state, 0, sizeof(private_state));
    private_state.mode_percent = game->mode_percent;
    private_state.caste_percent = game->caste_percent;
    message.code = (uint16_t)(window_id | hit);
    message.point = (SimSetupPoint){x, y};
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    trace_control_input("message", message.code, x, y, game->left_down);
#endif
    status = sim_recovered_engine_control_event(&game->engine,
        window_id == 0x1200 ? SIM_SETUP_MODE_CONTROL : SIM_SETUP_CASTE_CONTROL,
        &message, &private_state, &provider);
    if (status != SIM_RECOVERED_ENGINE_OK) {
        if (game->error[0] == '\0') set_error(game, game->engine.failed_service != NULL ?
            game->engine.failed_service : sim_recovered_engine_status_string(status));
        return 0;
    }
    game->mode_percent = private_state.mode_percent;
    game->caste_percent = private_state.caste_percent;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    ++game->control_event_calls;
    game->control_last_code = message.code;
#endif
    game->scheduler.initialized = 0;
    if (!reconcile_modal_input(game) || !redraw(game)) return 0;
    return dispatch_deferred_host_events(game);
}

#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
static int run_source_history(PortableLiveGame *game, int16_t x, int16_t y,
                              int *handled)
{
    PortableWindowRegistrySlot *slot;
    SimRecoveredEngineStatus status;
    PortableWindowObject *object;
    int hit;
    *handled = 0;
    if (game->windows.front_window_id != 0x1500) return 1;
    slot = &game->registry->slots[0x15];
    if (!slot->loaded || !(game->windows.windows[0x15].flags & PORTABLE_WINDOW_OPEN))
        return 1;
    hit = portable_window_mouse_hit_test(&slot->window, (PortableWindowPoint){x, y});
    if (hit < 0) return 1;
    *handled = 1;
    object = &slot->window.objects[hit];
    if (hit < 2 || hit > 14) {
        set_error(game, "source History frame/close dispatch is unavailable");
        return 0;
    }
    if (object->type == 1) {
        PortableControlPreselectCallbacks preselect = {
            control_clip_push, control_top_clip, control_selected_state,
            control_wait_ticks, control_clip_pop, game};
        if (portable_control_preselect(game->registry, (uint16_t)(0x1500 | hit),
                &preselect) != PORTABLE_CONTROL_PRESELECT_OK) {
            set_error(game, "source History button preselection failed");
            return 0;
        }
    } else if (object->type != 6 || (object->flags & 0x800u)) {
        /* f_218D_000C has no type-specific work for type 6, and its common
         * selection path is skipped when bit 0x800 is clear. */
        set_error(game, "source History object preselection is unavailable");
        return 0;
    }
    game->history_input_active = 1;
    status = sim_recovered_engine_history_event(&game->engine, (uint16_t)(0x1500 | hit));
    game->history_input_active = 0;
    if (status != SIM_RECOVERED_ENGINE_OK) {
        if (game->error[0] == '\0') set_error(game, game->engine.failed_service != NULL ?
            game->engine.failed_service : sim_recovered_engine_status_string(status));
        return 0;
    }
    game->scheduler.initialized = 0;
    if (!reconcile_modal_input(game) || !redraw(game)) return 0;
    return dispatch_deferred_host_events(game);
}
#endif

static int apply_input_effects(PortableLiveGame *game,
                               const PortableInputEffects *effects)
{
    size_t i;
    for (i = 0; i < effects->count; ++i) {
        const PortableInputEffect *effect = &effects->items[i];
        switch (effect->kind) {
        case PORTABLE_INPUT_EFFECT_SET_SPEED:
            if (effect->value < 0 || effect->value > 3) {
                set_error(game, "unsupported simulation speed value");
                return 0;
            }
            if (sim_recovered_engine_action(&game->engine,
                    SIM_RECOVERED_ACTION_SPEED, effect->value, 0) !=
                    SIM_RECOVERED_ENGINE_OK) {
                set_error(game, game->engine.failed_service != NULL ?
                    game->engine.failed_service :
                    sim_recovered_engine_status_string(game->engine.status));
                return 0;
            }
            game->scheduler.initialized = 0;
            game->dirty = 1;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
            ++game->speed_action_calls[effect->value];
#endif
            return 1;
        case PORTABLE_INPUT_EFFECT_SET_PAUSED:
            if (sim_recovered_engine_action(&game->engine,
                    SIM_RECOVERED_ACTION_PAUSE, effect->value != 0, 0) !=
                    SIM_RECOVERED_ENGINE_OK) {
                set_error(game, game->engine.failed_service != NULL ?
                    game->engine.failed_service :
                    sim_recovered_engine_status_string(game->engine.status));
                return 0;
            }
            game->scheduler.initialized = 0;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
            ++game->pause_action_calls;
            if (effect->value != 0) {
                game->pause_start_ticks = game->engine.completed_ticks;
                game->pause_start_ns = host_time_ns();
            } else {
                game->pause_end_ticks = game->engine.completed_ticks;
                game->pause_duration_ns = host_time_ns() >= game->pause_start_ns
                    ? host_time_ns() - game->pause_start_ns : 0;
            }
#endif
            return 1;
        case PORTABLE_INPUT_EFFECT_SET_MAP_PLANE:
            if (sim_recovered_engine_action(&game->engine,
                    SIM_RECOVERED_ACTION_MAP_PLANE, effect->value, 0) !=
                    SIM_RECOVERED_ENGINE_OK) {
                set_error(game, game->engine.failed_service != NULL ?
                    game->engine.failed_service :
                    sim_recovered_engine_status_string(game->engine.status));
                return 0;
            }
            game->scheduler.initialized = 0;
            game->dirty = 1;
            return 1;
        default:
            set_error(game, "this recovered input command has no live handler");
            return 0;
        }
    }
    return 1;
}

PortableLiveGame *portable_live_game_create(
    SimSession *session, PortableWindowRegistry *registry,
    PortableWindowRenderer *renderer, PortableFontSet *fonts,
    const PortableWindowTitlesStringSet *titles,
    PortableWindowTitleProjection *title_projection, Host *host,
    const HostPalette *host_palette, const PortablePalette *palette)
{
    static const int16_t initial_order[] = { 0x1300, 0x1200, 0x0100, 0x0000 };
    static const int16_t window_args[4] = { 0, 0, 0, 0 };
    const PortableWindowRect screen_menu = { 0, 0, LIVE_SCREEN_WIDTH, 0 };
    SimRecoveredHost core_host;
    PortableLiveGame *game;
    size_t i;
    if (session == NULL || registry == NULL || renderer == NULL || fonts == NULL ||
        titles == NULL || title_projection == NULL || host == NULL ||
        host_palette == NULL || palette == NULL ||
        !session->new_game_ready || !session->resources_ready ||
        !session->advice.loaded ||
        renderer->framebuffer == NULL || renderer->database != session->window_database ||
        registry != session->window_registry || !registry->initialized ||
        renderer->framebuffer->width != LIVE_SCREEN_WIDTH ||
        renderer->framebuffer->height != LIVE_SCREEN_HEIGHT)
        return NULL;
    game = (PortableLiveGame *)calloc(1, sizeof(*game));
    if (game == NULL) return NULL;
    game->session = session;
    game->registry = registry;
    game->renderer = renderer;
    game->fonts = fonts;
    game->titles = titles;
    game->title_projection = title_projection;
    game->host = host;
    game->host_palette = host_palette;
    game->palette = palette;
    game->mode_percent = 1;
    game->caste_percent = 1;
    game->started_ns = host_time_ns();
    game->snapshot_session = (SimSession *)malloc(sizeof(*game->snapshot_session));
    if (game->snapshot_session == NULL) {
        set_error(game, "could not allocate source edit snapshot projection");
        goto fail;
    }
    memcpy(game->snapshot_session, session, sizeof(*game->snapshot_session));
    if (portable_window_registry_load(registry, 4) !=
            PORTABLE_WINDOW_REGISTRY_OK) {
        set_error(game, "source EndGame window resource 0x0400 could not be loaded");
        goto fail;
    }
#ifdef SIMANT_ENABLE_NEW_GAME_NEXT5
    if (portable_window_registry_load(registry, 2) !=
            PORTABLE_WINDOW_REGISTRY_OK) {
        set_error(game, "source DoScenario window resource 0x0200 could not be loaded");
        goto fail;
    }
#endif
    if (portable_window_open_scene_init(registry, NULL, 0, &game->windows) !=
        PORTABLE_WINDOW_OPEN_OK) {
        set_error(game, "could not initialize source open-window state");
        goto fail;
    }
    portable_ribbon_init(&game->ribbons);
    for (i = 0; i < sizeof(initial_order) / sizeof(initial_order[0]); ++i) {
        PortableWindowOpenStatus open_status = portable_window_open_apply(
            registry, &game->windows, initial_order[i], window_args,
            LIVE_SCREEN_WIDTH, LIVE_SCREEN_HEIGHT, &screen_menu,
            &game->open_result);
        if (open_status != PORTABLE_WINDOW_OPEN_OK) {
            set_error(game, portable_window_open_status_string(open_status));
            goto fail;
        }
    }
    if (sim_timing_clock_init_bios(&game->clock, LIVE_PIT_NUMERATOR,
                                   LIVE_PIT_DENOMINATOR) != SIM_TIMING_OK) {
        set_error(game, "could not initialize rational BIOS tick clock");
        goto fail;
    }
    portable_menu_init(&game->menu);
    if (portable_menu_load(&game->menu, &session->shared_database,
                           LIVE_SCREEN_WIDTH) != PORTABLE_MENU_OK) {
        set_error(game, "could not load the source SHARED menu resource");
        goto fail;
    }
    game->source_clip_window = PORTABLE_WINDOW_OPEN_NONE;
    game->previous_mouse_event_tick = -1;
    memset(&core_host, 0, sizeof(core_host));
    core_host.context = game;
    core_host.tick_count = tick_count_provider;
    core_host.query = host_query;
    core_host.effect = host_effect;
    core_host.song_done = song_done_provider;
    core_host.end_game = live_end_game_provider;
#ifdef SIMANT_ENABLE_NEW_GAME_NEXT5
    core_host.scenario_select = live_scenario_select_provider;
#endif
    core_host.audio_driver_ready = 0; /* No DOS PIT/DAC audio driver. */
    core_host.screen_width = LIVE_SCREEN_WIDTH;
    core_host.hardware_profile = registry->profile_id;
    if (sim_recovered_engine_init(&game->engine, session, &core_host) !=
        SIM_RECOVERED_ENGINE_INIT_OK) {
        set_error(game, "recovered core rejected the initialized NewGame session");
        goto fail;
    }
    game->dirty = 1;
    if (!redraw(game)) goto fail;
#if defined(SIMANT_LIVE_GAME_TEST_DIAGNOSTICS) && \
    defined(SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC)
    if (getenv("SIMANT_LIVE_NEWGAME_202_DIAGNOSTIC") != NULL) {
        SimRecoveredEngineStatus action_status;
        game->newgame_202_action_called = 1;
        action_status = sim_recovered_engine_action(&game->engine,
            SIM_RECOVERED_ACTION_DIAGNOSTIC_END_GAME, 0, 0);
        game->newgame_202_action_status = (int16_t)action_status;
        if (action_status != SIM_RECOVERED_ENGINE_OK ||
            game->newgame_202_selection_code != 0x0202 ||
            !game->newgame_202_returned) {
            if (game->error[0] == '\0')
                set_error(game,
                    "bounded EndGame-to-scenario-0x0202 diagnostic did not complete");
            goto fail;
        }
    }
#endif
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    if (getenv("SIMANT_LIVE_END_GAME_SMOKE") != NULL) {
        SimGameOverInput test_input;
        SimRng test_rng = session->rng;
        memset(&test_input, 0, sizeof(test_input));
        test_input.health = 100;
        test_input.scenario = 0;
        test_input.screen_width = LIVE_SCREEN_WIDTH;
        /* This opt-in diagnostic invokes the exact host callback with an
         * isolated input/RNG copy; it never resets or mutates live game state. */
        game->end_game_test_called = 1;
        game->engine.audio_binding.intents = &game->engine.audio_intents;
        game->engine.audio_binding.driver_ready =
            game->engine.host.audio_driver_ready;
        game->engine.audio_binding.song_done = game->engine.host.song_done;
        game->engine.audio_binding.song_done_context =
            game->engine.host.context;
        sim_recovered_audio_bind(&game->engine.audio_binding);
        game->end_game_test_callback_result = game->engine.host.end_game(
            game->engine.host.context, &test_input, &test_rng);
        if (!sim_recovered_audio_unbind(&game->engine.audio_binding)) {
            set_error(game, "could not release diagnostic EndGame audio binding");
            goto fail;
        }
        if (game->end_game_test_callback_result != 0 ||
            !game->end_game_boundary_reached || !game->end_game_opened ||
            !game->end_game_closed) {
            char prior[sizeof(game->error)];
            (void)snprintf(prior, sizeof(prior), "%s", game->error);
            (void)snprintf(game->error, sizeof(game->error),
                "diagnostic EndGame did not stop at NewGame boundary: %.96s",
                prior);
            goto fail;
        }
    }
#endif
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    if (!write_control_geometry(game)) {
        set_error(game, "could not write control geometry diagnostic");
        goto fail;
    }
#endif
    return game;
fail:
    game->faulted = 1;
    return game;
}

int portable_live_game_update(PortableLiveGame *game, uint64_t now_ns)
{
    uint64_t elapsed;
    uint32_t mac_now;
    uint32_t due;
    uint32_t i;
    int16_t speed;
    int16_t delay;
    int pause_exception;
    if (game == NULL || game->faulted || game->quit_requested) return 0;
    if (!game->clock_started) {
        game->last_now_ns = now_ns;
        game->clock_started = 1;
    }
    elapsed = now_ns >= game->last_now_ns ? now_ns - game->last_now_ns : 0;
    game->last_now_ns = now_ns;
    if (sim_timing_advance_nanoseconds(&game->clock, elapsed) != SIM_TIMING_OK) {
        set_error(game, "source BIOS clock could not advance");
        game->faulted = 1;
        return 0;
    }
    mac_now = sim_timing_mac_tick_count(&game->clock);
    speed = game->engine.recovered.fd_3D57_07CC[0];
    pause_exception = game->engine.recovered.fd_50F6_0AA0 != 0 &&
                      game->engine.recovered.fd_50F6_105E < 10;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    if (game->engine.recovered.fd_50F6_047E != 0)
        ++game->paused_update_calls;
#endif
    due = sim_timing_take_due(&game->scheduler, mac_now, speed,
                              game->engine.recovered.fd_50F6_047E,
                              pause_exception);
    if (due != 0) {
        /* m15F8 samples MacTickCount before DoAntSim and advances this
         * iteration's deadline by the selected delay before the call. A long
         * synchronous source modal therefore does not cause catch-up ticks. */
        delay = sim_timing_speed_delay(speed);
        game->scheduler.deadline_mac = mac_now + (delay > 0 ? (uint32_t)delay : 0u);
        game->scheduler.initialized = 1;
        game->scheduler.speed_index = (int8_t)speed;
        due = 1;
    }
    for (i = 0; i < due; ++i) {
        SimRecoveredEngineStatus status;
        status = sim_recovered_engine_tick(&game->engine, NULL);
        if (status != SIM_RECOVERED_ENGINE_OK) {
            if (game->engine.failed_service != NULL)
                (void)snprintf(game->error, sizeof(game->error), "%s: %s",
                    sim_recovered_engine_status_string(status),
                    game->engine.failed_service);
            else
                set_error(game, sim_recovered_engine_status_string(status));
            game->faulted = 1;
            return 0;
        }
        game->dirty = 1;
        if (!dispatch_deferred_host_events(game)) {
            game->faulted = 1;
            return 0;
        }
    }
    if (game->dirty && !redraw(game)) {
        game->faulted = 1;
        return 0;
    }
    return 1;
}

int portable_live_game_event(PortableLiveGame *game, const HostEvent *event)
{
    uint16_t scan;
    int first_keydown = 1;
    if (game == NULL || event == NULL || game->faulted) return 0;
    if (event->kind == HOST_EVENT_QUIT) {
        game->quit_requested = 1;
        return 1;
    }
    if (event->kind == HOST_EVENT_MOUSE_MOVE) {
        game->cursor_x = event->x;
        game->cursor_y = event->y;
        return 1;
    }
    if (event->kind == HOST_EVENT_MOUSE_DOWN || event->kind == HOST_EVENT_MOUSE_UP) {
        if (event->button != 1) {
            if (event->kind == HOST_EVENT_MOUSE_DOWN && event->button == 3 &&
                !reject_registered_right_hotbox(game, event->x, event->y)) {
                game->faulted = 1;
                return 0;
            }
            return 1;
        }
        if (event->kind == HOST_EVENT_MOUSE_DOWN) {
            if (!game->left_down) {
                game->left_down = 1;
                game->cursor_x = event->x;
                game->cursor_y = event->y;
                if (point_in_source_menu_bar(game, event->x, event->y)) {
                    if (!run_source_menu(game, event->x, event->y)) {
                        game->faulted = 1;
                        return 0;
                    }
                    return 1;
                }
                {
                    int handled = 0;
                    if (!run_source_control(game, event->x, event->y, &handled)) {
                        game->faulted = 1;
                        return 0;
                    }
                    if (handled) return 1;
                }
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
                {
                    int handled = 0;
                    if (!run_source_history(game, event->x, event->y, &handled)) {
                        game->faulted = 1;
                        return 0;
                    }
                    if (handled) return 1;
                }
#endif
                if (!enqueue_edit_hotbox(game, event->x, event->y)) {
                    game->faulted = 1;
                    return 0;
                }
                if (game->source_event_count != 0 && !game->source_wait_active) {
                    SimRecoveredEvent source_event;
                    if (!pop_source_event(game, &source_event) ||
                        !process_source_edit_event(game, &source_event)) {
                        game->faulted = 1;
                        return 0;
                    }
                }
            }
        } else {
            /* The verified f_1B73_030F mouse callback does not enqueue the
             * release edge; it only clears StillDown for processEdit. */
            game->left_down = 0;
            game->cursor_x = event->x;
            game->cursor_y = event->y;
        }
        return 1;
    }
    if (event->kind != HOST_EVENT_KEY_DOWN && event->kind != HOST_EVENT_KEY_UP)
        return 1;
    scan = (uint16_t)(event->key >> 8);
    if (event->kind == HOST_EVENT_KEY_UP) {
        size_t i;
        if (scan == 0x1d) game->control_down =
            (event->modifiers & 4u) != 0;
        game->dos_keyboard_flags = event->modifiers;
        for (i = 0; i < game->held_key_count; ++i) {
            if ((game->held_keys[i].key >> 8) == scan) {
                game->held_keys[i] = game->held_keys[game->held_key_count - 1];
                --game->held_key_count;
                break;
            }
        }
        return 1;
    }
    game->dos_keyboard_flags = event->modifiers;
    if (scan == 0x1d) game->control_down =
        (event->modifiers & 4u) != 0;
    if (scan != 0 && scan != 0x1d && scan != 0x2a && scan != 0x36 && scan != 0x38 &&
        game->held_key_count < LIVE_MAX_HELD_KEYS) {
        size_t i;
        for (i = 0; i < game->held_key_count; ++i) {
            if ((game->held_keys[i].key >> 8) == scan) {
                first_keydown = 0;
                break;
            }
        }
        if (i < game->held_key_count) game->held_keys[i] = *event;
        else game->held_keys[game->held_key_count++] = *event;
    }
    /* The recovered Control+keypad path applies one source scroll for each
     * physical key-down edge. SDL key-repeat events are state refreshes, not
     * extra source events, so they must not drive the DDA once per host frame. */
    if (first_keydown && game->control_down && scan != 0) {
        int16_t scroll_x, scroll_y;
        if (portable_input_camera_delta(1, &scan, 1, &scroll_x, &scroll_y) !=
                PORTABLE_INPUT_OK) {
            set_error(game, "source keypad camera input is invalid");
            return 0;
        }
        if (scroll_x != 0 || scroll_y != 0) {
            SimRecoveredEngineStatus action_status = sim_recovered_engine_action(
                &game->engine, SIM_RECOVERED_ACTION_SCROLL, scroll_x, scroll_y);
            if (action_status != SIM_RECOVERED_ENGINE_OK) {
                set_error(game, game->engine.failed_service != NULL ?
                    game->engine.failed_service :
                    sim_recovered_engine_status_string(action_status));
                game->faulted = 1;
                return 0;
            }
            game->dirty = 1;
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
            ++game->scroll_action_calls;
#endif
        }
    }
    {
        int16_t logical;
        PortableInputStatus input_status =
            portable_input_decode_bios_key(event->key, &logical);
        if (input_status == PORTABLE_INPUT_MODIFIER_ONLY ||
            input_status == PORTABLE_INPUT_NO_KEY) return 1;
        if (input_status != PORTABLE_INPUT_OK) {
            set_error(game, portable_input_status_string(input_status));
            return 0;
        }
        {
            PortableInputEffects effects;
            input_status = portable_input_key((uint16_t)logical,
                game->engine.recovered.fd_50F6_047E,
                game->session->world.selected_map_plane,
                game->session->world.yard_mode,
                (game->windows.windows[0x19].flags & PORTABLE_WINDOW_OPEN) != 0,
                &effects);
            if (input_status == PORTABLE_INPUT_UNBOUND) {
                RecoveredState before = game->engine.recovered;
                int16_t handled = 0;
                SimRecoveredEngineStatus key_status;
                /* The recovered main event loop handles Ctrl+keypad camera
                 * movement before it calls YellowCommandKey. Other Ctrl
                 * combinations remain with that special-key route. */
                if (game->control_down) return 1;
                key_status = sim_recovered_engine_yellow_command_key(
                    &game->engine, logical, NULL, &handled);
                if (key_status != SIM_RECOVERED_ENGINE_OK) {
                    set_error(game, game->engine.failed_service != NULL ?
                        game->engine.failed_service :
                        sim_recovered_engine_status_string(key_status));
                    game->faulted = 1;
                    return 0;
                }
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
                ++game->yellow_key_calls;
                game->yellow_key_last = logical;
                game->yellow_key_last_result = handled;
                if (handled) ++game->yellow_key_handled_calls;
                else {
                    ++game->yellow_key_unhandled_calls;
                    if (memcmp(&before, &game->engine.recovered,
                               sizeof(before)) == 0)
                        ++game->yellow_key_unhandled_unchanged_calls;
                }
#else
                if (!handled && memcmp(&before, &game->engine.recovered,
                                       sizeof(before)) != 0) {
                    set_error(game, "unhandled source YellowCommandKey changed recovered state");
                    game->faulted = 1;
                    return 0;
                }
#endif
                if (!handled) return 1;
                game->dirty = 1;
                return redraw(game);
            }
            if (input_status != PORTABLE_INPUT_OK) {
                set_error(game, portable_input_status_string(input_status));
                return 0;
            }
            return apply_input_effects(game, &effects);
        }
    }
}

void portable_live_game_destroy(PortableLiveGame *game)
{
#ifdef SIMANT_LIVE_GAME_TEST_DIAGNOSTICS
    if (game != NULL) {
        const char *base = getenv("SIMANT_LIVE_SMOKE_STATE_REPORT");
        if (base != NULL && base[0] != '\0') {
            char path[1024];
            FILE *file;
            unsigned i;
            if (snprintf(path, sizeof(path), "%s.recovered.bin", base) <
                    (int)sizeof(path) && (file = fopen(path, "wb")) != NULL) {
                (void)fwrite(&game->engine.recovered, 1,
                             sizeof(game->engine.recovered), file);
                (void)fclose(file);
            }
            if (snprintf(path, sizeof(path), "%s.normalized.bin", base) <
                    (int)sizeof(path) && (file = fopen(path, "wb")) != NULL) {
                RecoveredState normalized = game->engine.recovered;
                unsigned pointer_index;
                memset(&normalized.AdviceStrs, 0, sizeof(normalized.AdviceStrs));
                for (pointer_index = 0; pointer_index < 40; ++pointer_index)
                    memset(&normalized.fd_3D57_0852[pointer_index], 0,
                           sizeof(normalized.fd_3D57_0852[pointer_index]));
                memset(&normalized.fd_50F6_02BA, 0,
                       sizeof(normalized.fd_50F6_02BA));
                memset(&normalized.fd_50F6_034C, 0,
                       sizeof(normalized.fd_50F6_034C));
                memset(&normalized.fd_50F6_0B22, 0,
                       sizeof(normalized.fd_50F6_0B22));
                memset(&normalized.g_5AAC, 0, sizeof(normalized.g_5AAC));
                (void)fwrite(&normalized, 1, sizeof(normalized), file);
                (void)fclose(file);
            }
            if (snprintf(path, sizeof(path), "%s.rng.bin", base) <
                    (int)sizeof(path) && (file = fopen(path, "wb")) != NULL) {
                (void)fwrite(&game->session->rng, 1,
                             sizeof(game->session->rng), file);
                (void)fclose(file);
            }
            if (snprintf(path, sizeof(path), "%s.stats.json", base) <
                    (int)sizeof(path) && (file = fopen(path, "wb")) != NULL) {
                (void)fprintf(file,
                    "{\"completed_ticks\":%llu,\"bios_tick_count\":%u,"
                    "\"mac_tick_count\":%u,\"wall_elapsed_ns\":%llu,"
                    "\"recovered_state_size\":%zu,\"normalized_state_size\":%zu,"
                    "\"rng_state_size\":%zu,\"source_pause\":%d,"
                    "\"source_speed\":%d,\"menu_resource_id\":%d,"
                    "\"camera_x\":%d,\"camera_y\":%d,\"scroll_action_calls\":%llu,"
                    "\"menu_loaded\":%s,\"active_clip_window\":%d,"
                    "\"pause_action_calls\":%llu,\"pause_start_ticks\":%llu,"
                    "\"pause_end_ticks\":%llu,\"pause_duration_ns\":%llu,"
                    "\"paused_update_calls\":%llu,"
                    "\"speed_action_calls\":[%llu,%llu,%llu,%llu],"
                    "\"menu_item_state_calls\":%llu,\"menu_item_text_calls\":%llu,"
                    "\"edit_hotbox_clicks\":%llu,\"edit_events_delivered\":%llu,"
                    "\"edit_double_clicks\":%llu,\"edit_queue_remaining\":%zu,"
                    "\"yellow_key_calls\":%llu,\"yellow_key_handled_calls\":%llu,"
                    "\"yellow_key_unhandled_calls\":%llu,"
                    "\"yellow_key_unhandled_unchanged_calls\":%llu,"
                    "\"yellow_key_last\":%d,\"yellow_key_last_result\":%d,"
                    "\"overview_render_calls\":%llu,\"overview_mode\":%d,"
                    "\"overview_image_rect\":[%d,%d,%d,%d],"
                    "\"overview_cursor_rect\":[%d,%d,%d,%d],"
                    "\"event_goal_active\":%d,\"event_goal_mode\":%d,"
                    "\"event_goal_x\":%d,\"event_goal_y\":%d,"
                    "\"event_goal_plane\":%d,"
                    "\"event_left_down\":%u,"
                    "\"edit_object4_rect\":[%d,%d,%d,%d],\"edit_object4_flags\":%u,"
                    "\"edit_object4_type\":%u,\"edit_object4_value\":%d,"
                    "\"front_window\":%d,\"source_goal_active\":%d,"
                    "\"source_goal_mode\":%d,\"source_goal_x\":%d,"
                    "\"source_goal_y\":%d,\"left_down\":%u,"
                    "\"effects\":[",
                    (unsigned long long)game->engine.completed_ticks,
                    sim_timing_tick_count(&game->clock),
                    sim_timing_mac_tick_count(&game->clock),
                    (unsigned long long)(host_time_ns() >= game->started_ns ?
                        host_time_ns() - game->started_ns : 0),
                    sizeof(game->engine.recovered), sizeof(game->engine.recovered),
                    sizeof(game->session->rng),
                    game->engine.recovered.fd_50F6_047E,
                    game->engine.recovered.fd_3D57_07CC[0],
                    game->menu.resource_id,
                    game->engine.recovered.fd_50F6_0508[0],
                    game->engine.recovered.fd_50F6_0508[1],
                    (unsigned long long)game->scroll_action_calls,
                    game->menu.loaded ? "true" : "false",
                    game->source_clip_window,
                    (unsigned long long)game->pause_action_calls,
                    (unsigned long long)game->pause_start_ticks,
                    (unsigned long long)game->pause_end_ticks,
                    (unsigned long long)game->pause_duration_ns,
                    (unsigned long long)game->paused_update_calls,
                    (unsigned long long)game->speed_action_calls[0],
                    (unsigned long long)game->speed_action_calls[1],
                    (unsigned long long)game->speed_action_calls[2],
                    (unsigned long long)game->speed_action_calls[3],
                    (unsigned long long)game->menu_item_state_calls,
                    (unsigned long long)game->menu_item_text_calls,
                    (unsigned long long)game->edit_hotbox_clicks,
                    (unsigned long long)game->edit_events_delivered,
                    (unsigned long long)game->edit_double_clicks,
                    game->source_event_count,
                    (unsigned long long)game->yellow_key_calls,
                    (unsigned long long)game->yellow_key_handled_calls,
                    (unsigned long long)game->yellow_key_unhandled_calls,
                    (unsigned long long)game->yellow_key_unhandled_unchanged_calls,
                    game->yellow_key_last,
                    game->yellow_key_last_result,
                    (unsigned long long)game->overview_render_calls,
                    game->overview_mode,
                    game->overview_image_rect[0], game->overview_image_rect[1],
                    game->overview_image_rect[2], game->overview_image_rect[3],
                    game->overview_cursor_rect[0], game->overview_cursor_rect[1],
                    game->overview_cursor_rect[2], game->overview_cursor_rect[3],
                    game->edit_goal_active_after_event,
                    game->edit_goal_mode_after_event,
                    game->edit_goal_x_after_event,
                    game->edit_goal_y_after_event,
                    game->edit_goal_plane_after_event,
                    game->edit_left_down_after_event,
                    game->registry->slots[0].window.objects[4].rect.left,
                    game->registry->slots[0].window.objects[4].rect.top,
                    game->registry->slots[0].window.objects[4].rect.right,
                    game->registry->slots[0].window.objects[4].rect.bottom,
                    game->registry->slots[0].window.objects[4].flags,
                    game->registry->slots[0].window.objects[4].type,
                    game->registry->slots[0].window.objects[4].value,
                    game->windows.front_window_id,
                    game->engine.recovered.fd_50F6_0AA0,
                    game->engine.recovered.fd_50F6_0A8E,
                    game->engine.recovered.fd_50F6_08E2,
                    game->engine.recovered.fd_50F6_09F0,
                    game->left_down);
                for (i = 0; i <= SIM_RECOVERED_EFFECT_GRAPHICS_LINE; ++i)
                    (void)fprintf(file, "%s%llu", i == 0 ? "" : ",",
                                  (unsigned long long)game->effect_calls[i]);
                (void)fprintf(file, "],\"queries\":[");
                for (i = 0; i <= SIM_RECOVERED_QUERY_BUTTON; ++i)
                    (void)fprintf(file, "%s%llu", i == 0 ? "" : ",",
                                  (unsigned long long)game->query_calls[i]);
                (void)fprintf(file,
                    "],\"control_event_calls\":%llu,\"control_last_code\":%u,"
                    "\"mode_percent\":%d,\"caste_percent\":%d,"
                    "\"mode_selector\":%d,\"caste_selector\":%d,"
                    "\"mode_auto\":%d,\"caste_auto\":%d,"
                    "\"mode_level\":[%u,%u,%u],\"caste_level\":[%u,%u,%u]}\n",
                    (unsigned long long)game->control_event_calls,
                    game->control_last_code, game->mode_percent, game->caste_percent,
                    game->session->setup_controls.mode_current,
                    game->session->setup_controls.caste_current,
                    game->session->setup_controls.mode_auto,
                    game->session->setup_controls.caste_auto,
                    game->session->setup_controls.mode_level.frac,
                    game->session->setup_controls.mode_level.mid,
                    game->session->setup_controls.mode_level.weight,
                    game->session->setup_controls.caste_level.frac,
                    game->session->setup_controls.caste_level.mid,
                    game->session->setup_controls.caste_level.weight);
                (void)fclose(file);
            }
            if (snprintf(path, sizeof(path), "%s.endgame.json", base) <
                    (int)sizeof(path) && (file = fopen(path, "wb")) != NULL) {
                (void)fprintf(file,
                    "{\"schema\":\"portable-live-end-game-smoke-v1\","
                    "\"diagnostic_callback_invoked\":%s,"
                    "\"callback_result\":%d,\"opened\":%s,\"closed\":%s,"
                    "\"restart_boundary_reached\":%s,\"boundary\":\"%s\","
                    "\"score\":%ld,\"scenario_index\":%u,\"level_index\":%u,"
                    "\"window_rect\":[%d,%d,%d,%d],"
                    "\"text_object_rects\":[[%d,%d,%d,%d],[%d,%d,%d,%d],"
                    "[%d,%d,%d,%d]],\"open_tick\":%u,\"close_tick\":%u,"
                    "\"wait_delay_ticks\":%u,\"modal_event_polls\":%llu,"
                    "\"dialog_abort_polls\":%llu,\"song_done_polls\":%llu,"
                    "\"song_requests\":%llu,\"rendered_modal_frames\":%llu,"
                    "\"modal_frame_saved\":%s,\"logical_key\":%d,"
                    "\"quit_seen\":%s,\"audio_driver_ready\":%d,"
                    "\"error\":\"%s\"}\n",
                    game->end_game_test_called ? "true" : "false",
                    game->end_game_test_callback_result,
                    game->end_game_opened ? "true" : "false",
                    game->end_game_closed ? "true" : "false",
                    game->end_game_boundary_reached ? "true" : "false",
                    game->end_game_boundary,
                    (long)game->end_game_score,
                    (unsigned)game->end_game_scenario_index,
                    (unsigned)game->end_game_level_index,
                    game->end_game_window_rect[0], game->end_game_window_rect[1],
                    game->end_game_window_rect[2], game->end_game_window_rect[3],
                    game->end_game_object_rects[0], game->end_game_object_rects[1],
                    game->end_game_object_rects[2], game->end_game_object_rects[3],
                    game->end_game_object_rects[4], game->end_game_object_rects[5],
                    game->end_game_object_rects[6], game->end_game_object_rects[7],
                    game->end_game_object_rects[8], game->end_game_object_rects[9],
                    game->end_game_object_rects[10], game->end_game_object_rects[11],
                    game->end_game_open_tick, game->end_game_close_tick,
                    game->end_game_wait_delay,
                    (unsigned long long)game->end_game_polls,
                    (unsigned long long)game->end_game_dialog_abort_polls,
                    (unsigned long long)game->end_game_song_done_polls,
                    (unsigned long long)game->end_game_song_requests,
                    (unsigned long long)game->end_game_rendered_frames,
                    game->end_game_modal_frame_saved ? "true" : "false",
                    game->end_game_last_key,
                    game->end_game_quit_seen ? "true" : "false",
                    game->engine.audio_binding.driver_ready,
                    game->error);
                (void)fclose(file);
            }
#ifdef SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC
            if (snprintf(path, sizeof(path), "%s.newgame202.json", base) <
                    (int)sizeof(path) && (file = fopen(path, "wb")) != NULL) {
                (void)fprintf(file,
                    "{\"schema\":\"portable-live-newgame-202-action-v1\","
                    "\"diagnostic_action_called\":%s,"
                    "\"diagnostic_action_status\":%d,"
                    "\"scenario_result_code\":%d,"
                    "\"source_newgame_returned\":%s,"
                    "\"source_newgame_result\":%d,"
                    "\"endgame_opened\":%s,\"endgame_closed\":%s,"
                    "\"scenario_index_after\":%u,"
                    "\"selected_map_plane_after\":%d,"
                    "\"completed_ticks_after\":%llu,"
                    "\"gameover_callback_count\":%llu,"
                    "\"gameover_entry_completed_ticks\":%llu,"
                    "\"gameover_callback_completed\":%s,"
                    "\"gameover_input\":{\"scenario\":%d,\"world_ticks\":%d,"
                    "\"health\":%d,\"blue_workers\":%d,\"red_workers\":%d,"
                    "\"losing_side\":%d,\"sound_enabled\":%u,"
                    "\"history_cursor\":%d,\"history_count\":%d,"
                    "\"food_total\":%d,\"food_used\":%d,"
                    "\"blue_colony_score\":%d,\"colony_score_a\":%d,"
                    "\"colony_score_b\":%d,\"screen_width\":%u},"
                    "\"rng_before\":{\"s\":%u,\"c\":%lu},"
                    "\"rng_after\":{\"s\":%u,\"c\":%lu},"
                    "\"engine_status\":%d,\"engine_failed_service\":\"%s\","
                    "\"error\":\"%s\"}\n",
                    game->newgame_202_action_called ? "true" : "false",
                    game->newgame_202_action_status,
                    game->newgame_202_selection_code,
                    game->newgame_202_returned ? "true" : "false",
                    game->newgame_202_source_result,
                    game->end_game_opened ? "true" : "false",
                    game->end_game_closed ? "true" : "false",
                    (unsigned)game->engine.recovered.fd_50F6_0EAC,
                    game->engine.recovered.fd_3D57_07C8[0],
                    (unsigned long long)game->engine.completed_ticks,
                    (unsigned long long)game->gameover_callback_count,
                    (unsigned long long)game->gameover_entry_completed_ticks,
                    game->gameover_callback_completed ? "true" : "false",
                    game->gameover_callback_input.scenario,
                    game->gameover_callback_input.world_ticks,
                    game->gameover_callback_input.health,
                    game->gameover_callback_input.blue_workers,
                    game->gameover_callback_input.red_workers,
                    game->gameover_callback_input.losing_side,
                    game->gameover_callback_input.sound_enabled,
                    game->gameover_callback_input.history_cursor,
                    game->gameover_callback_input.history_count,
                    game->gameover_callback_input.food_total,
                    game->gameover_callback_input.food_used,
                    game->gameover_callback_input.blue_colony_score,
                    game->gameover_callback_input.colony_score_a,
                    game->gameover_callback_input.colony_score_b,
                    game->gameover_callback_input.screen_width,
                    game->gameover_callback_rng_before.s_state,
                    (unsigned long)game->gameover_callback_rng_before.c_state,
                    game->gameover_callback_rng_after.s_state,
                    (unsigned long)game->gameover_callback_rng_after.c_state,
                    (int)game->engine.status,
                    game->engine.failed_service != NULL ?
                        game->engine.failed_service : "",
                    game->error);
                (void)fclose(file);
            }
#endif
        }
    }
#endif
    if (game != NULL) {
#ifdef SIMANT_ENABLE_HISTORY_UI_NEXT10
        portable_history_active_resources_free(&game->history_resources);
#endif
        portable_menu_release(&game->menu);
        free(game->snapshot_session);
    }
    free(game);
}

const char *portable_live_game_error(const PortableLiveGame *game)
{
    return game == NULL ? "live game is not initialized" : game->error;
}

int portable_live_game_quit_requested(const PortableLiveGame *game)
{
    return game != NULL && game->quit_requested;
}

uint64_t portable_live_game_completed_ticks(const PortableLiveGame *game)
{
    return game == NULL ? 0 : game->engine.completed_ticks;
}

int portable_live_game_needs_present(const PortableLiveGame *game)
{
    return game != NULL && game->frame_pending;
}

void portable_live_game_mark_presented(PortableLiveGame *game)
{
    if (game != NULL) game->frame_pending = 0;
}

#endif
