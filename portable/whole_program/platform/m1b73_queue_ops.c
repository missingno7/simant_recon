#include "m1b73_queue_ops.h"
#include "m1b73_mouse_state.h"

#include "input_time.h"

#include <stdlib.h>
#include <string.h>

enum { PORTABLE_M1B73_QUEUE_MAX_RECORDS = 48 };

typedef struct PortableM1B73CallbackSidecar {
    PortableM1B73SourceQueueCallback callback;
    void *context;
} PortableM1B73CallbackSidecar;

static PortableM1B73CallbackSidecar callback_sidecars[
    PORTABLE_M1B73_QUEUE_COUNT][PORTABLE_M1B73_QUEUE_MAX_RECORDS];
static PortableM1B73QueueOpsServices active_ops;
static uint8_t ops_bound;
static uint8_t cursor_mode = UINT8_C(0xff); /* ASM code-segment initializer */

/* Source ASM globals consumed by the keyboard/cursor navigation paths. */
uint8_t g_4362;
uint8_t g_4363;
uint8_t g_4368;
uint8_t g_4369;

static void require_ops(void)
{
    if (!ops_bound || active_ops.events == NULL ||
        active_ops.events->input_host == NULL ||
        active_ops.events->source_shift_state == NULL ||
        !active_ops.events->bound || active_ops.scan_state_table == NULL)
        abort();
}

static uint8_t queue_index(const PortableM1B73Queue *queue)
{
    uint8_t i;
    if (queue == NULL)
        abort();
    for (i = 0; i < PORTABLE_M1B73_QUEUE_COUNT; ++i) {
        if (queue == &portable_m1b73_queue_set.queues[i])
            return i;
    }
    abort(); /* no foreign queue storage or offset-based pointer casts */
}

static void validate_queue(const PortableM1B73Queue *queue, uint8_t index)
{
    if (queue->records == NULL || queue->capacity == 0 ||
        queue->capacity > queue->allocated_record_count ||
        queue->allocated_record_count > PORTABLE_M1B73_QUEUE_MAX_RECORDS ||
        queue->count > queue->capacity ||
        queue->records != portable_m1b73_queue_set.queues[index].records)
        abort();
}

static uint16_t read_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static int16_t read_i16(const uint8_t *p)
{
    uint16_t bits = read_u16(p);
    int16_t value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static void write_u16(uint8_t *p, uint16_t bits)
{
    p[0] = (uint8_t)bits;
    p[1] = (uint8_t)(bits >> 8);
}

static void write_i16(uint8_t *p, int16_t value)
{
    uint16_t bits;
    memcpy(&bits, &value, sizeof(bits));
    write_u16(p, bits);
}

static int contains_inclusive(const uint8_t *record, int16_t x, int16_t y)
{
    return x >= read_i16(record + 0) && x <= read_i16(record + 4) &&
           y >= read_i16(record + 2) && y <= read_i16(record + 6);
}

static void require_timer_sidecar(const struct Timer *timer,
                                  PortableM1B73CallbackSidecar *sidecar)
{
    if (!ops_bound || timer == NULL || sidecar == NULL ||
        active_ops.resolve_timer_callback == NULL ||
        !active_ops.resolve_timer_callback(active_ops.context, timer,
            &sidecar->callback, &sidecar->context) ||
        sidecar->callback == NULL)
        abort();
}

static void write_timer_record(uint8_t *record, const struct Timer *timer)
{
    write_i16(record + 0, timer->r.left);
    write_i16(record + 2, timer->r.top);
    write_i16(record + 4, timer->r.right);
    write_i16(record + 6, timer->r.bottom);
    /* +8..+11 are the old far pointer; native function pointers live only in
     * callback_sidecars and are never truncated into the 18-byte DOS row. */
    memset(record + 8, 0, 4);
    write_i16(record + 12, timer->ticks);
    record[14] = (uint8_t)timer->a;
    record[15] = (uint8_t)timer->b;
    record[16] = (uint8_t)timer->c;
    record[17] = (uint8_t)timer->d;
}

int portable_m1b73_queue_ops_bind(
    const PortableM1B73QueueOpsServices *services)
{
    PortableM1B73QueueServices queue_services;
    if (services == NULL || services->events == NULL ||
        services->events->input_host == NULL ||
        services->events->source_shift_state == NULL ||
        !services->events->bound || services->scan_state_table == NULL ||
        services->resolve_timer_callback == NULL || ops_bound)
        return 0;
    active_ops = *services;
    queue_services.context = NULL;
    queue_services.dispatch_record = portable_m1b73_queue_ops_dispatch_record;
    if (!portable_m1b73_queues_bind(&queue_services)) {
        memset(&active_ops, 0, sizeof(active_ops));
        return 0;
    }
    ops_bound = 1;
    return 1;
}

void portable_m1b73_queue_ops_unbind(void)
{
    portable_m1b73_queues_unbind();
    memset(&active_ops, 0, sizeof(active_ops));
    ops_bound = 0;
}

void portable_m1b73_queue_ops_clear_sidecars(void)
{
    memset(callback_sidecars, 0, sizeof(callback_sidecars));
    cursor_mode = UINT8_C(0xff);
}

int portable_m1b73_queue_ops_dispatch_record(
    void *context, uint8_t index, uint8_t record_index,
    const uint8_t record[PORTABLE_M1B73_QUEUE_RECORD_BYTES],
    const PortableM1B73QueueEvent *event)
{
    PortableM1B73CallbackSidecar *sidecar;
    (void)context;
    if (!ops_bound || index >= PORTABLE_M1B73_QUEUE_COUNT ||
        record_index >= PORTABLE_M1B73_QUEUE_MAX_RECORDS ||
        record == NULL || event == NULL)
        abort();
    sidecar = &callback_sidecars[index][record_index];
    if (sidecar->callback == NULL)
        abort(); /* source callback is required; never report empty success */
    return sidecar->callback(sidecar->context,
        read_i16(record + 12), read_u16(record + 14),
        event->status, event->x, event->y) != 0;
}

int portable_m1b73_queue_ops_hit_test(
    int16_t x, int16_t y, uint16_t query, uint32_t *hotbox_token)
{
    PortableM1B73Queue *queue = &portable_m1b73_queue_set.queues[3];
    uint8_t index = 3;
    uint8_t i;
    validate_queue(queue, index);
    if (hotbox_token == NULL)
        return -1;
    *hotbox_token = 0;
    for (i = 0; i < queue->count; ++i) {
        const uint8_t *record = queue->records[i];
        if ((read_u16(record + 16) & query) != 0 &&
            contains_inclusive(record, x, y)) {
            *hotbox_token = (uint32_t)i + 1u;
            return 1;
        }
    }
    return 0;
}

void f_1B73_0AC3(struct Timer *timer, PortableM1B73Queue *slot)
{
    PortableM1B73CallbackSidecar sidecar = { 0 };
    uint8_t index = queue_index(slot);
    validate_queue(slot, index);
    if (slot->count >= slot->capacity || slot->count >= slot->allocated_record_count)
        abort(); /* original capacity overflow calls Punt */
    require_timer_sidecar(timer, &sidecar);
    write_timer_record(slot->records[slot->count], timer);
    callback_sidecars[index][slot->count] = sidecar;
    ++slot->count;
}

void f_1B73_0B00(struct Timer *timer, PortableM1B73Queue *slot)
{
    PortableM1B73CallbackSidecar sidecar = { 0 };
    uint8_t index = queue_index(slot);
    uint16_t old_count;
    validate_queue(slot, index);
    if (index == 3) {
        if (!ops_bound || active_ops.prepare_cursor_change == NULL ||
            !active_ops.prepare_cursor_change(active_ops.context))
            abort();
    }
    if (slot->count >= slot->capacity || slot->count >= slot->allocated_record_count)
        abort();
    require_timer_sidecar(timer, &sidecar);
    old_count = slot->count;
    if (old_count != 0) {
        uint16_t row;
        for (row = old_count; row != 0; --row)
            memcpy(slot->records[row], slot->records[row - 1u],
                   PORTABLE_M1B73_QUEUE_RECORD_BYTES);
        memmove(&callback_sidecars[index][1],
            &callback_sidecars[index][0],
            (size_t)old_count * sizeof(callback_sidecars[index][0]));
    }
    write_timer_record(slot->records[0], timer);
    callback_sidecars[index][0] = sidecar;
    slot->count = (uint16_t)(old_count + 1u);
    if (index == 3 && (active_ops.refresh_cursor == NULL ||
        !active_ops.refresh_cursor(active_ops.context)))
        abort();
}

void f_1B73_0B5B(int16_t id, PortableM1B73Queue *slot)
{
    uint8_t index = queue_index(slot);
    uint16_t i;
    int restore_cursor = 0;
    validate_queue(slot, index);
    /* Source hides before lookup only when signed g_4365 is positive. The
     * matching 00D9 restore runs after the search even when no ID matched. */
    if (index == 3 && g_4365 != 0 && g_4365 < 0x80) {
        if (!ops_bound || active_ops.prepare_cursor_change == NULL ||
            !active_ops.prepare_cursor_change(active_ops.context))
            abort();
        restore_cursor = 1;
    }
    for (i = 0; i < slot->count; ++i) {
        if (read_i16(slot->records[i] + 12) == id) {
            uint16_t new_count = (uint16_t)(slot->count - 1u);
            uint16_t rows_after = (uint16_t)(new_count - i);
            uint16_t row;
            for (row = 0; row < rows_after; ++row)
                memcpy(slot->records[i + row], slot->records[i + row + 1u],
                       PORTABLE_M1B73_QUEUE_RECORD_BYTES);
            if (rows_after != 0) {
                memmove(&callback_sidecars[index][i],
                    &callback_sidecars[index][i + 1u],
                    (size_t)rows_after * sizeof(callback_sidecars[index][0]));
            }
            memset(&callback_sidecars[index][new_count], 0,
                   sizeof(callback_sidecars[index][new_count]));
            slot->count = new_count;
            break;
        }
    }
    if (restore_cursor && (active_ops.refresh_cursor == NULL ||
        !active_ops.refresh_cursor(active_ops.context)))
        abort();
}

int16_t f_1B73_0BC5(int16_t id, PortableM1B73Queue *slot)
{
    uint16_t i;
    uint8_t index = queue_index(slot);
    validate_queue(slot, index);
    for (i = 0; i < slot->count; ++i) {
        const uint8_t *record = slot->records[i];
        if (read_i16(record + 12) == id &&
            g_9122 >= read_i16(record + 0) &&
            g_9122 <= read_i16(record + 4) &&
            g_9124 >= read_i16(record + 2) &&
            g_9124 <= read_i16(record + 6)) {
            return 1;
        }
    }
    return 0;
}

int16_t f_1B73_0BFF(void)
{
    PortableM1B73Queue *queue = &portable_m1b73_queue_set.queues[3];
    uint8_t i;
    validate_queue(queue, 3);
    for (i = 0; i < queue->count; ++i) {
        const uint8_t *record = queue->records[i];
        if (g_9122 >= read_i16(record + 0) &&
            g_9122 <= read_i16(record + 4) &&
            g_9124 >= read_i16(record + 2) &&
            g_9124 < read_i16(record + 6))
            return read_i16(record + 12);
    }
    return 0;
}

void f_1B73_0C80(int16_t id)
{
    PortableM1B73Queue *queue = &portable_m1b73_queue_set.queues[3];
    uint8_t i;
    validate_queue(queue, 3);
    for (i = 0; i < queue->count; ++i) {
        const uint8_t *record = queue->records[i];
        if (read_i16(record + 12) == id) {
            uint16_t xsum = (uint16_t)((uint16_t)read_i16(record + 0) +
                                       (uint16_t)read_i16(record + 4));
            uint16_t ysum = (uint16_t)((uint16_t)read_i16(record + 2) +
                                       (uint16_t)read_i16(record + 6));
            if (!ops_bound || active_ops.warp_source_pointer == NULL ||
                !active_ops.warp_source_pointer(active_ops.context,
                    (int16_t)(xsum >> 1), (int16_t)(ysum >> 1)))
                abort();
            return;
        }
    }
}

void f_1B73_0A6C(void)
{
    require_ops();
    memset(active_ops.scan_state_table, 0x80, 128);
    portable_input_time_set_numlock_policy(
        &active_ops.events->input_host->input_time, 1);
    if (active_ops.set_keyboard_hook == NULL ||
        !active_ops.set_keyboard_hook(active_ops.context, 1))
        abort();
}

void f_1B73_0A40(void)
{
    uint16_t buttons;
    f_1B73_0A6C();
    require_ops();
    if (active_ops.set_keyboard_hook == NULL ||
        !active_ops.set_keyboard_hook(active_ops.context, 0))
        abort();
    portable_input_time_set_numlock_policy(
        &active_ops.events->input_host->input_time, 0);
    if (active_ops.read_mouse_buttons == NULL ||
        !active_ops.read_mouse_buttons(active_ops.context, &buttons))
        abort();
    g_9120 = buttons;
    *active_ops.events->source_shift_state = 0;
    g_4362 = 0;
    g_4363 = 0;
    g_4368 = 0;
    g_4369 = 0;
}

int16_t f_1B73_0D4B(int16_t mode_arg)
{
    uint16_t bits = (uint16_t)mode_arg;
    uint8_t mode = (uint8_t)(bits & UINT16_C(3));
    int16_t source_ax;
    if (mode == 0)
        return (int16_t)(bits & UINT16_C(0xff00));
    if (cursor_mode == mode)
        abort(); /* source calls Punt on duplicate nonzero cursor mode */
    cursor_mode = mode;
    /* The original dispatch handles only modes 1 and 2. Mode 3 updates the
     * state byte but falls through both decrements with AL=1; it has no draw. */
    if (mode == 3)
        return (int16_t)((bits & UINT16_C(0xff00)) | UINT16_C(1));
    if (!ops_bound || active_ops.set_cursor_mode == NULL)
        abort();
    if (!active_ops.set_cursor_mode(active_ops.context, mode, &source_ax))
        abort();
    return source_ax;
}
