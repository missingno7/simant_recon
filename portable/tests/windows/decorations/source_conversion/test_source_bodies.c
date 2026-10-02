#include "../../../../game/resources/database.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct Pt { int16_t x, y; } Point;
typedef struct Rect { int16_t left, top, right, bottom; } Rect;
typedef struct PortableDecorationWindow {
    Rect rect;
    int16_t flags;
    const uint8_t *state;
} PortableDecorationWindow;

typedef enum EventKind { EVENT_LOOKUP = 1, EVENT_REGISTER, EVENT_UNREGISTER } EventKind;
typedef struct Event {
    EventKind kind;
    int16_t id, mode;
    Rect rect;
} Event;

static PortableDatabase database;
static Event events[32];
static size_t event_count;
static int16_t last_metric_id;
static int failure;
static int run_failed;

static void source_metric(Point *size, int16_t object_id);
static void source_register(Rect *rect, int16_t mode);
static void source_unregister(int16_t mode);

#define far
#define _fastcall
#define f_208F_0419 source_metric
#define f_1FD2_03EB source_register
#define f_1FD2_0438 source_unregister
#define int int16_t
#include "extracted_bodies.inc"
#undef int
#undef f_1FD2_0438
#undef f_1FD2_03EB
#undef f_208F_0419
#undef _fastcall
#undef far

static void push_event(Event event)
{
    if (event_count >= sizeof(events) / sizeof(events[0])) {
        failure = 1;
        return;
    }
    events[event_count++] = event;
}

static int16_t id_for_mode(int16_t mode)
{
    switch ((uint16_t)mode) {
    case 0xf083: return 0x64;
    case 0xf084: return 0x70;
    case 0xf085: return last_metric_id;
    case 0xf088: return 0x65;
    case 0xf082: return 0x69;
    default: return -1;
    }
}

static void source_metric(Point *size, int16_t object_id)
{
    PortableDbRecord record;
    Event event;
    PortableDbStatus status = portable_db_load(&database, object_id, 2, &record);
    event.kind = EVENT_LOOKUP;
    event.id = object_id;
    event.mode = 0;
    memset(&event.rect, 0, sizeof(event.rect));
    push_event(event);
    last_metric_id = object_id;
    if (status != PORTABLE_DB_OK) {
        /* Mirrors f_208F_0419's missing-object 1x1 result. */
        size->x = 1;
        size->y = 1;
        return;
    }
    if (record.size < 12) {
        failure = 1;
        portable_db_record_free(&record);
        return;
    }
    size->x = (int16_t)(record.data[8] | (record.data[9] << 8));
    size->y = (int16_t)(record.data[10] | (record.data[11] << 8));
    portable_db_record_free(&record);
}

static void source_register(Rect *rect, int16_t mode)
{
    Event event;
    event.kind = EVENT_REGISTER;
    event.id = id_for_mode(mode);
    event.mode = mode;
    event.rect = *rect;
    if (event.id < 0)
        failure = 1;
    push_event(event);
}

static void source_unregister(int16_t mode)
{
    Event event;
    event.kind = EVENT_UNREGISTER;
    event.id = id_for_mode(mode);
    event.mode = mode;
    memset(&event.rect, 0, sizeof(event.rect));
    if (event.id < 0)
        failure = 1;
    push_event(event);
}

static void reset_window(PortableDecorationWindow *window, uint8_t state[0x40],
                         int16_t flags, int margin)
{
    memset(window, 0, sizeof(*window));
    memset(state, 0, 0x40);
    window->rect = (Rect){10, 20, 210, 120};
    window->flags = flags;
    state[0x28] = (uint8_t)margin;
    window->state = state;
}

static void print_events(const char *label, PortableDecorationWindow *window,
                         int show, int margin)
{
    uint8_t state[0x40];
    size_t i;
    reset_window(window, state, window->flags, margin);
    event_count = 0;
    last_metric_id = -1;
    failure = 0;
    f_2505_06B9((int16_t)show, window);
    if (failure) {
        fprintf(stderr, "source-body service failure in %s\n", label);
        run_failed = 1;
        return;
    }
    printf("{\"label\":\"%s\",\"steps\":[", label);
    for (i = 0; i < event_count; ++i) {
        const Event *e = &events[i];
        if (i) putchar(',');
        if (e->kind == EVENT_LOOKUP) {
            printf("{\"kind\":\"lookup\",\"id\":%d}", e->id);
        } else if (e->kind == EVENT_UNREGISTER) {
            printf("{\"kind\":\"unregister\",\"id\":%d,\"mode\":%d}",
                   e->id, (uint16_t)e->mode);
        } else {
            printf("{\"kind\":\"register\",\"id\":%d,\"mode\":%d,\"rect\":[%d,%d,%d,%d]}",
                   e->id, (uint16_t)e->mode, e->rect.left, e->rect.top,
                   e->rect.right, e->rect.bottom);
        }
    }
    puts("]}");
}

int main(void)
{
    static const int16_t ids[] = {0x64, 0x65, 0x66, 0x67, 0x69, 0x70};
    PortableDecorationWindow window;
    PortableDatabase shared;
    unsigned combination, max_select, show;
    size_t i;
    if (portable_db_open(&database, "assets/HCEGANT") != PORTABLE_DB_OK ||
        portable_db_open(&shared, "assets/SHARED") != PORTABLE_DB_OK)
        return 2;
    for (i = 0; i < sizeof(ids) / sizeof(ids[0]); ++i) {
        const PortableDbIndexEntry *entry = 0;
        if (portable_db_lookup(&shared, ids[i], 2, &entry, 0) != PORTABLE_DB_NOT_FOUND || entry)
            return 3;
    }
    portable_db_close(&shared);

    memset(&window, 0, sizeof(window));
    window.flags = 0x059c;
    print_events("all-flags-maximized", &window, 1, 3);
    window.flags = 0x051c;
    print_events("all-flags-normal", &window, 1, 3);
    window.flags = 0x059c;
    print_events("all-flags-unregister", &window, 0, 3);

    for (combination = 0; combination < 32; ++combination) {
        int flags = 0;
        if (combination & 1) flags |= 0x0004;
        if (combination & 2) flags |= 0x0008;
        if (combination & 4) flags |= 0x0100;
        if (combination & 8) flags |= 0x0010;
        if (combination & 16) flags |= 0x0400;
        for (max_select = 0; max_select < 2; ++max_select) {
            for (show = 0; show < 2; ++show) {
                char label[40];
                window.flags = (int16_t)(flags | (max_select ? 0x0080 : 0));
                (void)snprintf(label, sizeof(label), "matrix-%02x-%u-%u",
                               combination, max_select, show);
                print_events(label, &window, (int)show, 3);
            }
        }
    }
    window.flags = 4;
    print_events("margin-neg128", &window, 1, -128);
    print_events("margin-neg1", &window, 1, -1);
    print_events("margin-zero", &window, 1, 0);
    print_events("margin-pos127", &window, 1, 127);
    portable_db_close(&database);
    return run_failed ? 4 : 0;
}
