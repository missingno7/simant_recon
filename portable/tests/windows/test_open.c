#include "../../ui_model/windows/open.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "assertion failed at %s:%d: %s\n", \
                __FILE__, __LINE__, #condition); \
        exit(1); \
    } \
} while (0)

static void assert_rect(PortableWindowRect r, int left, int top,
                        int right, int bottom)
{
    assert(r.left == left && r.top == top && r.right == right && r.bottom == bottom);
}

static void assert_event(const PortableWindowOpenResult *result, size_t index,
                         PortableWindowOpenEventKind kind, int window_id)
{
    assert(index < result->event_count);
    assert(result->events[index].kind == kind);
    assert(result->events[index].window_id == window_id);
}

static void test_hcegant_open_sequence(void)
{
    static const int16_t ids[] = {0x0000, 0x0100, 0x1200, 0x1300};
    static const PortableWindowRect expected[] = {
        {14, 22, 418, 347}, {118, 24, 634, 348},
        {86, 158, 300, 350}, {342, 158, 556, 350}
    };
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    PortableWindowOpenScene scene = {0};
    PortableWindowRect menu = {0, 0, 640, 30};
    int16_t args[4] = {0, 0, 0, 0};
    PortableWindowOpenResult result;
    size_t i;

    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_open_scene_init(&registry, NULL, 0, &scene) ==
           PORTABLE_WINDOW_OPEN_OK);
    for (i = 0; i < sizeof(ids) / sizeof(ids[0]); ++i) {
        PortableWindowOpenStatus status = portable_window_open_apply(
            &registry, &scene, ids[i], args, 640, 350, &menu, &result);
        if (status != PORTABLE_WINDOW_OPEN_OK)
            fprintf(stderr, "open %#x failed: %s / registry %d\n", ids[i],
                    portable_window_open_status_string(status), result.registry_status);
        assert(status == PORTABLE_WINDOW_OPEN_OK);
        assert_rect(result.frame_before_move, expected[i].left, expected[i].top,
                    expected[i].right, expected[i].bottom);
        assert_rect(result.frame_after, expected[i].left, expected[i].top,
                    expected[i].right, expected[i].bottom);
        assert(result.opened && !result.moved);
        assert(scene.front_window_id == ids[i]);
        assert(scene.order[0] == ids[i]);
        assert((scene.windows[(uint16_t)ids[i] >> 8].flags & PORTABLE_WINDOW_OPEN) != 0);
        assert((registry.slots[(uint16_t)ids[i] >> 8].window.flags &
                PORTABLE_WINDOW_OPEN) != 0);
        assert_event(&result, 0, PORTABLE_WINDOW_OPEN_RECALCULATE, ids[i]);
        assert_event(&result, result.event_count - 1,
                     PORTABLE_WINDOW_OPEN_FLUSH_EVENTS, ids[i]);
    }
    assert(scene.open_count == 4);
    assert(scene.order[0] == 0x1300 && scene.order[1] == 0x1200 &&
           scene.order[2] == 0x0100 && scene.order[3] == 0x0000);

    /* Reopening the front window does no recalc/draw, only source event flush. */
    assert(portable_window_open_apply(&registry, &scene, 0x1300, args,
                                      640, 350, &menu, &result) ==
           PORTABLE_WINDOW_OPEN_OK);
    assert(result.already_front && result.event_count == 1);
    assert_event(&result, 0, PORTABLE_WINDOW_OPEN_FLUSH_EVENTS, 0x1300);

    /* Raising an already-open window recalculates it and moves it to the front. */
    assert(portable_window_open_apply(&registry, &scene, 0x1200, args,
                                      640, 350, &menu, &result) ==
           PORTABLE_WINDOW_OPEN_OK);
    assert(scene.front_window_id == 0x1200 && scene.order[0] == 0x1200);
    assert(scene.open_count == 4);
    assert_event(&result, result.event_count - 1,
                 PORTABLE_WINDOW_OPEN_FLUSH_EVENTS, 0x1200);

    assert(portable_window_close_apply(&registry, &scene, 0x1200, &result) ==
           PORTABLE_WINDOW_OPEN_OK);
    assert(scene.front_window_id == 0x1300 && scene.open_count == 3);
    assert((scene.windows[0x12].flags & PORTABLE_WINDOW_OPEN) == 0);
    assert_event(&result, 0, PORTABLE_WINDOW_OPEN_FLAG_CLEARED, 0x1200);
    assert_event(&result, 1, PORTABLE_WINDOW_OPEN_FRONT_RESTORED, 0x1300);
    assert_event(&result, 2, PORTABLE_WINDOW_OPEN_ERASE_REQUESTED, 0x1200);

    /* win_Open does not lazily load a missing resource on behalf of the host. */
    assert(portable_window_open_apply(&registry, &scene, 0x0200, args,
                                      640, 350, &menu, &result) ==
           PORTABLE_WINDOW_OPEN_NOT_LOADED);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

static void test_movable_window_clamp_and_restore(void)
{
    PortableDatabase database = {0};
    PortableWindowRegistry registry = {0};
    PortableWindowOpenScene scene = {0};
    PortableWindowRect menu = {0, 0, 640, 30};
    PortableWindowOpenResult result;
    PortableWindowOpenStatus status;
    int16_t args[4] = {0, 0, 0, 0};
    PortableWindowRect saved;
    PortableWindowRegistrySlot *slot;

    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_open_scene_init(&registry, NULL, 0, &scene) ==
           PORTABLE_WINDOW_OPEN_OK);
    slot = &registry.slots[0];
    /* Controlled movable-flag contrast: HCEGANT profile-0 windows 0/1/18/19
     * do not carry this bit, so mutate only the runtime test fixture. */
    slot->window.flags |= PORTABLE_WINDOW_MOVABLE;
    scene.windows[0].flags |= PORTABLE_WINDOW_MOVABLE;
    status = portable_window_open_apply(&registry, &scene, 0x0000, args,
                                        640, 200, &menu, &result);
    assert(status == PORTABLE_WINDOW_OPEN_OK);
    assert(result.moved && result.move_dx == 0 && result.move_dy == -147);
    assert_rect(result.frame_before_move, 14, 22, 418, 347);
    assert_rect(result.frame_after, 14, -125, 418, 200);
    saved = scene.windows[0].saved_origin;
    assert(scene.windows[0].has_saved_origin);
    assert_event(&result, 0, PORTABLE_WINDOW_OPEN_RECALCULATE, 0);
    assert_event(&result, 1, PORTABLE_WINDOW_OPEN_SAVE_ORIGIN, 0);
    assert_event(&result, 2, PORTABLE_WINDOW_OPEN_MOVE_ORIGIN, 0);
    assert_event(&result, 3, PORTABLE_WINDOW_OPEN_RECALCULATE_AFTER_MOVE, 0);
    assert(portable_window_close_apply(&registry, &scene, 0, &result) ==
           PORTABLE_WINDOW_OPEN_OK);
    assert(!scene.windows[0].has_saved_origin);
    assert(slot->window.objects[0].offsets[0] == saved.left);
    assert(slot->window.objects[0].offsets[1] == saved.top);
    /* Close restores the saved source origin but deliberately does not recalc. */
    assert_rect(slot->window.rect, 14, -125, 418, 200);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

int main(void)
{
    test_hcegant_open_sequence();
    test_movable_window_clamp_and_restore();
    puts("window open model tests passed");
    return 0;
}
