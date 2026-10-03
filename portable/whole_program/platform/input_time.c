#include "input_time.h"

#include <stddef.h>
#include <stdlib.h>
#include <string.h>

static PortableInputTime *active_input_time;

static PortableInputTimeStatus provider_result(int result)
{
    return result == 1 ? PORTABLE_INPUT_TIME_OK : PORTABLE_INPUT_TIME_PROVIDER_FAILED;
}

void portable_input_time_init(PortableInputTime *input_time,
                              const PortableInputTimeServices *services)
{
    if (input_time == NULL)
        return;
    memset(input_time, 0, sizeof(*input_time));
    input_time->clear_numlock_policy = 1; /* original g_53BD initial datum */
    if (services != NULL)
        input_time->services = *services;
}

PortableInputTimeStatus portable_input_time_bind(PortableInputTime *input_time)
{
    if (input_time == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (active_input_time != NULL && active_input_time != input_time)
        return PORTABLE_INPUT_TIME_INVALID_LIFETIME;
    active_input_time = input_time;
    return PORTABLE_INPUT_TIME_OK;
}

void portable_input_time_unbind(PortableInputTime *input_time)
{
    if (input_time != NULL && active_input_time == input_time)
        active_input_time = NULL;
}

void portable_input_time_set_numlock_policy(PortableInputTime *input_time,
                                            uint8_t source_g_53BD)
{
    if (input_time != NULL)
        input_time->clear_numlock_policy = source_g_53BD;
}

PortableInputTimeStatus portable_input_time_read_ticks(PortableInputTime *input_time,
                                                        uint32_t *ticks)
{
    if (input_time == NULL || ticks == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (input_time->services.read_logical_bios_ticks == NULL)
        return PORTABLE_INPUT_TIME_PROVIDER_MISSING;
    return provider_result(input_time->services.read_logical_bios_ticks(
        input_time->services.context, ticks));
}

PortableInputTimeStatus portable_input_time_key_available(PortableInputTime *input_time,
                                                           int16_t *bios_ax)
{
    int result;
    uint16_t bios_key = 0;
    if (input_time == NULL || bios_ax == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (input_time->pending_key != 0) {
        *bios_ax = (int16_t)input_time->pending_key;
    } else {
        if (input_time->services.key_available == NULL)
            return PORTABLE_INPUT_TIME_PROVIDER_MISSING;
        result = input_time->services.key_available(input_time->services.context,
                                                    &bios_key);
        if (result < 0 || result > 1)
            return PORTABLE_INPUT_TIME_PROVIDER_FAILED;
        *bios_ax = result == 0 ? 0 : (int16_t)bios_key;
    }
    if (input_time->clear_numlock_policy != 0) {
        if (input_time->services.clear_numlock_state == NULL)
            return PORTABLE_INPUT_TIME_PROVIDER_MISSING;
        if (input_time->services.clear_numlock_state(input_time->services.context) != 1)
            return PORTABLE_INPUT_TIME_PROVIDER_FAILED;
    }
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_read_char(PortableInputTime *input_time,
                                                      int16_t *character)
{
    uint16_t bios_key;
    uint8_t ascii, scan;
    int result;
    if (input_time == NULL || character == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (input_time->pending_key != 0) {
        bios_key = input_time->pending_key;
        input_time->pending_key = input_time->second_pending_key;
        input_time->second_pending_key = 0;
        *character = (int16_t)(bios_key & 0xffu);
        return PORTABLE_INPUT_TIME_OK;
    }
    if (input_time->services.read_key_blocking == NULL)
        return PORTABLE_INPUT_TIME_PROVIDER_MISSING;
    result = input_time->services.read_key_blocking(input_time->services.context,
                                                    &bios_key);
    if (result != 1)
        return PORTABLE_INPUT_TIME_PROVIDER_FAILED;
    ascii = (uint8_t)bios_key;
    if (ascii != 0) {
        *character = (ascii & 0x80u) != 0
            ? (int16_t)((int16_t)ascii - 256) : (int16_t)ascii;
        return PORTABLE_INPUT_TIME_OK;
    }
    scan = (uint8_t)(bios_key >> 8);
    input_time->pending_key = (uint16_t)(((uint16_t)scan << 8) | scan);
    *character = 0;
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_read_key(PortableInputTime *input_time,
                                                     int16_t *key)
{
    PortableInputTimeStatus status;
    int16_t first, second;
    if (input_time == NULL || key == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    status = portable_input_time_read_char(input_time, &first);
    if (status != PORTABLE_INPUT_TIME_OK)
        return status;
    if (first != 0) {
        *key = first;
        return PORTABLE_INPUT_TIME_OK;
    }
    status = portable_input_time_read_char(input_time, &second);
    if (status != PORTABLE_INPUT_TIME_OK)
        return status;
    *key = second != 0 ? second : (int16_t)0x0800;
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_pushback(PortableInputTime *input_time,
                                                     uint8_t character)
{
    uint16_t old_pending;
    if (input_time == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    old_pending = input_time->pending_key;
    input_time->pending_key = (uint16_t)(0x8000u | character);
    input_time->second_pending_key = old_pending;
    return PORTABLE_INPUT_TIME_OK;
}

PortableInputTimeStatus portable_input_time_restore_ctrl_break(PortableInputTime *input_time)
{
    if (input_time == NULL)
        return PORTABLE_INPUT_TIME_BAD_ARGUMENT;
    if (!input_time->ctrl_break_saved_valid)
        return PORTABLE_INPUT_TIME_INVALID_LIFETIME;
    if (input_time->services.restore_ctrl_break == NULL)
        return PORTABLE_INPUT_TIME_PROVIDER_MISSING;
    if (input_time->services.restore_ctrl_break(input_time->services.context,
                                                 input_time->saved_ctrl_break_vector) != 1)
        return PORTABLE_INPUT_TIME_PROVIDER_FAILED;
    input_time->ctrl_break_installed = 0;
    input_time->cleanup_status = PORTABLE_INPUT_TIME_OK;
    return PORTABLE_INPUT_TIME_OK;
}

static void restore_at_exit(void *context)
{
    PortableInputTime *input_time = (PortableInputTime *)context;
    if (input_time == NULL)
        return;
    input_time->cleanup_status = portable_input_time_restore_ctrl_break(input_time);
}

static PortableInputTime *require_active(void)
{
    if (active_input_time == NULL)
        abort();
    return active_input_time;
}

uint32_t f_1F58_0006(void)
{
    uint32_t ticks;
    if (portable_input_time_read_ticks(require_active(), &ticks) != PORTABLE_INPUT_TIME_OK)
        abort();
    return ticks;
}

int16_t f_1F58_0014(void)
{
    return 0;
}

void f_1F58_0017(uint8_t *destination, uint8_t *source, uint16_t count)
{
    uint32_t i;
    if (count != 0 && (destination == NULL || source == NULL))
        abort();
    for (i = 0; i < count; ++i) {
        uint8_t temporary = destination[i];
        destination[i] = source[i];
        source[i] = temporary;
    }
}

int16_t f_1F58_0038(void)
{
    int16_t available;
    if (portable_input_time_key_available(require_active(), &available) != PORTABLE_INPUT_TIME_OK)
        abort();
    return available;
}

int16_t f_1F58_005A(void)
{
    int16_t character;
    if (portable_input_time_read_char(require_active(), &character) != PORTABLE_INPUT_TIME_OK)
        abort();
    return character;
}

void f_1F58_007F(uint16_t character)
{
    if (portable_input_time_pushback(require_active(), (uint8_t)character) != PORTABLE_INPUT_TIME_OK)
        abort();
}

int16_t f_1F58_0090(void)
{
    int16_t key;
    if (portable_input_time_read_key(require_active(), &key) != PORTABLE_INPUT_TIME_OK)
        abort();
    return key;
}

void f_1F58_00A1(void)
{
    if (portable_input_time_restore_ctrl_break(require_active()) != PORTABLE_INPUT_TIME_OK)
        abort();
}

void f_1F58_00B8(const uint16_t *new_vector_words)
{
    PortableInputTime *input_time = require_active();
    uint32_t new_vector, old_vector = 0;
    if (new_vector_words == NULL || input_time->ctrl_break_installed ||
        input_time->services.install_ctrl_break == NULL ||
        input_time->services.restore_ctrl_break == NULL ||
        input_time->services.register_exit_cleanup == NULL)
        abort();
    new_vector = ((uint32_t)new_vector_words[1] << 16) | new_vector_words[0];
    if (input_time->services.install_ctrl_break(input_time->services.context,
                                                new_vector, &old_vector) != 1)
        abort();
    input_time->saved_ctrl_break_vector = old_vector;
    input_time->ctrl_break_installed = 1;
    input_time->ctrl_break_saved_valid = 1;
    if (input_time->services.register_exit_cleanup(input_time->services.context,
                                                   restore_at_exit, input_time) != 1) {
        if (input_time->services.restore_ctrl_break(input_time->services.context,
                                                    old_vector) == 1) {
            input_time->ctrl_break_installed = 0;
            input_time->ctrl_break_saved_valid = 0;
        }
        abort();
    }
}
