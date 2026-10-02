#include "../../ui_model/windows/ribbon.h"
#include "../../game/resources/advice.h"
#include "../../game/resources/fonts.h"
#include "../../game/resources/database.h"

#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct FakeClock {
    int32_t values[8];
    size_t count;
    size_t next;
} FakeClock;

static int32_t read_clock(void *context)
{
    FakeClock *clock = (FakeClock *)context;
    assert(clock != NULL && clock->next < clock->count);
    return clock->values[clock->next++];
}

static int32_t signed_bits(uint32_t value)
{
    if (value <= (uint32_t)INT32_MAX)
        return (int32_t)value;
    return -1 - (int32_t)(UINT32_MAX - value);
}

static int32_t deadline_for(int32_t now, int32_t duration)
{
    int32_t scaled = signed_bits((uint32_t)duration * 3u) / 2;
    return signed_bits((uint32_t)now + (uint32_t)scaled);
}

static void open_resources(PortableDatabase *database,
                           PortableDatabase *shared_database,
                           PortableAdviceResources *advice,
                           PortableFontSet *font_set,
                           PortableWindowRegistry *registry)
{
    assert(portable_db_open(database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_db_open(shared_database, "assets/SHARED") == PORTABLE_DB_OK);
    portable_advice_init(advice);
    assert(portable_advice_load(advice, shared_database) == PORTABLE_ADVICE_OK);
    portable_fonts_init(font_set);
    assert(portable_fonts_load(font_set, "assets") == PORTABLE_RENDER_OK);
    assert(portable_window_registry_init(registry, database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
}

static void close_resources(PortableDatabase *database,
                            PortableDatabase *shared_database,
                            PortableAdviceResources *advice,
                            PortableFontSet *font_set,
                            PortableWindowRegistry *registry)
{
    portable_window_registry_destroy(registry);
    portable_fonts_destroy(font_set);
    portable_advice_free(advice);
    portable_db_close(shared_database);
    portable_db_close(database);
}

static const char *tutorial_message(PortableAdviceResources *advice,
                                    size_t index)
{
    size_t count = 0;
    const char *const *messages = portable_advice_pointers(
        advice, PORTABLE_ADVICE_TUTORIAL, &count);
    assert(messages != NULL && index < count && messages[index] != NULL);
    return messages[index];
}

static void test_edit_message_source_state(void)
{
    PortableDatabase database;
    PortableDatabase shared_database;
    PortableAdviceResources advice;
    PortableFontSet font_set;
    PortableWindowRegistry registry;
    PortableRibbonState state;
    PortableRibbonEditResult result;
    const char *message;
    FakeClock clock = {{100, 200, 300, 301, 400, 401, 0x70000000,
                        0x70000001}, 8, 0};
    int32_t duration;

    open_resources(&database, &shared_database, &advice, &font_set, &registry);
    message = tutorial_message(&advice, 0);
    portable_ribbon_init(&state);
    assert(state.edit_surface.dirty == 1 && state.map_yard.dirty == 0);

    assert(portable_ribbon_edit_message(&state, &advice, message, 0, 1, 1,
                                        read_clock, &clock, &result) ==
           PORTABLE_RIBBON_OK);
    assert(result.applied && result.tick_reads == 2);
    assert(result.edit_pointer_changed && result.map_pointer_changed);
    assert(state.edit_surface.deadline == 100);
    assert(state.map_yard.deadline == 200);
    assert(state.edit_surface.message.pointer == message);
    assert(state.edit_surface.message.source.table_id == PORTABLE_ADVICE_TUTORIAL);
    assert(state.edit_surface.message.source.index == 0);
    assert(state.edit_surface.dirty && state.map_yard.dirty);

    /* The source mode-0 gate leaves all state and the clock untouched. */
    portable_ribbon_clear_dirty(&state, PORTABLE_RIBBON_EDIT_SURFACE);
    portable_ribbon_clear_dirty(&state, PORTABLE_RIBBON_MAP);
    assert(portable_ribbon_edit_message(&state, &advice, NULL, 12, 0, 0,
                                        read_clock, &clock, &result) ==
           PORTABLE_RIBBON_OK);
    assert(!result.applied && result.tick_reads == 0 && clock.next == 2);
    assert(state.edit_surface.message.pointer == message &&
           state.edit_surface.deadline == 100 && !state.edit_surface.dirty);

    /* A permitted clear in mode 0 uses the infinite-deadline gate. */
    state.edit_surface.deadline = INT32_MAX;
    assert(portable_ribbon_edit_message(&state, &advice, NULL, -2, 0, 1,
                                        NULL, NULL, &result) ==
           PORTABLE_RIBBON_OK);
    assert(result.applied && result.tick_reads == 0 &&
           result.edit_pointer_changed && result.map_pointer_changed);
    assert(state.edit_surface.message.pointer == NULL &&
           state.map_yard.message.pointer == NULL);
    assert(state.edit_surface.deadline == INT32_MAX &&
           state.map_yard.deadline == INT32_MAX);

    /* A negative duration is an indefinite message and reads no clock. */
    assert(portable_ribbon_edit_message(&state, &advice, message, -1, 1, 1,
                                        NULL, NULL, &result) ==
           PORTABLE_RIBBON_OK);
    assert(result.applied && result.tick_reads == 0);
    assert(state.edit_surface.deadline == INT32_MAX &&
           state.map_yard.deadline == INT32_MAX);

    /* Source evaluates two independent TickCount calls in left-to-right order. */
    duration = INT32_C(0x40000000);
    assert(portable_ribbon_edit_message(&state, &advice, message, duration, 1, 1,
                                        read_clock, &clock, &result) ==
           PORTABLE_RIBBON_OK);
    assert(result.tick_reads == 2 && clock.next == 4);
    assert(state.edit_surface.deadline == deadline_for(300, duration));
    assert(state.map_yard.deadline == deadline_for(301, duration));
    assert(!result.edit_pointer_changed && !result.map_pointer_changed);

    /* Large positive duration exercises signed 32-bit wrap at both stages. */
    duration = INT32_MAX;
    assert(portable_ribbon_edit_message(&state, &advice, message, duration, 1, 1,
                                        read_clock, &clock, &result) ==
           PORTABLE_RIBBON_OK);
    assert(result.tick_reads == 2 && clock.next == 6);
    assert(state.edit_surface.deadline == deadline_for(400, duration));
    assert(state.map_yard.deadline == deadline_for(401, duration));

    /* Foreign pointers fail closed before changing state or reading ticks. */
    {
        int32_t edit_deadline = state.edit_surface.deadline;
        int32_t map_deadline = state.map_yard.deadline;
        assert(portable_ribbon_edit_message(&state, &advice, "not-owned", 5, 1, 1,
                                            read_clock, &clock, &result) ==
               PORTABLE_RIBBON_UNKNOWN_MESSAGE);
        assert(clock.next == 6 && state.edit_surface.deadline == edit_deadline &&
               state.map_yard.deadline == map_deadline);
    }
    close_resources(&database, &shared_database, &advice, &font_set, &registry);
}

static void test_render_and_expiry(void)
{
    PortableDatabase database;
    PortableDatabase shared_database;
    PortableAdviceResources advice;
    PortableFontSet font_set;
    PortableWindowRegistry registry;
    PortableRibbonState state;
    PortableRibbonEditResult edit;
    PortableRibbonRenderResult rendered;
    PortableFramebuffer framebuffer;
    PortableWindowRenderer renderer;
    PortableWindowRect expected;
    uint8_t *pixels = NULL;
    PortableDbRecord color_record;
    FakeClock clock = {{100, 100, 100, 101, 100, 100, 101}, 7, 0};
    const char *message;
    size_t pixel_count;
    size_t i;
    size_t foreground_pixels = 0;

    open_resources(&database, &shared_database, &advice, &font_set, &registry);
    message = tutorial_message(&advice, 0);
    memset(&color_record, 0, sizeof(color_record));
    assert(portable_db_load(&database, 0x81, 0, &color_record) == PORTABLE_DB_OK);
    memset(&renderer, 0, sizeof(renderer));
    renderer.screen_width = 640;
    renderer.database = &database;
    renderer.colors = color_record.data;
    renderer.colors_size = color_record.size;
    renderer.fonts[0] = portable_fonts_get(&font_set, 2);
    assert(renderer.fonts[0] != NULL);
    pixel_count = 640u * 480u;
    pixels = (uint8_t *)calloc(pixel_count, 1);
    assert(pixels != NULL);
    assert(portable_framebuffer_init(&framebuffer, 640, 480, 640, pixels) ==
           PORTABLE_RENDER_OK);
    renderer.framebuffer = &framebuffer;
    portable_ribbon_init(&state);
    assert(portable_ribbon_edit_message(&state, &advice, message, 0, 1, 1,
                                        read_clock, &clock, &edit) ==
           PORTABLE_RIBBON_OK);

    /* Deadline equality stays live; source expires only when TickCount > end. */
    clock.next = 2;
    assert(portable_ribbon_render_current(&state, &advice, PORTABLE_RIBBON_MAP,
                 &registry, &renderer, 1, read_clock, &clock, &rendered) ==
           PORTABLE_RIBBON_OK);
    assert(rendered.message_live && rendered.drawn && !rendered.expired);
    assert(rendered.font_id == PORTABLE_RIBBON_FONT_OTHER &&
           rendered.color_index == PORTABLE_RIBBON_COLOR_INDEX);
    assert(rendered.has_clip_exclusion && state.map_yard.message.pointer == message);
    assert(portable_window_registry_get_object_rect(&registry, 0x0102, &expected) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(rendered.target_rect.left == expected.left &&
           rendered.target_rect.right == expected.right &&
           rendered.text_rect.top == expected.top + 4);
    assert(rendered.text_rect.left ==
           ((int32_t)expected.right -
            portable_font_string_width(renderer.fonts[0],
                (const uint8_t *)message, strlen(message)) + expected.left) / 2);
    assert(rendered.text_rect.right - rendered.text_rect.left ==
           portable_font_string_width(renderer.fonts[0],
                (const uint8_t *)message, strlen(message)));
    assert(state.map_yard.dirty == 1);
    for (i = 0; i < pixel_count; ++i) {
        assert(pixels[i] == 0 || pixels[i] == renderer.colors[18]);
        if (pixels[i] == renderer.colors[18] && renderer.colors[18] != 0)
            ++foreground_pixels;
    }
    assert(foreground_pixels != 0);

    /* Expiry happens even when the yard presentation is currently hidden. */
    clock.next = 3;
    assert(portable_ribbon_render_current(&state, &advice, PORTABLE_RIBBON_YARD,
                 &registry, &renderer, 0, read_clock, &clock, &rendered) ==
           PORTABLE_RIBBON_OK);
    assert(rendered.expired && !rendered.drawn && !rendered.message_live);
    assert(state.map_yard.message.pointer == NULL && state.map_yard.dirty);

    /* Expiry is strict: at deadline the message survives; above it it clears. */
    assert(portable_ribbon_edit_message(&state, &advice, message, 0, 1, 1,
                                        read_clock, &clock, &edit) ==
           PORTABLE_RIBBON_OK);
    clock.next = 6;
    assert(portable_ribbon_render_current(&state, &advice,
                 PORTABLE_RIBBON_EDIT_SURFACE, &registry, &renderer, 1,
                 read_clock, &clock, &rendered) == PORTABLE_RIBBON_OK);
    assert(rendered.expired); /* 101 > the first TickCount (100). */

    portable_db_record_free(&color_record);
    free(pixels);
    close_resources(&database, &shared_database, &advice, &font_set, &registry);
}

int main(void)
{
    test_edit_message_source_state();
    test_render_and_expiry();
    puts("ribbon model tests passed");
    return 0;
}
