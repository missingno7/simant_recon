#include "../../platform/memory.h"
#include "../../game/recovered/memory_adapter.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void check(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "platform memory test failed: %s\n", message);
        exit(1);
    }
}

static void fill(uint8_t *data, size_t size)
{
    size_t i;
    for (i = 0; i < size; ++i)
        data[i] = (uint8_t)(i * 37u + 11u);
}

static void test_copy_direction(void)
{
    uint8_t data[32], expected[32];
    uint8_t *returned;

    fill(data, sizeof(data));
    memcpy(expected, data, sizeof(data));
    for (size_t i = 0; i + 1u < 8u; i += 2u) {
        uint8_t low = expected[i];
        uint8_t high = expected[i + 1u];
        expected[3u + i] = low;
        expected[4u + i] = high;
    }
    returned = (uint8_t *)portable_fmemcpy(data + 3, data, 8);
    check(returned == data + 3, "_fmemcpy return pointer");
    check(memcmp(data, expected, sizeof(data)) == 0,
          "_fmemcpy must retain original forward overlap behavior");

    fill(data, sizeof(data));
    memcpy(expected, data, sizeof(data));
    memmove(expected + 2, expected + 7, 8);
    returned = (uint8_t *)portable_fmemcpy(data + 2, data + 7, 8);
    check(returned == data + 2 && memcmp(data, expected, sizeof(data)) == 0,
          "forward _fmemcpy non-overlapping copy");
    check(portable_fmemcpy(NULL, NULL, 0) == NULL, "zero-count _fmemcpy");
}

static void test_move_direction(void)
{
    uint8_t actual[32], expected[32];

    fill(actual, sizeof(actual));
    memcpy(expected, actual, sizeof(actual));
    memmove(expected + 3, expected, 17);
    check(portable_fmemmove(actual + 3, actual, 17) == actual + 3,
          "_fmemmove backward return pointer");
    check(memcmp(actual, expected, sizeof(actual)) == 0,
          "_fmemmove must preserve right-overlap bytes");

    fill(actual, sizeof(actual));
    memcpy(expected, actual, sizeof(actual));
    memmove(expected, expected + 4, 19);
    check(portable_fmemmove(actual, actual + 4, 19) == actual,
          "_fmemmove forward return pointer");
    check(memcmp(actual, expected, sizeof(actual)) == 0,
          "_fmemmove must preserve left-overlap bytes");
    check(portable_fmemmove(NULL, NULL, 0) == NULL, "zero-count _fmemmove");
}

static void test_blockmove_and_abs(void)
{
    uint8_t source[9], destination[9];
    fill(source, sizeof(source));
    memset(destination, 0, sizeof(destination));
    portable_block_move(source, destination, (uint16_t)sizeof(source));
    check(memcmp(source, destination, sizeof(source)) == 0,
          "BlockMove source/destination order");
    memset(destination, 0, sizeof(destination));
    BlockMove(source, destination, (int32_t)sizeof(source));
    check(memcmp(source, destination, sizeof(source)) == 0,
          "recovered BlockMove adapter");
    check(_fmemcpy(destination, source, (uint16_t)sizeof(source)) == destination,
          "recovered _fmemcpy adapter");
    check(_fmemmove(destination, source, (uint16_t)sizeof(source)) == destination,
          "recovered _fmemmove adapter");
    check(portable_abs16(INT16_MIN) == INT16_MIN, "ABS signed-min wrap");
    check(portable_abs16(-32767) == 32767, "ABS negative value");
    check(portable_abs16(-1) == 1 && portable_abs16(0) == 0 &&
          portable_abs16(32767) == 32767, "ABS ordinary values");
    check(ABS(INT16_MIN) == INT16_MIN && ABS(-17) == 17,
          "recovered ABS adapter");
}

int main(void)
{
    test_copy_direction();
    test_move_direction();
    test_blockmove_and_abs();
    puts("platform memory tests passed");
    return 0;
}
