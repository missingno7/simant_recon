#include "../../../ui_model/windows/titles.h"
#include "../../../ui_model/windows/render.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void check_table_matches_resource(PortableDatabase *database,
                                         int16_t object_id,
                                         const PortableTitleStringTable *table)
{
    PortableDbRecord record = {0};
    size_t cursor = 2, i;
    assert(portable_db_load(database, object_id, PORTABLE_TITLE_STRING_KIND,
                            &record) == PORTABLE_DB_OK);
    assert(table->count == record.data[1]);
    for (i = 0; i < table->count; ++i) {
        size_t length = record.data[cursor++];
        assert(strlen(table->items[i]) == length);
        assert(memcmp(table->items[i], record.data + cursor, length) == 0);
        cursor += length;
    }
    assert(cursor == record.size);
    portable_db_record_free(&record);
}

static void test_actual_tables_and_all_title_indices(void)
{
    PortableDatabase database = {0};
    PortableWindowTitlesStringSet strings = {0};
    PortableWindowTitleProjection projection = {0};
    PortableWindowTitleScene scene = {0};
    unsigned scenario, map_mode, yard_mode;

    assert(portable_db_open(&database, "assets/SHARED") == PORTABLE_DB_OK);
    {
        PortableWindowTitlesStatus status =
            portable_window_titles_load(&strings, &database);
        if (status != PORTABLE_WINDOW_TITLES_OK)
            fprintf(stderr, "title load failed: %s (%d)\n",
                    portable_window_titles_status_string(status), (int)status);
        assert(status == PORTABLE_WINDOW_TITLES_OK);
    }
    assert(strings.map_modes.count == 13);
    assert(strings.scenarios.count == 4);
    assert(strings.edit_suffixes.count == 19);
    assert(strcmp(strings.map_modes.items[0], "BackYard View") == 0);
    assert(strcmp(strings.map_modes.items[1], "Surface View") == 0);
    assert(strcmp(strings.map_modes.items[2], "Black Nest View") == 0);
    assert(strcmp(strings.map_modes.items[9], "Yard View") == 0);
    assert(strcmp(strings.scenarios.items[0], "Tutorial Game") == 0);
    assert(strcmp(strings.scenarios.items[1], "Quick Game") == 0);
    assert(strcmp(strings.scenarios.items[2], "Full Game") == 0);
    assert(strcmp(strings.scenarios.items[3], "Experimental") == 0);
    assert(strcmp(strings.edit_suffixes.items[15], " - ") == 0);
    check_table_matches_resource(&database, PORTABLE_TITLE_MAP_TABLE_ID,
                                 &strings.map_modes);
    check_table_matches_resource(&database, PORTABLE_TITLE_SCENARIO_TABLE_ID,
                                 &strings.scenarios);
    check_table_matches_resource(&database, PORTABLE_TITLE_EDIT_SUFFIX_TABLE_ID,
                                 &strings.edit_suffixes);

    scene.edit_window_open = 1;
    scene.map_window_open = 1;
    scene.yard_window_open = 1;
    for (scenario = 0; scenario < 4; ++scenario) {
        for (map_mode = 0; map_mode < 9; ++map_mode) {
            for (yard_mode = 0; yard_mode < 4; ++yard_mode) {
                char expected_edit[PORTABLE_TITLE_MAX_BYTES];
                scene.scenario = (int16_t)scenario;
                scene.map_mode = (int16_t)map_mode;
                scene.yard_mode = (int16_t)yard_mode;
                assert(portable_window_titles_update(&strings, &scene,
                                                     &projection) ==
                       PORTABLE_WINDOW_TITLES_OK);
                assert(projection.edit.object_id == 0x0001);
                assert(projection.edit.redraw_window_id == 0);
                assert(projection.edit.redraw);
                assert(projection.map.object_id == 0x0101);
                assert(projection.map.redraw_window_id == 0x0100);
                assert(projection.map.redraw);
                assert(projection.yard.object_id == 0x1901);
                assert(projection.yard.redraw_window_id == 0x1900);
                assert(!projection.yard.redraw); /* Map window wins source priority. */
                assert(snprintf(expected_edit, sizeof expected_edit, "SimAnt%s%s",
                    strings.edit_suffixes.items[15],
                    strings.scenarios.items[scenario]) > 0);
                assert(strcmp((const char *)projection.edit.text,
                              expected_edit) == 0);
                assert(strcmp((const char *)projection.map.text,
                              strings.map_modes.items[map_mode]) == 0);
                assert(strcmp((const char *)projection.yard.text,
                              strings.map_modes.items[yard_mode + 9]) == 0);
            }
        }
    }
    portable_window_titles_free(&strings);
    portable_db_close(&database);
}

static void test_redraw_routing_and_renderer_resolver(void)
{
    PortableDatabase database = {0};
    PortableWindowTitlesStringSet strings = {0};
    PortableWindowTitleProjection projection = {0};
    PortableWindowTitleScene scene = {1, 2, 3, 1, 0, 1};
    PortableWindowRenderer renderer = {0};
    const uint8_t format[] = "title format";
    const uint8_t *text = NULL;
    size_t text_size = 0;

    assert(portable_db_open(&database, "assets/SHARED") == PORTABLE_DB_OK);
    assert(portable_window_titles_load(&strings, &database) ==
           PORTABLE_WINDOW_TITLES_OK);
    assert(portable_window_titles_update(&strings, &scene, &projection) ==
           PORTABLE_WINDOW_TITLES_OK);
    renderer.resolve_text = portable_window_titles_resolve_text;
    renderer.text_context = &projection;
    assert(projection.edit.redraw);
    assert(!projection.map.redraw);
    assert(projection.yard.redraw);
    assert(renderer.resolve_text(renderer.text_context, 0, 1,
        format, sizeof format, &text, &text_size));
    assert(text == projection.edit.text);
    assert(text_size == projection.edit.text_size);
    assert(renderer.resolve_text(renderer.text_context, 0x0100, 1,
        format, sizeof format, &text, &text_size));
    assert(text == projection.map.text);
    assert(renderer.resolve_text(renderer.text_context, 0x1900, 1,
        format, sizeof format, &text, &text_size));
    assert(text == projection.yard.text);
    assert(!renderer.resolve_text(renderer.text_context, 0x0100, 2,
        format, sizeof format, &text, &text_size));

    scene.map_window_open = 0;
    scene.yard_window_open = 0;
    assert(portable_window_titles_update(&strings, &scene, &projection) ==
           PORTABLE_WINDOW_TITLES_OK);
    assert(!projection.map.redraw && !projection.yard.redraw);

    scene.map_mode = 9;
    assert(portable_window_titles_update(&strings, &scene, &projection) ==
           PORTABLE_WINDOW_TITLES_INVALID_SCENE);
    /* Invalid input leaves the last valid, renderer-readable projection intact. */
    assert(renderer.resolve_text(renderer.text_context, 0, 1,
        format, sizeof format, &text, &text_size));

    portable_window_titles_free(&strings);
    portable_db_close(&database);
}

static void test_actual_string_database_is_required(void)
{
    PortableDatabase database = {0};
    PortableWindowTitlesStringSet strings = {0};
    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_titles_load(&strings, &database) ==
           PORTABLE_WINDOW_TITLES_DATABASE_ERROR);
    assert(!strings.loaded);
    portable_window_titles_free(&strings);
    portable_db_close(&database);
}

int main(void)
{
    test_actual_tables_and_all_title_indices();
    test_redraw_routing_and_renderer_resolver();
    test_actual_string_database_is_required();
    puts("window title model tests passed");
    return 0;
}
