#include "../../whole_program/platform/input_time.h"

#include <stddef.h>

typedef struct KeyQueue {
    const uint16_t *keys;
    size_t count;
    size_t next;
    unsigned calls;
} KeyQueue;

static PortableInputTime state;
static KeyQueue queue;

static int read_key(void *context, uint16_t *key)
{
    KeyQueue *q = (KeyQueue *)context;
    if (q->next >= q->count)
        return -1;
    ++q->calls;
    *key = q->keys[q->next++];
    return 1;
}

static void bind_state(const PortableInputTimeServices *services)
{
    portable_input_time_unbind(&state);
    portable_input_time_init(&state, services);
    (void)portable_input_time_bind(&state);
}

int16_t input_time_key_read_bios(const uint16_t *keys, size_t count)
{
    PortableInputTimeServices services = {0};
    queue.keys = keys;
    queue.count = count;
    queue.next = 0;
    queue.calls = 0;
    services.context = &queue;
    services.read_key_blocking = read_key;
    bind_state(&services);
    return f_1F58_0090();
}

int16_t input_time_key_read_seeded(uint16_t first, uint16_t second)
{
    bind_state(NULL);
    state.pending_key = first;
    state.second_pending_key = second;
    return f_1F58_0090();
}

unsigned input_time_key_provider_calls(void) { return queue.calls; }
uint16_t input_time_key_pending(unsigned index)
{
    return index == 0 ? state.pending_key : state.second_pending_key;
}
void input_time_key_unbind(void) { portable_input_time_unbind(&state); }
