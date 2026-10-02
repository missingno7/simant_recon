#include <SDL3/SDL.h>

#include "../../ui_model/menus/interaction.h"
#include "../../platform/host.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Rect { int left, top, right, bottom; } Rect;
typedef struct Target {
    int title_x, title_y;
    int row_x[2], row_y[2];
    int pause_title_x, pause_title_y, pause_row_x, pause_row_y;
    int mode_button[8], caste_button[8];
    Rect mode_triangle, caste_triangle;
    int geometry_ready;
    int menu_index, mode_row, caste_row;
} Target;

static Target target;
static SDL_TimerID timer_id;
static volatile unsigned phase, pushed_events, failures;
static unsigned long long operation_mask;
static HostEvent control_pointer_events[16];
static unsigned control_pointer_event_count;

int __real_host_poll_event(Host *host, HostEvent *event);

int __wrap_host_poll_event(Host *host, HostEvent *event)
{
    const int result = __real_host_poll_event(host, event);
    if (result > 0 && target.geometry_ready &&
        (event->kind == HOST_EVENT_MOUSE_MOVE ||
         event->kind == HOST_EVENT_MOUSE_DOWN ||
         event->kind == HOST_EVENT_MOUSE_UP) && event->button <= 1) {
        const Rect *triangles[2] = {&target.mode_triangle, &target.caste_triangle};
        unsigned i;
        for (i = 0; i < 2; ++i) {
            const Rect *r = triangles[i];
            if (event->x >= r->left && event->x <= r->right &&
                event->y >= r->top && event->y <= r->bottom) {
                if (control_pointer_event_count < 16)
                    control_pointer_events[control_pointer_event_count++] = *event;
                break;
            }
        }
    }
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

static int read_geometry_rect(unsigned object_id, Rect *rect)
{
    const char *path = getenv("SIMANT_LIVE_CONTROL_GEOMETRY_REPORT");
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
    if (fread(data, 1, (size_t)size, file) != (size_t)size) {
        free(data);
        goto done;
    }
    data[size] = '\0';
    (void)snprintf(needle, sizeof(needle), "\"object_id\":%u", object_id);
    at = strstr(data, needle);
    if (at != NULL && (end = strstr(at, "\"rect\":[")) != NULL &&
        end - at < 160 && sscanf(end, "\"rect\":[%d,%d,%d,%d]",
            &rect->left, &rect->top, &rect->right, &rect->bottom) == 4)
        ok = 1;
    free(data);
done:
    (void)fclose(file);
    return ok;
}

static int center(const Rect *r, int *x, int *y)
{
    if (r->right <= r->left || r->bottom <= r->top) return 0;
    *x = (r->left + r->right) / 2;
    *y = (r->top + r->bottom) / 2;
    return 1;
}

static int prepare_menu(void)
{
    PortableDatabase database = {0};
    PortableMenuBar menu;
    PortableMenuLayout layout;
    PortableMenuDrawCommand commands[64];
    PortableMenuInteraction interaction;
    size_t count = 0, title = (size_t)-1, speed = (size_t)-1, row;
    size_t mode = (size_t)-1, caste = (size_t)-1, pause = (size_t)-1;
    int result = 0;
    if (portable_db_open(&database, "assets/SHARED") != PORTABLE_DB_OK) return 0;
    portable_menu_init(&menu);
    if (portable_menu_load(&menu, &database, 640) != PORTABLE_MENU_OK ||
        portable_menu_build_draw_plan(&menu, 1, (PortableMenuRect){0,0,640,350},
            640, 8, 14, 0, &layout, commands, 64, &count) != PORTABLE_MENU_OK)
        goto done;
    for (row = 0; row < menu.titles.count; ++row)
        if (text_has(&menu, portable_menu_title(&menu, row), "window")) title = row;
        else if (text_has(&menu, portable_menu_title(&menu, row), "speed")) speed = row;
    if (title == (size_t)-1 || speed == (size_t)-1 ||
        portable_menu_interaction_init_from_bar(
            &interaction, &menu, &layout, title, 640, 350, 14, 8, 0) !=
            PORTABLE_MENU_INTERACTION_RUNNING) goto done;
    for (row = 0; row < interaction.item_count; ++row) {
        const PortableMenuString *item = portable_menu_item(&menu, title, row);
        if (text_has(&menu, item, "behavior")) mode = row;
        if (text_has(&menu, item, "caste")) caste = row;
    }
    if (mode == (size_t)-1 || caste == (size_t)-1 || mode >= interaction.item_count ||
        caste >= interaction.item_count || !interaction.row_enabled[mode] ||
        !interaction.row_enabled[caste]) goto done;
    target.menu_index = (int)title;
    target.mode_row = (int)mode;
    target.caste_row = (int)caste;
    target.title_x = (layout.title_rects[title].left + layout.title_rects[title].right) / 2;
    target.title_y = (layout.title_rects[title].top + layout.title_rects[title].bottom) / 2;
    target.row_x[0] = (interaction.row_rects[mode].left + interaction.row_rects[mode].right) / 2;
    target.row_y[0] = (interaction.row_rects[mode].top + interaction.row_rects[mode].bottom) / 2;
    target.row_x[1] = (interaction.row_rects[caste].left + interaction.row_rects[caste].right) / 2;
    target.row_y[1] = (interaction.row_rects[caste].top + interaction.row_rects[caste].bottom) / 2;
    if ((((title << 4) + mode - 0x2ffu) & 0xffffu) != 0xfd13u ||
        (((title << 4) + caste - 0x2ffu) & 0xffffu) != 0xfd14u) goto done;
    if (portable_menu_interaction_init_from_bar(&interaction, &menu, &layout,
            speed, 640, 350, 14, 8, 0) != PORTABLE_MENU_INTERACTION_RUNNING)
        goto done;
    for (row = 0; row < interaction.item_count; ++row)
        if (text_has(&menu, portable_menu_item(&menu, speed, row), "pause")) pause = row;
    if (pause == (size_t)-1 || !interaction.row_enabled[pause] ||
        ((((speed << 4) + pause - 0x2ffu) & 0xffffu) != 0xfd41u)) goto done;
    target.pause_title_x = (layout.title_rects[speed].left + layout.title_rects[speed].right) / 2;
    target.pause_title_y = (layout.title_rects[speed].top + layout.title_rects[speed].bottom) / 2;
    target.pause_row_x = (interaction.row_rects[pause].left + interaction.row_rects[pause].right) / 2;
    target.pause_row_y = (interaction.row_rects[pause].top + interaction.row_rects[pause].bottom) / 2;
    result = 1;
done:
    portable_menu_release(&menu);
    portable_db_close(&database);
    return result;
}

static int prepare_game_geometry(void)
{
    int y;
    if (!read_geometry_rect(0x1204, &((Rect){0})) ||
        !read_geometry_rect(0x1205, &((Rect){0})) ||
        !read_geometry_rect(0x1208, &((Rect){0})) ||
        !read_geometry_rect(0x1210, &((Rect){0})) ||
        !read_geometry_rect(0x1304, &((Rect){0})) ||
        !read_geometry_rect(0x1305, &((Rect){0})) ||
        !read_geometry_rect(0x1308, &((Rect){0})) ||
        !read_geometry_rect(0x1310, &((Rect){0})) ||
        !read_geometry_rect(0x120d, &target.mode_triangle) ||
        !read_geometry_rect(0x130d, &target.caste_triangle)) return 0;
    {
        Rect r;
        if (!read_geometry_rect(0x1204, &r) || !center(&r,&target.mode_button[0],&target.mode_button[1])) return 0;
        if (!read_geometry_rect(0x1205, &r) || !center(&r,&target.mode_button[2],&target.mode_button[3])) return 0;
        if (!read_geometry_rect(0x1208, &r) || !center(&r,&target.mode_button[4],&target.mode_button[5])) return 0;
        if (!read_geometry_rect(0x1210, &r) || !center(&r,&target.mode_button[6],&target.mode_button[7])) return 0;
        if (!read_geometry_rect(0x1304, &r) || !center(&r,&target.caste_button[0],&target.caste_button[1])) return 0;
        if (!read_geometry_rect(0x1305, &r) || !center(&r,&target.caste_button[2],&target.caste_button[3])) return 0;
        if (!read_geometry_rect(0x1308, &r) || !center(&r,&target.caste_button[4],&target.caste_button[5])) return 0;
        if (!read_geometry_rect(0x1310, &r) || !center(&r,&target.caste_button[6],&target.caste_button[7])) return 0;
    }
    (void)y;
    target.geometry_ready = 1;
    return 1;
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
{
    return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN,x,y) &&
           push_mouse(SDL_EVENT_MOUSE_BUTTON_UP,x,y);
}

static int select_window(unsigned row)
{
    return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN,target.title_x,target.title_y) &&
           push_mouse(SDL_EVENT_MOUSE_MOTION,target.row_x[row],target.row_y[row]) &&
           push_mouse(SDL_EVENT_MOUSE_BUTTON_UP,target.row_x[row],target.row_y[row]);
}

static int toggle_pause(void)
{
    return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN,target.pause_title_x,target.pause_title_y) &&
           push_mouse(SDL_EVENT_MOUSE_MOTION,target.pause_row_x,target.pause_row_y) &&
           push_mouse(SDL_EVENT_MOUSE_BUTTON_UP,target.pause_row_x,target.pause_row_y);
}

static int drag(const Rect *r)
{
    int x, y, end_x, end_y;
    if (!center(r,&x,&y)) return 0;
    end_x = r->left + (r->right-r->left)/2;
    end_y = r->bottom - 3;
    return push_mouse(SDL_EVENT_MOUSE_BUTTON_DOWN,x,y) &&
           push_mouse(SDL_EVENT_MOUSE_MOTION,end_x,end_y) &&
           push_mouse(SDL_EVENT_MOUSE_BUTTON_UP,end_x,end_y);
}

static Uint32 SDLCALL inject_controls(void *context, SDL_TimerID id, Uint32 interval)
{
    (void)context; (void)id; (void)interval;
    if (!target.geometry_ready && !prepare_game_geometry()) return 100;
    switch (phase) {
    case 0: if (!toggle_pause()) ++failures; break;
    case 1: if (!select_window(0)) ++failures; break;
    case 2: if (!click(target.mode_button[0],target.mode_button[1])) ++failures; operation_mask |= 1ull<<0; break;
    case 3: if (!click(target.mode_button[2],target.mode_button[3])) ++failures; operation_mask |= 1ull<<1; break;
    case 4: if (!click(target.mode_button[4],target.mode_button[5])) ++failures; operation_mask |= 1ull<<2; break;
    case 5: if (!click(target.mode_button[6],target.mode_button[7])) ++failures; operation_mask |= 1ull<<3; break;
    case 6: if (!drag(&target.mode_triangle)) ++failures; operation_mask |= 1ull<<4; break;
    case 7: if (!select_window(1)) ++failures; break;
    case 8: if (!click(target.caste_button[0],target.caste_button[1])) ++failures; operation_mask |= 1ull<<5; break;
    case 9: if (!click(target.caste_button[2],target.caste_button[3])) ++failures; operation_mask |= 1ull<<6; break;
    case 10: if (!click(target.caste_button[4],target.caste_button[5])) ++failures; operation_mask |= 1ull<<7; break;
    case 11: if (!click(target.caste_button[6],target.caste_button[7])) ++failures; operation_mask |= 1ull<<8; break;
    case 12: if (!drag(&target.caste_triangle)) ++failures; operation_mask |= 1ull<<9; break;
    case 13: if (!toggle_pause()) ++failures; break;
    default: return 0;
    }
    ++phase;
    return 250;
}

__attribute__((constructor)) static void start_physical_control_timer(void)
{
    if (prepare_menu()) timer_id = SDL_AddTimer(350, inject_controls, NULL);
    else ++failures;
}

__attribute__((destructor)) static void write_injection_report(void)
{
    const char *path = getenv("SIMANT_LIVE_CONTROL_EVENT_REPORT");
    FILE *file;
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    if (path == NULL || *path == '\0') return;
    file = fopen(path,"wb");
    if (file == NULL) return;
    (void)fprintf(file,
        "{\"schema\":\"portable-live-physical-controls-inject-v1\","
        "\"phase_count\":%u,\"pushed_event_count\":%u,\"injection_failures\":%u,"
        "\"operation_mask\":%llu,\"window_menu_index\":%d,"
        "\"mode_menu_item\":\"Behavior\",\"caste_menu_item\":\"Caste\","
        "\"mode_row\":%d,\"caste_row\":%d,\"mode_command\":64787,"
        "\"caste_command\":64788,\"pause_command\":64833,\"pause_toggle_count\":2,"
        "\"control_action_order\":[\"mode:auto-on\",\"mode:auto-off\","
        "\"mode:preset-3\",\"mode:percent\",\"mode:drag\","
        "\"caste:auto-on\",\"caste:auto-off\",\"caste:preset-3\","
        "\"caste:percent\",\"caste:drag\"],"
        "\"mode_triangle_rect\":[%d,%d,%d,%d],\"caste_triangle_rect\":[%d,%d,%d,%d],"
        "\"converted_control_pointer_events\":[",
        phase,pushed_events,failures,operation_mask,target.menu_index,target.mode_row,
        target.caste_row,target.mode_triangle.left,target.mode_triangle.top,
        target.mode_triangle.right,target.mode_triangle.bottom,target.caste_triangle.left,
        target.caste_triangle.top,target.caste_triangle.right,target.caste_triangle.bottom);
    for (unsigned i = 0; i < control_pointer_event_count; ++i) {
        const HostEvent *event = &control_pointer_events[i];
        (void)fprintf(file, "%s{\"kind\":%d,\"x\":%d,\"y\":%d,\"button\":%u}",
            i == 0 ? "" : ",", (int)event->kind, event->x, event->y,
            (unsigned)event->button);
    }
    (void)fprintf(file, "]}\n");
    (void)fclose(file);
}
