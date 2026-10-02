#include "../../ui_model/dialogs/end_game_view.h"
#include "../../game/resources/database.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, \
                #condition); \
        exit(1); \
    } \
} while (0)

typedef struct TestContext {
    PortableEndGameView *view;
    PortableWindowRegistry *registry;
    PortableWindowOpenScene *scene;
    uint8_t open_called;
    PortableWindowRect opened_rect;
} TestContext;

static int open_window(void *context, int16_t window_id)
{
    TestContext *test = (TestContext *)context;
    int16_t args[4] = {0, 0, 0, 0};
    PortableWindowOpenResult result;
    PortableWindowOpenStatus status;
    status = portable_window_open_apply(test->registry, test->scene,
        window_id, args, 640, 350, &(PortableWindowRect){0, 0, 640, 14},
        &result);
    if (status != PORTABLE_WINDOW_OPEN_OK) {
        fprintf(stderr, "window open failed: %s\n",
                portable_window_open_status_string(status));
        return 0;
    }
    test->open_called = 1;
    test->opened_rect = result.frame_after;
    return portable_end_game_view_note_open(test->view, window_id);
}

static int set_font(void *context, int16_t font)
{
    TestContext *test = (TestContext *)context;
    return portable_end_game_view_set_font(test->view, font);
}

static int set_resource_text(void *context, int16_t object,
                             int16_t resource, int16_t index)
{
    TestContext *test = (TestContext *)context;
    return portable_end_game_view_set_resource_text(test->view, object,
                                                    resource, index);
}

static int set_score_text(void *context, int16_t object, int32_t score)
{
    TestContext *test = (TestContext *)context;
    return portable_end_game_view_set_score_text(test->view, object, score);
}

static int wait_init(void *context, int16_t seconds)
{
    (void)context;
    return seconds == 100;
}

static void assert_loaded_string(PortableDatabase *shared, int16_t resource,
                                 int16_t index,
                                 const PortableEndGameString *actual)
{
    PortableDbRecord table = {0};
    size_t cursor = 2, item;
    assert(portable_db_load(shared, resource, 4, &table) == PORTABLE_DB_OK);
    assert(table.data[1] > (uint8_t)index);
    for (item = 0; item <= (size_t)index; ++item) {
        size_t length = table.data[cursor++];
        if (item == (size_t)index) {
            assert(actual->length == length);
            assert(memcmp(actual->bytes, table.data + cursor, length) == 0);
        }
        cursor += length;
    }
    portable_db_record_free(&table);
}

static uint64_t pixel_hash(const uint8_t *pixels, size_t length)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t i;
    for (i = 0; i < length; ++i) {
        hash ^= pixels[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

int main(int argc, char **argv)
{
    PortableDatabase shared = {0}, windows = {0};
    PortableDbRecord colors = {0};
    PortableWindowRegistry registry;
    PortableWindowRegistry registry_320;
    PortableWindowOpenScene scene;
    PortableWindowOpenScene scene_320;
    PortableFontSet fonts;
    PortableWindowRenderer renderer = {0};
    PortableFramebuffer framebuffer;
    PortableEndGameView view;
    PortableEndGameView view_320;
    SimGameOverInput input = {0};
    SimGameOverResult summary;
    SimGameOverResult summary_320;
    SimEndGameFlow flow;
    SimEndGameFlowHost host = {0};
    TestContext test;
    uint8_t pixels[640 * 350];
    uint8_t *baseline_pixels;
    uint8_t *before_record;
    size_t before_record_size;
    PortableWindowRect rects_before[5];
    size_t nonzero = 0, i;
    PortableEndGameViewStatus view_status;
    assert(argc == 2);
    assert(portable_db_open(&shared, "assets/SHARED") == PORTABLE_DB_OK);
    assert(portable_db_open(&windows, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_db_load(&windows, 0x81, 0, &colors) == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &windows, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_load(&registry, 4) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(registry.slots[4].window.resource_id == 4);
    before_record_size = registry.slots[4].window.record_size;
    before_record = (uint8_t *)malloc(before_record_size);
    assert(before_record != NULL);
    memcpy(before_record, registry.slots[4].window.record_bytes,
           before_record_size);
    assert(portable_window_open_scene_init(&registry, NULL, 0, &scene) ==
           PORTABLE_WINDOW_OPEN_OK);
    portable_fonts_init(&fonts);
    assert(portable_fonts_load(&fonts, argv[1]) == PORTABLE_RENDER_OK);
    portable_end_game_view_init(&view);
    input.health = 100;
    input.screen_width = 640;
    input.scenario = 0;
    assert(sim_game_over_calculate(&input, &summary) == SIM_GAME_OVER_OK);
    assert(portable_end_game_view_prepare(&view, &shared, &summary, 640) ==
           PORTABLE_END_GAME_VIEW_OK);
    test.view = &view;
    test.registry = &registry;
    test.scene = &scene;
    test.open_called = 0;
    host.context = &test;
    host.open_window = open_window;
    host.set_font = set_font;
    host.set_resource_text = set_resource_text;
    host.set_score_text = set_score_text;
    host.dialog_wait_init = wait_init;
    assert(sim_end_game_flow_begin(&flow, &input, &(SimRng){0}, &host) ==
           SIM_END_GAME_FLOW_OK);
    assert(test.open_called && scene.front_window_id == 0x0400);
    assert(view.text_font_id == 4 && view.active_font_id == 0);
    assert(strcmp(view.score_text, "15157") == 0);
    assert(view.scenario_record.id == 1001 && view.scenario_record.kind == 4);
    assert(view.level_record.id == 1900 && view.level_record.kind == 4);
    assert_loaded_string(&shared, 1001, summary.scenario_index, &view.scenario_text);
    assert_loaded_string(&shared, 1900, summary.level_index, &view.level_text);
    assert(test.opened_rect.left == 132 && test.opened_rect.top == 59 &&
           test.opened_rect.right == 452 && test.opened_rect.bottom == 259);
    for (i = 0; i < 5; ++i)
        rects_before[i] = registry.slots[4].window.objects[i].rect;
    /* The render path must use the already-open resource coordinates; it does
     * not recalculate or move the object-zero origin. */
    assert(memcmp(before_record, registry.slots[4].window.record_bytes,
                  before_record_size) == 0);
    memset(pixels, 0, sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer, 640, 350, 640, pixels) ==
           PORTABLE_RENDER_OK);
    renderer.framebuffer = &framebuffer;
    renderer.database = &windows;
    renderer.colors = colors.data;
    renderer.colors_size = colors.size;
    renderer.screen_width = 640;
    view_status = portable_end_game_view_render(&view, &registry, &scene, &fonts,
                                                &renderer);
    if (view_status != PORTABLE_END_GAME_VIEW_OK) {
        size_t object_index;
        fprintf(stderr, "EndGame render: %s, bounds=[%d,%d,%d,%d], count=%u\n",
                portable_end_game_view_status_string(view_status),
                registry.slots[4].window.rect.left,
                registry.slots[4].window.rect.top,
                registry.slots[4].window.rect.right,
                registry.slots[4].window.rect.bottom,
                registry.slots[4].window.count);
        for (object_index = 0; object_index < registry.slots[4].window.count;
             ++object_index) {
            const PortableWindowObject *object =
                &registry.slots[4].window.objects[object_index];
            fprintf(stderr, "object %zu type=%u font=%u bytes=%u rect=%d,%d,%d,%d\n",
                    object_index, object->type, object->resource_bytes[0x28],
                    object->resource_size, object->rect.left, object->rect.top,
                    object->rect.right, object->rect.bottom);
        }
    }
    assert(view_status == PORTABLE_END_GAME_VIEW_OK);
    for (i = 0; i < sizeof(pixels); ++i)
        if (pixels[i] != 0) ++nonzero;
    assert(nonzero > 1000);
    assert(pixel_hash(pixels, sizeof(pixels)) == UINT64_C(0x49dc1b626aba55be));
    assert(portable_end_game_view_render(&view, &registry, &scene, &fonts,
                                         &renderer) == PORTABLE_END_GAME_VIEW_OK);
    for (i = 0; i < 5; ++i)
        assert(memcmp(&rects_before[i], &registry.slots[4].window.objects[i].rect,
                      sizeof(rects_before[i])) == 0);
    assert(memcmp(before_record, registry.slots[4].window.record_bytes,
                  before_record_size) == 0);

    /* Compare a no-score baseline to the long score rendered into a narrow
     * live object. The caller clip is narrower than the window but wider than
     * the object, so any missing source object clip leaks visibly outside it. */
    {
        PortableWindowObject *score_object =
            &registry.slots[4].window.objects[3];
        PortableWindowRect original_rect = score_object->rect;
        PortableRect original_clip = framebuffer.clip;
        PortableRect caller_clip = {245, 162, 270, 178};
        PortableRect object_clip;
        size_t changed_inside = 0;
        size_t original_score_length = view.score_text_length;
        baseline_pixels = (uint8_t *)malloc(sizeof(pixels));
        assert(baseline_pixels != NULL);
        score_object->rect = (PortableWindowRect){250, 164, 265, 177};
        memset(pixels, 0, sizeof(pixels));
        view.score_text_length = 0;
        portable_framebuffer_set_clip(&framebuffer, caller_clip);
        assert(portable_end_game_view_render(&view, &registry, &scene, &fonts,
                                             &renderer) ==
               PORTABLE_END_GAME_VIEW_OK);
        memcpy(baseline_pixels, pixels, sizeof(pixels));
        view.score_text_length = original_score_length;
        assert(portable_end_game_view_render(&view, &registry, &scene, &fonts,
                                             &renderer) ==
               PORTABLE_END_GAME_VIEW_OK);
        assert(memcmp(&framebuffer.clip, &caller_clip, sizeof(caller_clip)) == 0);
        object_clip = (PortableRect){250, 164, 265, 177};
        for (i = 0; i < sizeof(pixels); ++i) {
            int32_t x = (int32_t)(i % 640u);
            int32_t y = (int32_t)(i / 640u);
            int inside = x >= object_clip.left && x < object_clip.right &&
                         y >= object_clip.top && y < object_clip.bottom;
            if (inside) {
                if (pixels[i] != baseline_pixels[i]) ++changed_inside;
            } else {
                assert(pixels[i] == baseline_pixels[i]);
            }
        }
        assert(changed_inside > 0);
        score_object->rect = original_rect;
        portable_framebuffer_set_clip(&framebuffer, original_clip);
        free(baseline_pixels);
    }

    input.screen_width = 320;
    assert(sim_game_over_calculate(&input, &summary_320) == SIM_GAME_OVER_OK);
    assert(portable_window_registry_init(&registry_320, &windows, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_load(&registry_320, 4) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_open_scene_init(&registry_320, NULL, 0, &scene_320) ==
           PORTABLE_WINDOW_OPEN_OK);
    {
        int16_t args[4] = {0, 0, 0, 0};
        PortableWindowOpenResult open_result;
        assert(portable_window_open_apply(&registry_320, &scene_320, 0x0400,
            args, 320, 200, &(PortableWindowRect){0, 0, 320, 14},
            &open_result) == PORTABLE_WINDOW_OPEN_OK);
    }
    portable_end_game_view_init(&view_320);
    assert(portable_end_game_view_prepare(&view_320, &shared, &summary_320, 320) ==
           PORTABLE_END_GAME_VIEW_OK);
    assert(summary_320.font_id == 2);
    assert(portable_end_game_view_set_font(&view_320, 2));
    assert(portable_end_game_view_set_resource_text(&view_320,
        summary_320.scenario_object_id, summary_320.scenario_resource_id,
        summary_320.scenario_index));
    assert(portable_end_game_view_set_score_text(&view_320,
        summary_320.score_object_id, summary_320.score));
    assert(portable_end_game_view_set_resource_text(&view_320,
        summary_320.level_object_id, summary_320.level_resource_id,
        summary_320.level_index));
    assert(portable_end_game_view_set_font(&view_320, 0));
    assert(view_320.text_font_id == 2 && view_320.active_font_id == 0);
    memset(pixels, 0, sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer, 320, 200, 320, pixels) ==
           PORTABLE_RENDER_OK);
    renderer.framebuffer = &framebuffer;
    renderer.screen_width = 320;
    assert(portable_end_game_view_render(&view_320, &registry_320, &scene_320,
                                         &fonts, &renderer) ==
           PORTABLE_END_GAME_VIEW_INVALID_STATE);
    /* A prepared view is not a substitute for the runtime window-open event. */
    assert(portable_end_game_view_note_open(&view_320, 0x0400));
    assert(portable_end_game_view_render(&view_320, &registry_320, &scene_320,
                                         &fonts, &renderer) ==
           PORTABLE_END_GAME_VIEW_OK);
    assert(pixel_hash(pixels, 320u * 200u) == UINT64_C(0xac5f4a3063829490));

    portable_end_game_view_release(&view_320);
    portable_end_game_view_release(&view);
    portable_fonts_destroy(&fonts);
    portable_window_registry_destroy(&registry_320);
    portable_window_registry_destroy(&registry);
    portable_db_record_free(&colors);
    portable_db_close(&windows);
    portable_db_close(&shared);
    free(before_record);
    puts("EndGame view: retained source strings, font state, and resource rendering passed");
    return 0;
}
