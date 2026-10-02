#include "../../../game/resources/database.h"
#include "../../../ui_model/windows/decorations.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static const int16_t metric_ids[] = {0x64, 0x65, 0x66, 0x67, 0x69, 0x70};

static void load_metrics(PortableDatabase *db,
                         PortableWindowDecorationMetrics metrics[6])
{
    PortableDatabase shared;
    size_t i;
    assert(portable_db_open(db, "assets/HCEGANT") == PORTABLE_DB_OK);
    for (i = 0; i < 6; ++i) {
        PortableDbRecord record;
        assert(portable_db_load(db, metric_ids[i], 2, &record) == PORTABLE_DB_OK);
        assert(record.size >= 12);
        metrics[i].object_id = metric_ids[i];
        metrics[i].width = (int16_t)(record.data[8] | (record.data[9] << 8));
        metrics[i].height = (int16_t)(record.data[10] | (record.data[11] << 8));
        portable_db_record_free(&record);
    }
    assert(metrics[0].width == 15 && metrics[0].height == 15);
    assert(metrics[1].width == 15 && metrics[1].height == 15);
    assert(metrics[2].width == 15 && metrics[2].height == 15);
    assert(metrics[3].width == 15 && metrics[3].height == 15);
    assert(metrics[4].width == 15 && metrics[4].height == 15);
    assert(metrics[5].width == 16 && metrics[5].height == 16);
    assert(portable_db_open(&shared, "assets/SHARED") == PORTABLE_DB_OK);
    for (i = 0; i < 6; ++i) {
        const PortableDbIndexEntry *entry = 0;
        assert(portable_db_lookup(&shared, metric_ids[i], 2, &entry, 0) ==
               PORTABLE_DB_NOT_FOUND);
        assert(entry == 0);
    }
    portable_db_close(&shared);
}

static int overlaps(PortableWindowRect a, PortableWindowRect b)
{
    return a.left <= b.right && b.left <= a.right &&
           a.top <= b.bottom && b.top <= a.bottom;
}

static void print_plan(const char *label, const PortableWindowDecorationMetrics *metrics,
                       size_t metric_count, int flags, int show, int margin)
{
    PortableWindowDecorationInput input;
    PortableWindowDecorationStep steps[PORTABLE_WINDOW_DECORATION_MAX_STEPS];
    size_t i, count = 0;
    memset(&input, 0, sizeof(input));
    input.window_rect = (PortableWindowRect){10, 20, 210, 120};
    input.window_flags = (int16_t)flags;
    input.margin = (int8_t)margin;
    input.show = (uint8_t)show;
    input.metrics = metrics;
    input.metric_count = metric_count;
    assert(portable_window_decorations_plan(&input, steps,
           PORTABLE_WINDOW_DECORATION_MAX_STEPS, &count) == PORTABLE_WINDOW_DECORATION_OK);
    printf("{\"label\":\"%s\",\"steps\":[", label);
    for (i = 0; i < count; ++i) {
        const PortableWindowDecorationStep *s = &steps[i];
        if (i) putchar(',');
        if (s->kind == PORTABLE_WINDOW_DECORATION_LOOKUP_SIZE) {
            printf("{\"kind\":\"lookup\",\"id\":%d}", s->object_id);
        } else if (s->kind == PORTABLE_WINDOW_DECORATION_UNREGISTER) {
            printf("{\"kind\":\"unregister\",\"id\":%d,\"mode\":%d}",
                   s->object_id, (uint16_t)s->mode);
        } else {
            printf("{\"kind\":\"register\",\"id\":%d,\"mode\":%d,\"rect\":[%d,%d,%d,%d]}",
                   s->object_id, (uint16_t)s->mode,
                   s->hit_rect.left, s->hit_rect.top,
                   s->hit_rect.right, s->hit_rect.bottom);
        }
    }
    puts("]}");
}

int main(void)
{
    PortableDatabase db;
    PortableWindowDecorationMetrics metrics[6];
    PortableWindowDecorationInput input;
    PortableWindowDecorationStep steps[PORTABLE_WINDOW_DECORATION_MAX_STEPS];
    PortableWindowDecorationHit hit;
    size_t count;
    unsigned combination, max_select, show;
    PortableWindowRect object_overlap = {200, 25, 210, 36};
    PortableWindowRect object_disjoint = {208, 25, 218, 36};
    load_metrics(&db, metrics);
    printf("{\"metrics\":[");
    for (count = 0; count < 6; ++count) {
        if (count) putchar(',');
        printf("[%d,%d,%d]", metrics[count].object_id,
               metrics[count].width, metrics[count].height);
    }
    puts("],\"shared_ids_absent\":true}");
    print_plan("all-flags-maximized", metrics, 6, 0x059c, 1, 3);
    print_plan("all-flags-normal", metrics, 6, 0x051c, 1, 3);
    print_plan("all-flags-unregister", metrics, 6, 0x059c, 0, 3);
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
                int case_flags = flags | (max_select ? 0x0080 : 0);
                (void)snprintf(label, sizeof(label), "matrix-%02x-%u-%u",
                               combination, max_select, show);
                print_plan(label, metrics, 6, case_flags, (int)show, 3);
            }
        }
    }
    print_plan("margin-neg128", metrics, 6, 0x0004, 1, -128);
    print_plan("margin-neg1", metrics, 6, 0x0004, 1, -1);
    print_plan("margin-zero", metrics, 6, 0x0004, 1, 0);
    print_plan("margin-pos127", metrics, 6, 0x0004, 1, 127);

    memset(&input, 0, sizeof(input));
    input.window_rect = (PortableWindowRect){10, 20, 210, 120};
    input.window_flags = 0x0100;
    input.margin = 3;
    input.show = 1;
    input.metrics = metrics;
    input.metric_count = 6;
    assert(portable_window_decorations_plan(&input, steps,
           PORTABLE_WINDOW_DECORATION_MAX_STEPS, &count) == PORTABLE_WINDOW_DECORATION_OK);
    assert(count == 3 && steps[2].object_id == 0x67);
    assert(overlaps(steps[2].hit_rect, object_overlap));
    assert(!overlaps(steps[2].hit_rect, object_disjoint));

    input.window_rect = (PortableWindowRect){10, 20, 210, 120};
    input.window_flags = 0x059c;
    input.margin = 3;
    assert(portable_window_decorations_plan(&input, steps,
           PORTABLE_WINDOW_DECORATION_MAX_STEPS, &count) == PORTABLE_WINDOW_DECORATION_OK);
    assert(portable_window_decoration_hit_test(steps, count,
           (PortableWindowPoint){200, 30}, &hit));
    assert(hit.object_id == 0x66 && hit.mode == (int16_t)0xf085);
    assert(portable_window_decoration_hit_test(steps, count,
           (PortableWindowPoint){207, 38}, &hit)); /* right/bottom inclusive */
    assert(hit.object_id == 0x66);
    assert(!portable_window_decoration_hit_test(steps, count,
           (PortableWindowPoint){208, 30}, &hit));

    input.window_flags = 4;
    input.window_rect = (PortableWindowRect){32760, 20, 32767, 120};
    input.margin = 0;
    assert(portable_window_decorations_plan(&input, steps,
           PORTABLE_WINDOW_DECORATION_MAX_STEPS, &count) ==
           PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW);
    input.window_flags = 0x0100;
    input.window_rect = (PortableWindowRect){-32768, 20, -32760, 120};
    assert(portable_window_decorations_plan(&input, steps,
           PORTABLE_WINDOW_DECORATION_MAX_STEPS, &count) ==
           PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW);

    input.window_flags = 0x0100;
    input.metrics = metrics;
    input.metric_count = 0;
    assert(portable_window_decorations_plan(&input, steps,
           PORTABLE_WINDOW_DECORATION_MAX_STEPS, &count) ==
           PORTABLE_WINDOW_DECORATION_MISSING_METRIC);
    portable_db_close(&db);
    return 0;
}
