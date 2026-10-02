#include "balloon_queue.h"

#include <limits.h>
#include <string.h>

static int16_t signed16(uint16_t bits)
{
    if (bits <= (uint16_t)INT16_MAX)
        return (int16_t)bits;
    return (int16_t)(-1 - (int16_t)(UINT16_MAX - bits));
}

static int32_t signed32(uint32_t bits)
{
    if (bits <= (uint32_t)INT32_MAX)
        return (int32_t)bits;
    return -1 - (int32_t)(UINT32_MAX - bits);
}

static int16_t add16(int16_t left, int16_t right)
{
    return signed16((uint16_t)((uint16_t)left + (uint16_t)right));
}

static int16_t multiply_add16(int16_t value, int16_t factor, int16_t addend)
{
    return signed16((uint16_t)((uint32_t)(uint16_t)value *
                               (uint32_t)(uint16_t)factor +
                               (uint16_t)addend));
}

static int32_t add32(int32_t left, int16_t right, int16_t addend)
{
    return signed32((uint32_t)left + (uint16_t)right + (uint16_t)addend);
}

static int lookup(const PortableBalloonServices *services,
                  PortableBalloonMessageId id, const char **text)
{
    *text = NULL;
    return services->lookup_text(services->context, &id, text);
}

void portable_balloon_queue_init(PortableBalloonQueue *queue,
                                 const PortableBalloonViewport *viewport,
                                 int16_t pixel_width, int16_t pixel_height)
{
    if (queue == NULL)
        return;
    memset(queue, 0, sizeof(*queue));
    if (viewport != NULL)
        queue->viewport = *viewport;
    queue->pixel_width = pixel_width;
    queue->pixel_height = pixel_height;
}

PortableBalloonQueueStatus portable_balloon_queue_add(
    PortableBalloonQueue *queue, int16_t x, int16_t y, int16_t plane,
    int16_t style, PortableBalloonMessageId id, const char *borrowed_text)
{
    int16_t tx, ty, pixel_x, pixel_y;
    PortableBalloonQueuedMessage *entry;
    if (queue == NULL || queue->pixel_width == 0 ||
        queue->pixel_height == 0)
        return PORTABLE_BALLOON_QUEUE_BAD_ARGUMENT;
    if (style == 10) {
        tx = (int16_t)(x / queue->pixel_width);
        ty = (int16_t)(y / queue->pixel_height);
        pixel_x = x;
        pixel_y = y;
    } else {
        tx = x;
        ty = y;
        pixel_x = multiply_add16(x, queue->pixel_width, 8);
        pixel_y = multiply_add16(y, queue->pixel_height, 8);
    }
    if (queue->count >= PORTABLE_BALLOON_QUEUE_CAPACITY ||
        !portable_balloon_is_visible(&queue->viewport, plane, tx, ty))
        return PORTABLE_BALLOON_QUEUE_OK;
    entry = &queue->entries[queue->count++];
    entry->id = id;
    entry->borrowed_text = borrowed_text;
    entry->x_pixels = pixel_x;
    entry->y_pixels = pixel_y;
    entry->plane = plane;
    entry->style = style;
    return PORTABLE_BALLOON_QUEUE_OK;
}

static PortableBalloonQueueStatus queue_table_message(
    PortableBalloonFrame *frame, const PortableBalloonServices *services,
    PortableBalloonTextTable table, uint16_t index,
    int16_t x, int16_t y, int16_t plane, int16_t style)
{
    PortableBalloonMessageId id;
    const char *text;
    if (!lookup(services, (PortableBalloonMessageId){(uint16_t)table, index, 0},
                &text))
        return PORTABLE_BALLOON_QUEUE_MISSING_TEXT;
    id = (PortableBalloonMessageId){(uint16_t)table, index,
                                    (uint8_t)(text == NULL)};
    return portable_balloon_queue_add(&frame->queue, x, y, plane, style, id,
                                      text);
}

static PortableBalloonQueueStatus advance_if_terminator(
    PortableBalloonCueMessages *messages,
    const PortableBalloonServices *services,
    PortableBalloonTextTable table, uint16_t *index)
{
    PortableBalloonMessageId id;
    const char *text;
    *index = (uint16_t)(*index + 1u);
    id = (PortableBalloonMessageId){(uint16_t)table, *index, 0};
    if (!lookup(services, id, &text))
        return PORTABLE_BALLOON_QUEUE_MISSING_TEXT;
    if (text == NULL)
        *index = 0;
    (void)messages;
    return PORTABLE_BALLOON_QUEUE_OK;
}

static uint32_t tick(const PortableBalloonServices *services)
{
    return services->tick_count(services->context);
}

static int16_t random_value(const PortableBalloonServices *services,
                            PortableBalloonRandomFamily family)
{
    return services->random(services->context, family);
}

static PortableBalloonQueueStatus update_fight(
    PortableBalloonFrame *frame, const PortableBalloonServices *services)
{
    PortableBalloonCueMessages *m = &frame->messages;
    PortableBalloonCueState *cue = &frame->cue[PORTABLE_BALLOON_FIGHT];
    PortableBalloonQueueStatus status;
    uint16_t *index;
    int16_t *enabled;
    int32_t *timer;
    PortableBalloonTextTable table;
    int16_t style, random_range;
    if (cue->active == 0)
        return PORTABLE_BALLOON_QUEUE_OK;
    if (frame->cue_pause == 0 &&
        (services->tick_count == NULL || services->random == NULL))
        return PORTABLE_BALLOON_QUEUE_MISSING_SERVICE;
    for (int item = 0; item < 2; ++item) {
        index = item == 0 ? &m->fight_first_index : &m->fight_second_index;
        enabled = item == 0 ? &m->fight_first_enabled : &m->fight_second_enabled;
        timer = item == 0 ? &frame->timers.fight_first : &frame->timers.fight_second;
        table = item == 0 ? PORTABLE_BALLOON_TEXT_FIGHT : PORTABLE_BALLOON_TEXT_FIGHT_ALT;
        style = (int16_t)item;
        if (frame->cue_pause == 0 && *timer < signed32(tick(services))) {
            int32_t now = signed32(tick(services));
            int16_t random_add = random_value(services,
                                             PORTABLE_BALLOON_SRAND32);
            *timer = add32(now, random_add, 60);
            random_range = random_value(services, PORTABLE_BALLOON_SRAND2);
            if (random_range == 0) {
                *enabled = 1;
                status = advance_if_terminator(m, services, table, index);
                if (status != PORTABLE_BALLOON_QUEUE_OK)
                    return status;
            } else {
                *enabled = 0;
            }
        }
        if (*enabled != 0) {
            status = queue_table_message(frame, services, table, *index,
                                         cue->displayed.x, cue->displayed.y,
                                         cue->displayed_plane, style);
            if (status != PORTABLE_BALLOON_QUEUE_OK)
                return status;
        }
    }
    return PORTABLE_BALLOON_QUEUE_OK;
}

static PortableBalloonQueueStatus update_single(
    PortableBalloonFrame *frame, const PortableBalloonServices *services,
    PortableBalloonCueKind kind, int32_t *timer, int16_t *enabled,
    uint16_t *index, PortableBalloonTextTable table,
    PortableBalloonRandomFamily timer_family,
    PortableBalloonRandomFamily choice_family, int16_t delay, int16_t style)
{
    PortableBalloonCueState *cue = &frame->cue[kind];
    PortableBalloonQueueStatus status;
    if (cue->active == 0)
        return PORTABLE_BALLOON_QUEUE_OK;
    if (frame->cue_pause == 0 &&
        (services->tick_count == NULL || services->random == NULL))
        return PORTABLE_BALLOON_QUEUE_MISSING_SERVICE;
    if (frame->cue_pause == 0 && *timer < signed32(tick(services))) {
        int32_t now = signed32(tick(services));
        int16_t random_add = random_value(services, timer_family);
        *timer = add32(now, random_add, delay);
        if (random_value(services, choice_family) == 0) {
            *enabled = 1;
            status = advance_if_terminator(&frame->messages, services, table,
                                           index);
            if (status != PORTABLE_BALLOON_QUEUE_OK)
                return status;
        } else {
            *enabled = 0;
        }
    }
    if (*enabled != 0)
        return queue_table_message(frame, services, table, *index,
                                   cue->displayed.x, cue->displayed.y,
                                   cue->displayed_plane, style);
    return PORTABLE_BALLOON_QUEUE_OK;
}

PortableBalloonQueueStatus portable_balloon_draw_current(
    PortableBalloonFrame *frame, const PortableBalloonServices *services)
{
    static const PortableBalloonCueKind order[] = {
        PORTABLE_BALLOON_FIGHT,
        PORTABLE_BALLOON_EGG,
        PORTABLE_BALLOON_QUEEN,
        PORTABLE_BALLOON_REST
    };
    PortableBalloonCueState *cue;
    PortableBalloonQueueStatus status;
    unsigned i;
    if (frame == NULL || services == NULL || services->lookup_text == NULL)
        return PORTABLE_BALLOON_QUEUE_BAD_ARGUMENT;
    if (!frame->updates_enabled || frame->sprite_state != -1)
        return PORTABLE_BALLOON_QUEUE_OK;
    if (frame->cue_pause == 0) {
        for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i) {
            cue = &frame->cue[order[i]];
            if (cue->active != 0 ||
                (cue->pending.x >= 0 && cue->pending.y >= 0)) {
                if (services->tick_count == NULL || services->random == NULL)
                    return PORTABLE_BALLOON_QUEUE_MISSING_SERVICE;
            }
        }
    }
    for (i = 0; i < PORTABLE_BALLOON_CUE_COUNT; ++i) {
        cue = &frame->cue[order[i]];
        if (cue->active == 0 && cue->pending.x >= 0 && cue->pending.y >= 0) {
            cue->displayed = cue->pending;
            cue->displayed_plane = cue->pending_plane;
            cue->active = add16(cue->active, 1);
            if (order[i] == PORTABLE_BALLOON_FIGHT) {
                frame->timers.fight_second = 0;
                frame->timers.fight_first = 0;
            } else if (order[i] == PORTABLE_BALLOON_EGG) {
                frame->timers.egg = 0;
                frame->messages.egg_enabled = 0;
            } else if (order[i] == PORTABLE_BALLOON_QUEEN) {
                frame->timers.queen = 0;
                frame->messages.queen_enabled = 0;
            } else {
                frame->timers.rest = 0;
                frame->messages.rest_enabled = 0;
            }
        }
        if (i == 0) {
            status = update_fight(frame, services);
            if (status != PORTABLE_BALLOON_QUEUE_OK)
                return status;
        } else if (i == 1) {
            status = update_single(frame, services, PORTABLE_BALLOON_EGG,
                                   &frame->timers.egg,
                                   &frame->messages.egg_enabled,
                                   &frame->messages.egg_index,
                                   PORTABLE_BALLOON_TEXT_EGG,
                                   PORTABLE_BALLOON_SRAND32,
                                   PORTABLE_BALLOON_SRAND4, 170, 2);
            if (status != PORTABLE_BALLOON_QUEUE_OK)
                return status;
        } else if (i == 2) {
            status = update_single(frame, services, PORTABLE_BALLOON_QUEEN,
                                   &frame->timers.queen,
                                   &frame->messages.queen_enabled,
                                   &frame->messages.queen_index,
                                   PORTABLE_BALLOON_TEXT_QUEEN,
                                   PORTABLE_BALLOON_SRAND32,
                                   PORTABLE_BALLOON_SRAND4, 180, 2);
            if (status != PORTABLE_BALLOON_QUEUE_OK)
                return status;
        } else {
            status = update_single(frame, services, PORTABLE_BALLOON_REST,
                                   &frame->timers.rest,
                                   &frame->messages.rest_enabled,
                                   &frame->messages.rest_index,
                                   PORTABLE_BALLOON_TEXT_REST,
                                   PORTABLE_BALLOON_SRAND64,
                                   PORTABLE_BALLOON_SRAND2, 120, 2);
            if (status != PORTABLE_BALLOON_QUEUE_OK)
                return status;
        }
    }
    return PORTABLE_BALLOON_QUEUE_OK;
}
