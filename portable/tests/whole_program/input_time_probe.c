#include "../../whole_program/platform/input_time.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct FakeServices {
    uint32_t ticks;
    uint16_t available_key;
    uint16_t read_keys[8];
    size_t read_count, read_next;
    int key_available;
    unsigned clear_count, read_count_calls, available_count_calls;
    uint32_t installed_vector, restored_vector;
    unsigned install_count, restore_count, cleanup_register_count;
    PortableInputTimeCleanup cleanup;
    void *cleanup_context;
} FakeServices;

static int read_ticks(void *context, uint32_t *ticks)
{
    FakeServices *fake = (FakeServices *)context;
    *ticks = fake->ticks;
    return 1;
}

static int key_available(void *context, uint16_t *key)
{
    FakeServices *fake = (FakeServices *)context;
    ++fake->available_count_calls;
    *key = fake->available_key;
    return fake->key_available;
}

static int read_key(void *context, uint16_t *key)
{
    FakeServices *fake = (FakeServices *)context;
    if (fake->read_next == fake->read_count)
        return -1;
    ++fake->read_count_calls;
    *key = fake->read_keys[fake->read_next++];
    return 1;
}

static int clear_numlock(void *context)
{
    ++((FakeServices *)context)->clear_count;
    return 1;
}

static int install_break(void *context, uint32_t new_vector, uint32_t *old_vector)
{
    FakeServices *fake = (FakeServices *)context;
    fake->installed_vector = new_vector;
    *old_vector = UINT32_C(0x56781234);
    ++fake->install_count;
    return 1;
}

static int restore_break(void *context, uint32_t old_vector)
{
    FakeServices *fake = (FakeServices *)context;
    fake->restored_vector = old_vector;
    ++fake->restore_count;
    return 1;
}

static int register_cleanup(void *context, PortableInputTimeCleanup cleanup,
                            void *cleanup_context)
{
    FakeServices *fake = (FakeServices *)context;
    fake->cleanup = cleanup;
    fake->cleanup_context = cleanup_context;
    ++fake->cleanup_register_count;
    return 1;
}

static int test_byteswap_copy(void)
{
    uint8_t dst[] = {1, 2, 3, 4, 5};
    uint8_t src[] = {9, 8, 7, 6, 5};
    f_1F58_0017(dst, src, 3);
    if (memcmp(dst, (uint8_t[]){9, 8, 7, 4, 5}, sizeof(dst)) != 0 ||
        memcmp(src, (uint8_t[]){1, 2, 3, 6, 5}, sizeof(src)) != 0)
        return 0;
    f_1F58_0017(NULL, NULL, 0);
    {
        uint8_t overlap[] = {1, 2, 3, 4};
        f_1F58_0017(overlap + 1, overlap, 3);
        if (memcmp(overlap, (uint8_t[]){2, 3, 4, 1}, sizeof(overlap)) != 0)
            return 0;
    }
    return f_1F58_0014() == 0;
}

static int test_keyboard(PortableInputTime *state, FakeServices *fake)
{
    int16_t pending;
    if (f_1F58_0038() != 0 || fake->clear_count != 1)
        return 0;
    f_1F58_007F('A');
    f_1F58_007F('B');
    pending = f_1F58_0038();
    if ((uint16_t)pending != 0x8042u || fake->clear_count != 2)
        return 0;
    if (f_1F58_005A() != 'B' || state->pending_key != 0x8041u ||
        state->second_pending_key != 0)
        return 0;
    if ((uint16_t)f_1F58_0038() != 0x8041u || f_1F58_005A() != 'A')
        return 0;
    if (f_1F58_0038() != 0 || fake->clear_count != 4 ||
        fake->available_count_calls != 2)
        return 0;

    fake->read_keys[fake->read_count++] = (uint16_t)(0x1eu << 8) | 'x';
    if (f_1F58_005A() != 'x')
        return 0;
    fake->read_keys[fake->read_count++] = (uint16_t)(0x48u << 8);
    if (f_1F58_0090() != 0x48 || state->pending_key != 0)
        return 0;
    fake->read_keys[fake->read_count++] = (uint16_t)(0x12u << 8) | 0xe9u;
    if (f_1F58_005A() != -23)
        return 0;
    return fake->read_count_calls == 3;
}

static int test_ctrl_break(PortableInputTime *state, FakeServices *fake)
{
    const uint16_t vector_words[] = {0x1234u, 0x5678u};
    f_1F58_00B8(vector_words);
    if (fake->installed_vector != UINT32_C(0x56781234) ||
        state->saved_ctrl_break_vector != UINT32_C(0x56781234) ||
        fake->install_count != 1 || fake->cleanup_register_count != 1 ||
        fake->cleanup == NULL || fake->cleanup_context != state)
        return 0;
    fake->cleanup(fake->cleanup_context);
    if (state->ctrl_break_installed || fake->restored_vector != UINT32_C(0x56781234) ||
        fake->restore_count != 1 || state->cleanup_status != PORTABLE_INPUT_TIME_OK)
        return 0;
    f_1F58_00B8(vector_words);
    f_1F58_00A1();
    return !state->ctrl_break_installed && fake->restore_count == 2;
}

int main(void)
{
    FakeServices fake;
    PortableInputTime state;
    PortableInputTimeServices services;
    uint32_t ticks = 0;
    memset(&fake, 0, sizeof(fake));
    memset(&services, 0, sizeof(services));
    fake.ticks = UINT32_C(0x89abcdef);
    services.context = &fake;
    services.read_logical_bios_ticks = read_ticks;
    services.key_available = key_available;
    services.read_key_blocking = read_key;
    services.clear_numlock_state = clear_numlock;
    services.install_ctrl_break = install_break;
    services.restore_ctrl_break = restore_break;
    services.register_exit_cleanup = register_cleanup;
    portable_input_time_init(&state, &services);
    portable_input_time_set_numlock_policy(&state, 1);
    if (portable_input_time_bind(&state) != PORTABLE_INPUT_TIME_OK ||
        portable_input_time_read_ticks(&state, &ticks) != PORTABLE_INPUT_TIME_OK ||
        ticks != fake.ticks || f_1F58_0006() != fake.ticks) {
        fputs("tick control failed\n", stderr);
        return 1;
    }
    {
        PortableInputTime unconfigured;
        int16_t key = 0;
        portable_input_time_init(&unconfigured, NULL);
        if (portable_input_time_read_ticks(&unconfigured, &ticks) !=
                PORTABLE_INPUT_TIME_PROVIDER_MISSING ||
            portable_input_time_key_available(&unconfigured, &key) !=
                PORTABLE_INPUT_TIME_PROVIDER_MISSING) {
            fputs("missing-provider control failed\n", stderr);
            return 1;
        }
    }
    fake.key_available = 0;
    if (!test_byteswap_copy() || !test_keyboard(&state, &fake)) {
        fputs("keyboard/byte-swap control failed\n", stderr);
        return 1;
    }
    if (!test_ctrl_break(&state, &fake)) {
        fputs("Ctrl-Break lifecycle control failed\n", stderr);
        return 1;
    }
    portable_input_time_unbind(&state);
    puts("PASS input/time source controls: logical ticks, BIOS key queue, pushback and Ctrl-Break service lifecycle");
    return 0;
}
