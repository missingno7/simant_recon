#include "../../ui_model/windows/balloon_queue.h"

#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

typedef struct Fixture {
    const char *text[5][4];
    uint32_t ticks[32];
    size_t tick_count;
    size_t tick_at;
    int16_t random_values[32];
    PortableBalloonRandomFamily random_families[32];
    size_t random_count;
    size_t random_at;
} Fixture;

static int lookup_text(void *context, const PortableBalloonMessageId *id,
                       const char **text)
{
    Fixture *fixture = context;
    if (id == NULL || id->table >= 5 || id->index >= 4)
        return 0;
    *text = fixture->text[id->table][id->index];
    return 1;
}

static uint32_t next_tick(void *context)
{
    Fixture *fixture = context;
    assert(fixture->tick_at < fixture->tick_count);
    return fixture->ticks[fixture->tick_at++];
}

static int16_t next_random(void *context, PortableBalloonRandomFamily family)
{
    Fixture *fixture = context;
    assert(fixture->random_at < fixture->random_count);
    if (fixture->random_families[fixture->random_at] != family)
        fprintf(stderr, "S-RNG order mismatch at %zu: expected %d, got %d\n",
                fixture->random_at,
                (int)fixture->random_families[fixture->random_at], (int)family);
    assert(fixture->random_families[fixture->random_at] == family);
    return fixture->random_values[fixture->random_at++];
}

static PortableBalloonServices services(Fixture *fixture)
{
    PortableBalloonServices result = {fixture, next_tick, next_random,
                                      lookup_text};
    return result;
}

static PortableBalloonViewport view(void)
{
    PortableBalloonViewport result = {2, 10, 20, 32, 24};
    return result;
}

static void init_fixture(Fixture *fixture)
{
    size_t table, index;
    memset(fixture, 0, sizeof(*fixture));
    for (table = 0; table < 5; ++table)
        for (index = 0; index < 3; ++index)
            fixture->text[table][index] = "resource-owned balloon";
    for (table = 0; table < 5; ++table)
        fixture->text[table][3] = NULL;
}

static void test_queue_styles_visibility_and_cap(void)
{
    PortableBalloonQueue queue;
    PortableBalloonViewport viewport = view();
    PortableBalloonMessageId id = {PORTABLE_BALLOON_TEXT_CALLER, 7, 0};
    const char *borrowed = "borrowed";
    unsigned i;
    portable_balloon_queue_init(&queue, &viewport, 16, 16);
    assert(portable_balloon_queue_add(&queue, 11, 23, 2, 0, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(portable_balloon_queue_add(&queue, 12, 24, 2, 1, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(portable_balloon_queue_add(&queue, 13, 25, 2, 2, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(portable_balloon_queue_add(&queue, 224, 368, 2, 10, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(queue.count == 4);
    assert(queue.entries[0].x_pixels == 184 &&
           queue.entries[0].y_pixels == 376 && queue.entries[0].style == 0);
    assert(queue.entries[1].x_pixels == 200 &&
           queue.entries[1].y_pixels == 392 && queue.entries[1].style == 1);
    assert(queue.entries[2].x_pixels == 216 &&
           queue.entries[2].y_pixels == 408 && queue.entries[2].style == 2);
    assert(queue.entries[3].x_pixels == 224 &&
           queue.entries[3].y_pixels == 368 && queue.entries[3].style == 10);
    assert(queue.entries[0].id.table == PORTABLE_BALLOON_TEXT_CALLER &&
           queue.entries[0].id.index == 7 &&
           queue.entries[0].borrowed_text == borrowed);
    assert(portable_balloon_queue_add(&queue, 40, 24, 2, 0, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(portable_balloon_queue_add(&queue, 41, 24, 2, 0, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(queue.count == PORTABLE_BALLOON_QUEUE_CAPACITY);
    for (i = 0; i < 2; ++i)
        assert(portable_balloon_queue_add(&queue, 12, 24, 2, 0, id,
                                          borrowed) == PORTABLE_BALLOON_QUEUE_OK);
    assert(queue.count == PORTABLE_BALLOON_QUEUE_CAPACITY);
    assert(portable_balloon_queue_add(&queue, 12, 24, 3, 0, id, borrowed) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(queue.count == PORTABLE_BALLOON_QUEUE_CAPACITY);
}

static void test_signed_pixel_wrap_and_style_ten_truncation(void)
{
    PortableBalloonQueue queue;
    PortableBalloonViewport viewport = {0, 0, 0, 32767, 32767};
    PortableBalloonMessageId id = {PORTABLE_BALLOON_TEXT_CALLER, 2, 0};
    portable_balloon_queue_init(&queue, &viewport, 16, 16);
    assert(portable_balloon_queue_add(&queue, 32760, 32760, 0, 2, id, NULL) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(queue.count == 1);
    assert(queue.entries[0].x_pixels == (int16_t)(32760u * 16u + 8u));
    viewport = (PortableBalloonViewport){0, -20, -20, 40, 40};
    portable_balloon_queue_init(&queue, &viewport, 16, 16);
    assert(portable_balloon_queue_add(&queue, -17, -17, 0, 10, id, NULL) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(queue.count == 1 && queue.entries[0].x_pixels == -17 &&
           queue.entries[0].y_pixels == -17);
}

static void set_active_cues(PortableBalloonFrame *frame)
{
    unsigned i;
    for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i) {
        frame->cue[i].active = 1;
        frame->cue[i].displayed.x = 11 + (int16_t)i;
        frame->cue[i].displayed.y = 23;
        frame->cue[i].displayed_plane = 2;
    }
}

static void test_draw_current_message_table_identity_and_order(void)
{
    PortableBalloonFrame frame;
    PortableBalloonViewport viewport = view();
    PortableBalloonServices api;
    Fixture fixture;
    int16_t flags[5] = {1, 1, 1, 1, 1};
    PortableBalloonMessageId expected[] = {
        {PORTABLE_BALLOON_TEXT_FIGHT, 0, 0},
        {PORTABLE_BALLOON_TEXT_FIGHT_ALT, 0, 0},
        {PORTABLE_BALLOON_TEXT_EGG, 0, 0},
        {PORTABLE_BALLOON_TEXT_QUEEN, 0, 0},
        {PORTABLE_BALLOON_TEXT_REST, 0, 0}
    };
    unsigned i;
    memset(&frame, 0, sizeof(frame));
    init_fixture(&fixture);
    api = services(&fixture);
    portable_balloon_queue_init(&frame.queue, &viewport, 16, 16);
    frame.updates_enabled = 1;
    frame.sprite_state = -1;
    frame.cue_pause = 1; /* avoid timer service while checking queued messages */
    set_active_cues(&frame);
    frame.messages.fight_first_enabled = flags[0];
    frame.messages.fight_second_enabled = flags[1];
    frame.messages.egg_enabled = flags[2];
    frame.messages.queen_enabled = flags[3];
    frame.messages.rest_enabled = flags[4];
    assert(portable_balloon_draw_current(&frame, &api) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(frame.queue.count == 5);
    for (i = 0; i < 5; ++i) {
        assert(frame.queue.entries[i].id.table == expected[i].table);
        assert(frame.queue.entries[i].id.index == expected[i].index);
        assert(frame.queue.entries[i].style == (i < 2 ? (int16_t)i : 2));
        assert(frame.queue.entries[i].borrowed_text == fixture.text[i][0]);
    }
    assert(fixture.tick_at == 0 && fixture.random_at == 0);
}

static void test_activation_order_and_timer_resource_calls(void)
{
    PortableBalloonFrame frame;
    PortableBalloonViewport viewport = view();
    PortableBalloonServices api;
    PortableBalloonServices missing;
    Fixture fixture;
    memset(&frame, 0, sizeof(frame));
    init_fixture(&fixture);
    api = services(&fixture);
    missing = (PortableBalloonServices){&fixture, NULL, NULL, lookup_text};
    portable_balloon_queue_init(&frame.queue, &viewport, 16, 16);
    frame.updates_enabled = 1;
    frame.sprite_state = -1;
    frame.cue[PORTABLE_BALLOON_REST].pending = (PortableBalloonPoint){14, 27};
    frame.cue[PORTABLE_BALLOON_REST].pending_plane = 2;
    frame.cue[PORTABLE_BALLOON_QUEEN].pending = (PortableBalloonPoint){13, 27};
    frame.cue[PORTABLE_BALLOON_QUEEN].pending_plane = 2;
    frame.cue[PORTABLE_BALLOON_EGG].pending = (PortableBalloonPoint){12, 27};
    frame.cue[PORTABLE_BALLOON_EGG].pending_plane = 2;
    frame.cue[PORTABLE_BALLOON_FIGHT].pending = (PortableBalloonPoint){11, 27};
    frame.cue[PORTABLE_BALLOON_FIGHT].pending_plane = 2;
    assert(portable_balloon_draw_current(&frame, &missing) ==
           PORTABLE_BALLOON_QUEUE_MISSING_SERVICE);
    assert(frame.cue[PORTABLE_BALLOON_FIGHT].active == 0);
    assert(frame.cue[PORTABLE_BALLOON_EGG].active == 0);

    /* A second call is timer-free when pause is set and performs the pending
     * transfers in the source Fight/Egg/Queen/Rest order. */
    frame.cue_pause = 1;
    assert(portable_balloon_draw_current(&frame, &api) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(frame.cue[PORTABLE_BALLOON_FIGHT].active == 1 &&
           frame.cue[PORTABLE_BALLOON_EGG].active == 1 &&
           frame.cue[PORTABLE_BALLOON_QUEEN].active == 1 &&
           frame.cue[PORTABLE_BALLOON_REST].active == 1);
    assert(frame.cue[PORTABLE_BALLOON_FIGHT].displayed.x == 11 &&
           frame.cue[PORTABLE_BALLOON_REST].displayed.x == 14);
}

static void test_rest_uses_srand64_for_timer(void)
{
    PortableBalloonFrame frame;
    PortableBalloonViewport viewport = view();
    PortableBalloonServices api;
    Fixture fixture;
    unsigned i;
    memset(&frame, 0, sizeof(frame));
    /* Zero is a valid pending coordinate and activates an inactive cue.
     * Isolate the rest timer with the source's absent-cue sentinel. */
    for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i)
        frame.cue[i].pending = (PortableBalloonPoint){-1, -1};
    init_fixture(&fixture);
    fixture.ticks[0] = 1000;
    fixture.ticks[1] = 1000;
    fixture.tick_count = 2;
    fixture.random_families[0] = PORTABLE_BALLOON_SRAND64;
    fixture.random_values[0] = 63;
    fixture.random_families[1] = PORTABLE_BALLOON_SRAND2;
    fixture.random_values[1] = 1;
    fixture.random_count = 2;
    api = services(&fixture);
    portable_balloon_queue_init(&frame.queue, &viewport, 16, 16);
    frame.updates_enabled = 1;
    frame.sprite_state = -1;
    frame.cue[PORTABLE_BALLOON_REST].active = 1;
    frame.cue[PORTABLE_BALLOON_REST].displayed =
        (PortableBalloonPoint){14, 27};
    frame.cue[PORTABLE_BALLOON_REST].displayed_plane = 2;
    assert(portable_balloon_draw_current(&frame, &api) ==
           PORTABLE_BALLOON_QUEUE_OK);
    assert(frame.timers.rest == 1183);
    assert(frame.messages.rest_enabled == 0);
    assert(fixture.tick_at == 2 && fixture.random_at == 2);
}

int main(void)
{
    test_queue_styles_visibility_and_cap();
    test_signed_pixel_wrap_and_style_ten_truncation();
    test_draw_current_message_table_identity_and_order();
    test_activation_order_and_timer_resource_calls();
    test_rest_uses_srand64_for_timer();
    puts("balloon queue model tests passed");
    return 0;
}
