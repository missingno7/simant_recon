#include "portable/whole_program/platform/crt_rng.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void SeedRRand(void);
int16_t RRand(int16_t limit);
void SetSRandSeed(int16_t seed);
uint32_t GetSRandSeed(void);
static uint32_t ticks[2];
static unsigned tick_index;

/* Link-only boundaries for functions outside this suite. Reaching either
 * aborts the run; these never manufacture DOS physical-memory data/results. */
uint32_t dos_host_read_u32(uint32_t address)
{
    (void)address;
    abort();
}
_Noreturn void dos_host_divide_fault(void)
{
    abort();
}

uint32_t TickCount(void)
{
    if (tick_index >= 2) abort();
    return ticks[tick_index++];
}

static uint32_t advance(uint32_t state)
{
    return state * UINT32_C(214013) + UINT32_C(2531011);
}

static void require(int condition)
{
    if (!condition) abort();
}

int main(void)
{
    uint32_t i, expected, restored;
    require(dos_crt_rng_state() == 1); /* MSC runtime startup state. */
    for (i = 0; i < 8192; ++i) {
        uint16_t seed = (uint16_t)(i * 40503u);
        int16_t limit = (int16_t)(1u + i % 32767u);
        SetSRandSeed((int16_t)seed);
        dos_crt_srand(seed);
        expected = advance(seed);
        require((uint16_t)dos_crt_rand() == ((expected >> 16) & 0x7fffu));
        expected = advance(expected);
        require(RRand(limit) == (int16_t)(((expected >> 16) & 0x7fffu) % (uint16_t)limit));
        require(dos_crt_rng_state() == expected);
        require(GetSRandSeed() == seed); /* source/private state remains separate. */
        restored = dos_crt_rng_state();
        (void)dos_crt_rand();
        dos_crt_rng_restore(restored);
        require(dos_crt_rng_state() == expected);
    }
    ticks[0] = UINT32_C(0x12345678);
    ticks[1] = UINT32_C(0x89abcdef);
    tick_index = 0;
    SeedRRand();
    require(tick_index == 2);
    {
        uint16_t s = (uint16_t)ticks[0] ^ 0x3751u;
        uint16_t shifted = (uint16_t)(s << 1);
        unsigned count, j;
        if (s & 0x8000u) shifted ^= 0x1bf5u;
        require(GetSRandSeed() == shifted);
        count = shifted & 127u;
        expected = (uint16_t)ticks[1];
        for (j = 0; j < count; ++j) expected = advance(expected);
        require(dos_crt_rng_state() == expected);
    }
    puts("PASS: 8192 interleaved source/runtime streams, private seed isolation, restore, ordered startup warmup");
    return 0;
}
