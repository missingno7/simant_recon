#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUE_OPS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_QUEUE_OPS_H

#include "m1b73_queues.h"
#include "m1b73_events.h"
#include "../types/timer.h"

/* Native callback sidecars replace the DOS far callback words at record +8.
 * This callback shape is the actual five-word stack pushed by 0CEF, in C
 * argument order. Its return value is the source AX stop/continue decision. */
typedef int16_t (*PortableM1B73SourceQueueCallback)(
    void *context, int16_t id, uint16_t flags, uint16_t status,
    int16_t x, int16_t y);

typedef struct PortableM1B73QueueOpsServices {
    void *context;
    /* Resolve a Timer.fn identity without casting or serializing its pointer. */
    int (*resolve_timer_callback)(
        void *context, const struct Timer *timer,
        PortableM1B73SourceQueueCallback *callback,
        void **callback_context);
    /* 0196 hide/prepares the cursor around queue-3 changes. */
    int (*prepare_cursor_change)(void *context);
    /* 00D9 refreshes the cursor/hot-box owner after a queue-3 change. */
    int (*refresh_cursor)(void *context);
    /* 09E9 maps and warps a source-coordinate pointer through the active view. */
    int (*warp_source_pointer)(void *context, int16_t x, int16_t y);
    /* INT 33h function 3 equivalent: return source mouse-button status bits. */
    int (*read_mouse_buttons)(void *context, uint16_t *buttons);
    /* A40/A6C key table / hook behavior, backed by the shared SDL input owner. */
    int (*set_keyboard_hook)(void *context, int enabled);
    /* Native platform action for the actual D4B cursor-mode state transition.
     * Return the AX value that the original renderer leaf leaves for dispatch. */
    int (*set_cursor_mode)(void *context, uint8_t mode, int16_t *source_ax);
    /* The 128-byte scan-state table's canonical native owner, initialized with
     * 0x80 values as in m1B73.asm. A6C mutates this owner in place. */
    uint8_t *scan_state_table;
    PortableM1B73Events *events;
} PortableM1B73QueueOpsServices;

int portable_m1b73_queue_ops_bind(
    const PortableM1B73QueueOpsServices *services);
void portable_m1b73_queue_ops_unbind(void);
void portable_m1b73_queue_ops_clear_sidecars(void);
int portable_m1b73_queue_ops_dispatch_record(
    void *context, uint8_t queue_index, uint8_t record_index,
    const uint8_t record[PORTABLE_M1B73_QUEUE_RECORD_BYTES],
    const PortableM1B73QueueEvent *event);
int portable_m1b73_queue_ops_hit_test(
    int16_t x, int16_t y, uint16_t query, uint32_t *hotbox_token);

/* Remaining original m1B73 queue/input exports implemented here. */
void f_1B73_0AC3(struct Timer *timer, PortableM1B73Queue *slot);
void f_1B73_0B00(struct Timer *timer, PortableM1B73Queue *slot);
void f_1B73_0B5B(int16_t id, PortableM1B73Queue *slot);
int16_t f_1B73_0BC5(int16_t id, PortableM1B73Queue *slot);
int16_t f_1B73_0BFF(void);
void f_1B73_0C80(int16_t id);
void f_1B73_0A40(void);
void f_1B73_0A6C(void);
int16_t f_1B73_0D4B(int16_t mode);

#endif
