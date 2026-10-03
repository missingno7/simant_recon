#include "../../whole_program/platform/input_time.h"

#include <string.h>

static PortableInputTime test_state;

void input_time_test_init(void)
{
    portable_input_time_init(&test_state, 0);
    portable_input_time_set_numlock_policy(&test_state, 0);
    (void)portable_input_time_bind(&test_state);
}

void input_time_test_unbind(void)
{
    portable_input_time_unbind(&test_state);
}

uint16_t input_time_test_pending(unsigned index)
{
    return index == 0 ? test_state.pending_key : test_state.second_pending_key;
}

void input_time_test_exchange(uint8_t *destination, uint8_t *source, uint16_t count)
{
    f_1F58_0017(destination, source, count);
}

int16_t input_time_test_pushback(uint16_t character)
{
    f_1F58_007F(character);
    return 0;
}

int16_t input_time_test_available(void)
{
    return f_1F58_0038();
}

int16_t input_time_test_read_char(void)
{
    return f_1F58_005A();
}
