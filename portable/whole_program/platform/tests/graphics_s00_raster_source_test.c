#include "../graphics_s00_raster_source.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char g_3D20[128];

enum {
    TEST_WIDTH = 112,
    TEST_STRIDE = TEST_WIDTH / 8,
    TEST_ROWS = 64,
    TEST_SPAN = (TEST_ROWS - 1) * TEST_STRIDE + 2,
    LEGACY_WRAPPER_SPAN = 31 * TEST_STRIDE + 2
};

static void check(int condition, const char *expression, int line)
{
    if (!condition) {
        fprintf(stderr, "check failed at line %d: %s\n", line, expression);
        exit(2);
    }
}

#define CHECK(expression) check((expression), #expression, __LINE__)

static void fill_pattern(uint8_t pattern[128])
{
    unsigned i;
    for (i = 0; i < 128u; ++i)
        pattern[i] = (uint8_t)(i ^ 0x5au);
}

static void check_transfer(const uint8_t *destination, uint8_t untouched)
{
    unsigned row;
    size_t column;
    for (row = 0; row < TEST_ROWS; ++row) {
        for (column = 0; column < TEST_STRIDE; ++column) {
            if (row == TEST_ROWS - 1u && column >= 2u)
                continue;
            uint8_t expected = column < 2u
                ? g_3D20[row * 2u + column] : untouched;
            if (destination[(size_t)row * TEST_STRIDE + column] != expected) {
                fprintf(stderr,
                        "row %u column %lu: got %02x want %02x\n", row,
                        (unsigned long)column,
                        destination[(size_t)row * TEST_STRIDE + column],
                        expected);
            }
            CHECK(destination[(size_t)row * TEST_STRIDE + column] == expected);
        }
    }
}

int main(void)
{
    uint8_t destination[TEST_SPAN + 2];
    uint8_t too_small[TEST_SPAN];
    SimS00RasterStatus status;
    size_t i;

    fill_pattern((uint8_t *)g_3D20);
    memset(destination, 0xcc, sizeof destination);
    status = sim_s00_raster_pattern_transfer(
        (const uint8_t *)g_3D20, destination, TEST_SPAN, TEST_WIDTH);
    CHECK(status == SIM_S00_RASTER_OK);
    check_transfer(destination, 0xcc);
    CHECK(destination[TEST_SPAN] == 0xcc);
    CHECK(destination[TEST_SPAN + 1] == 0xcc);

    /* Negative controls: one byte short and the old 32-row wrapper extent. */
    memset(too_small, 0xa7, sizeof too_small);
    status = sim_s00_raster_pattern_transfer(
        (const uint8_t *)g_3D20, too_small, TEST_SPAN - 1u, TEST_WIDTH);
    CHECK(status == SIM_S00_RASTER_BUFFER_TOO_SMALL);
    for (i = 0; i < sizeof too_small; ++i)
        CHECK(too_small[i] == 0xa7);
    status = sim_s00_raster_pattern_transfer(
        (const uint8_t *)g_3D20, too_small, LEGACY_WRAPPER_SPAN, TEST_WIDTH);
    CHECK(status == SIM_S00_RASTER_BUFFER_TOO_SMALL);
    for (i = 0; i < sizeof too_small; ++i)
        CHECK(too_small[i] == 0xa7);

    /* Exercise the source-compatible callback wrapper that previously aborted. */
    memset(destination, 0x3c, sizeof destination);
    o00_35A6_0406(destination, TEST_WIDTH);
    check_transfer(destination, 0x3c);
    CHECK(destination[TEST_SPAN] == 0x3c);
    CHECK(destination[TEST_SPAN + 1] == 0x3c);

    printf("PASS: 64 rows, 2 bytes per row, destination stride 14, span 884; "
           "883-byte and legacy 436-byte negative controls rejected\n");
    return 0;
}
