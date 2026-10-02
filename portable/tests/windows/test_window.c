#include "../../ui_model/windows/window.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_rect_edges_and_dialog_events(void)
{
    PortableWindowRect r = {10, 20, 30, 40};
    int result = -1;
    int scenario = -1;
    assert(portable_window_rect_contains(&r, (PortableWindowPoint){10, 20}));
    assert(!portable_window_rect_contains(&r, (PortableWindowPoint){30, 20}));
    assert(!portable_window_rect_contains(&r, (PortableWindowPoint){10, 40}));
    assert(portable_window_dialog_result(0x2100, 0, 'd', &result) && result == 0);
    assert(portable_window_dialog_result(0x2100, 0, '\r', &result) && result == 0);
    assert(portable_window_dialog_result(0x2100, 0, 'S', &result) && result == 1);
    assert(portable_window_dialog_result(0x2100, 0, 0x1b, &result) && result == 2);
    assert(portable_window_dialog_result(0x2100, 0x2104, 0, &result) && result == 1);
    assert(!portable_window_dialog_result(0x2200, 0x2104, 0, &result));
    assert(!portable_window_dialog_result(0x2200, 0, 'd', &result));
    assert(!portable_window_dialog_result(0x2100, 0, 'x', &result));
    assert(portable_newgame_scenario_action(0x202, &scenario) == PORTABLE_SCENARIO_START && scenario == 1);
    assert(portable_newgame_scenario_action(0x203, &scenario) == PORTABLE_SCENARIO_START && scenario == 2);
    assert(portable_newgame_scenario_action(0x204, &scenario) == PORTABLE_SCENARIO_START && scenario == 3);
    assert(portable_newgame_scenario_action(0x206, &scenario) == PORTABLE_SCENARIO_START && scenario == 0);
    assert(portable_newgame_scenario_action(0x205, &scenario) == PORTABLE_SCENARIO_CANCEL);
    assert(portable_newgame_scenario_action(0x207, &scenario) == PORTABLE_SCENARIO_CONFIRM_TRANSFER);
    assert(portable_newgame_scenario_action(0x208, &scenario) == PORTABLE_SCENARIO_UNRECOGNIZED);
}

static void test_actual_hcegant_2100(void)
{
    PortableDatabase db;
    PortableDbRecord record;
    PortableWindowResource window;
    PortableWindowStatus status;
    PortableWindowPoint point;
    PortableWindowRenderStep trace[12];
    int16_t no_args[4] = {0, 0, 0, 0};
    uint8_t immutable_before[344];

    assert(portable_db_open(&db, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_db_load(&db, 0x21, 0, &record) == PORTABLE_DB_OK);
    assert(record.size == sizeof(immutable_before));
    memcpy(immutable_before, record.data, record.size);
    status = portable_window_decode(&record, &window);
    assert(status == PORTABLE_WINDOW_OK);
    assert(window.resource_id == 0x21 && window.count == 6);
    assert(window.rect.left == 133 && window.rect.top == 70);
    assert(window.rect.right == 470 && window.rect.bottom == 236);
    assert(window.flags == 0x0840);
    assert(window.objects[0].type == 0 && window.objects[0].resource_size == 0x29);
    assert(window.objects[1].type == 1 && window.objects[1].resource_size == 0x28);
    assert(window.objects[3].type == 5 && window.objects[3].resource_size == 55);
    assert(window.objects[3].rect.left == 140 && window.objects[3].rect.top == 202);
    assert(window.objects[3].rect.right == 231 && window.objects[3].rect.bottom == 230);
    assert(window.objects[3].group == 0 && (window.objects[3].flags & 7) == 7);
    assert(window.objects[3].indices[0] == 0x2100);
    assert(window.objects[3].modes[0] == 1 && window.objects[3].modes[1] == 2);
    assert(window.objects[3].offsets[0] == 7 && window.objects[3].offsets[1] == 132);
    assert(portable_window_recalculate(&window, no_args) == PORTABLE_WINDOW_OK);
    assert(window.rect.left == 133 && window.rect.top == 70);
    assert(window.rect.right == 470 && window.rect.bottom == 236);
    assert(window.objects[3].rect.left == 140 && window.objects[3].rect.top == 202);
    assert(window.objects[3].rect.right == 231 && window.objects[3].rect.bottom == 230);
    assert(portable_window_render_trace(&window, 1, 1, trace, 12) == 9);
    assert(trace[0].kind == PORTABLE_WINDOW_HOOK_BEFORE);
    assert(trace[1].kind == PORTABLE_WINDOW_DRAW_OBJECT && trace[1].object_index == 0);
    assert(trace[6].kind == PORTABLE_WINDOW_DRAW_OBJECT && trace[6].object_index == 5);
    assert(trace[7].kind == PORTABLE_WINDOW_DRAW_FRAME);
    assert(trace[8].kind == PORTABLE_WINDOW_HOOK_AFTER);
    assert(portable_window_render_trace(&window, 0, 1, trace, 12) == 1);
    assert(trace[0].kind == PORTABLE_WINDOW_HOOK_AFTER);

    point = (PortableWindowPoint){200, 215};
    assert(portable_window_hit_test(&window, point) == 3);
    point = (PortableWindowPoint){294, 215};
    assert(portable_window_hit_test(&window, point) == 4);
    point = (PortableWindowPoint){470, 235};
    assert(portable_window_hit_test(&window, point) == -1);

    portable_window_set_group_selectable(&window, 0, 0);
    assert(portable_window_hit_test(&window, (PortableWindowPoint){200, 215}) == -1);
    portable_window_set_group_selectable(&window, 0, 1);
    assert(portable_window_hit_test(&window, (PortableWindowPoint){200, 215}) == 3);
    portable_window_set_group_selected(&window, 0, 0);
    assert((window.objects[3].flags & PORTABLE_WINDOW_OBJECT_SELECTED) == 0);
    assert(memcmp(immutable_before, record.data, record.size) == 0);

    portable_window_release(&window);
    portable_db_record_free(&record);

    assert(portable_db_load(&db, 0x21, 10, &record) != PORTABLE_DB_OK);
    portable_db_close(&db);
}

static void test_actual_scenario_window_0200(void)
{
    PortableDatabase db;
    PortableDbRecord record;
    PortableDbRecord profile;
    PortableWindowResource window;
    PortableWindowRenderStep trace[12];
    int16_t no_args[4] = {0, 0, 0, 0};
    int scenario = -1;
    int i;

    assert(portable_db_open(&db, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_db_load(&db, 2, 0, &record) == PORTABLE_DB_OK);
    assert(portable_db_load(&db, 0, 9, &profile) == PORTABLE_DB_OK);
    assert(record.size == 399);
    assert(portable_window_decode(&record, &window) == PORTABLE_WINDOW_OK);
    assert(window.resource_id == 2 && window.count == 8);
    assert(window.flags == 0x0840);
    assert(window.objects[0].type == 15);
    assert(window.objects[1].type == 6);
    for (i = 2; i < 8; ++i) {
        const PortableWindowObject *object = &window.objects[i];
        PortableWindowPoint center;
        int code = 0x0200 + i;
        PortableScenarioAction action;
        center.x = (int16_t)((object->rect.left + object->rect.right) / 2);
        center.y = (int16_t)((object->rect.top + object->rect.bottom) / 2);
        assert(object->type == 1);
        assert((object->flags & PORTABLE_WINDOW_OBJECT_SELECTABLE) != 0);
        assert(portable_window_hit_test(&window, center) == i);
        action = portable_newgame_scenario_action(code, &scenario);
        if (code == 0x0205)
            assert(action == PORTABLE_SCENARIO_CANCEL);
        else if (code == 0x0207)
            assert(action == PORTABLE_SCENARIO_CONFIRM_TRANSFER);
        else {
            assert(action == PORTABLE_SCENARIO_START);
            assert(scenario == (code == 0x0202 ? 1 : code == 0x0203 ? 2 :
                                code == 0x0204 ? 3 : 0));
        }
    }
    assert(portable_window_recalculate(&window, no_args) == PORTABLE_WINDOW_OK);
    assert(window.rect.left == 163 && window.rect.top == 107);
    assert(window.rect.right == 485 && window.rect.bottom == 365);
    assert(window.objects[2].rect.left == 339 && window.objects[2].rect.top == 133);
    assert(window.objects[2].rect.right == 402 && window.objects[2].rect.bottom == 196);
    assert(portable_window_hit_test(&window, (PortableWindowPoint){370, 165}) == 2);
    assert(portable_window_render_trace(&window, 1, 0, trace, 12) == 9);
    assert(trace[0].kind == PORTABLE_WINDOW_DRAW_OBJECT && trace[0].object_index == 0);
    assert(trace[7].kind == PORTABLE_WINDOW_DRAW_OBJECT && trace[7].object_index == 7);
    assert(trace[8].kind == PORTABLE_WINDOW_DRAW_FRAME);

    /* Startup's kind-9 profile row 2 replaces all four object-0 offset words. */
    assert(profile.size == 0x140);
    assert(portable_window_apply_origin_profile(&window, profile.data, profile.size) ==
           PORTABLE_WINDOW_OK);
    assert(portable_window_recalculate(&window, no_args) == PORTABLE_WINDOW_OK);
    assert(window.rect.left == 136 && window.rect.top == 41);
    assert(window.rect.right == 458 && window.rect.bottom == 299);
    assert(window.objects[2].rect.left == 312 && window.objects[2].rect.top == 67);
    assert(window.objects[2].rect.right == 375 && window.objects[2].rect.bottom == 130);
    assert(portable_window_hit_test(&window, (PortableWindowPoint){343, 98}) == 2);

    portable_window_release(&window);
    portable_db_record_free(&record);
    portable_db_record_free(&profile);
    portable_db_close(&db);
}

static void test_window_lifecycle_state(void)
{
    PortableWindowState state;
    memset(&state, 0, sizeof(state));
    state.origin = (PortableWindowRect){1, 2, 3, 4};
    state.flags = PORTABLE_WINDOW_MOVABLE;
    portable_window_lock(&state);
    portable_window_lock(&state);
    assert(state.lock_depth == 2);
    assert(portable_window_unlock(&state) && state.lock_depth == 1);
    assert(portable_window_unlock(&state) && state.lock_depth == 0);
    assert(!portable_window_unlock(&state));
    assert(portable_window_open(&state));
    assert(!portable_window_open(&state));
    portable_window_set_origin(&state, (PortableWindowRect){5, 6, 7, 8});
    assert(state.origin.left == 5 && state.origin.top == 6);
    assert(portable_window_close(&state));
    assert(state.origin.left == 1 && state.origin.top == 2);
    assert(!portable_window_close(&state));
}

int main(void)
{
    test_rect_edges_and_dialog_events();
    test_actual_hcegant_2100();
    test_actual_scenario_window_0200();
    test_window_lifecycle_state();
    puts("window model tests passed");
    return 0;
}
