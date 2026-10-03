#include "portable/game/simulation/rng.h"

#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void SetSRandSeed(int16_t value);
uint32_t GetSRandSeed(void);
void SeedSRand(void);
void SeedRRand(void);
uint32_t GetRRandSeed(void);
int16_t SRand1(uint16_t range);
int16_t SRand2(void);
int16_t SRand4(void);
int16_t SRand8(void);
int16_t SRand16(void);
int16_t SRand32(void);
int16_t SRand64(void);
int16_t SRand128(void);
int16_t SRand256(void);
int16_t RRand(int16_t limit);

static SimRng runtime_rng;
static uint32_t ticks[2];
static unsigned tick_at;
static uint32_t read_physical;
static unsigned read_count, fault_count;
static uint32_t fault_dividend;
static uint16_t fault_divisor;
static jmp_buf fault_target;
static volatile int fault_armed;
static unsigned rrand_cases;

uint32_t TickCount(void)
{
    return ticks[tick_at < 2 ? tick_at++ : 1];
}

void dos_crt_srand(uint16_t seed_value)
{
    runtime_rng.c_state = seed_value;
}

int16_t dos_crt_rand(void)
{
    return (int16_t)sim_rng_msc_rand(&runtime_rng);
}

uint32_t dos_host_read_u32(uint32_t physical_address)
{
    ++read_count;
    read_physical = physical_address;
    return UINT32_C(0x89abcdef);
}

_Noreturn void dos_host_divide_fault(void)
{
    ++fault_count;
    fault_dividend = GetSRandSeed();
    fault_divisor = 0;
    if (fault_armed)
        longjmp(fault_target, 1);
    abort();
}

static uint16_t next_seed(uint16_t seed)
{
    uint16_t ax = (uint16_t)(seed << 1);
    if ((seed & UINT16_C(0x8000)) != 0)
        ax ^= UINT16_C(0x1bf5);
    return ax;
}

static void require(int ok, const char *message)
{
    if (!ok) {
        fprintf(stderr, "RNG conversion probe failed: %s\n", message);
        exit(1);
    }
}

int main(void)
{
    static const uint16_t masks[8] = {1,3,7,15,31,63,127,255};
    int16_t (*mask_functions[8])(void) = {
        SRand2,SRand4,SRand8,SRand16,SRand32,SRand64,SRand128,SRand256
    };
    static const uint16_t ranges[7] = {1,3,7,8,255,32767,65535};
    unsigned seed, mask;
    SimRng expected;
    uint16_t value;

    for (seed = 0; seed < 65536u; ++seed) {
        uint16_t next = next_seed((uint16_t)seed);
        for (mask = 0; mask < 8u; ++mask) {
            SetSRandSeed((int16_t)(uint16_t)seed);
            require((uint16_t)mask_functions[mask]() == (uint16_t)(next & masks[mask]),
                    "mask return AX bits");
            require((uint16_t)GetSRandSeed() == next, "mask private seed advance");
        }
        for (mask = 0; mask < 7u; ++mask) {
            SimRng oracle = {(uint16_t)seed,0};
            SetSRandSeed((int16_t)(uint16_t)seed);
            require(sim_rng_s1(&oracle,ranges[mask],&value), "native bounded RNG control valid");
            require((uint16_t)SRand1(ranges[mask]) == value, "bounded SRand1 remainder");
            require((uint16_t)GetSRandSeed() == oracle.s_state, "bounded SRand1 seed state");
        }
    }

    SetSRandSeed((int16_t)UINT16_C(0xa55a));
    fault_armed = 1;
    if (setjmp(fault_target) == 0) {
        (void)SRand1(0);
        require(0, "zero range must not return");
    }
    fault_armed = 0;
    require(fault_count == 1 && fault_divisor == 0, "zero range reaches explicit nonreturn divisor fault leaf");
    require((uint16_t)GetSRandSeed() == next_seed(UINT16_C(0xa55a)),
            "DIV fault occurs after source seed write");

    for (seed = 0; seed < 65536u; ++seed) {
        int16_t limits[3] = {1,(int16_t)(1u + (seed % 32767u)),32767};
        unsigned j;
        for (j = 0; j < 3u; ++j) {
            int16_t actual;
            runtime_rng.c_state = seed;
            expected.c_state = seed;
            require(sim_rng_r(&expected,limits[j],&actual), "native MSC bounded control valid");
            runtime_rng.c_state = seed;
            require(RRand(limits[j]) == actual, "RRand namespaced runtime provider and signed remainder");
            require(runtime_rng.c_state == expected.c_state, "RRand runtime state advance");
            ++rrand_cases;
        }
    }

    ticks[0] = UINT32_C(0x12345678);ticks[1] = UINT32_C(0x89abcdef);tick_at = 0;
    sim_rng_seed_startup(&expected,ticks[0],ticks[1]);
    SeedRRand();
    require(tick_at == 2, "SeedRRand uses two ordered TickCount calls");
    require((uint16_t)GetSRandSeed() == expected.s_state, "SeedRRand private S stream state");
    require(runtime_rng.c_state == expected.c_state, "SeedRRand MSC runtime state provider");

    read_count = 0;read_physical = 0;
    require(GetRRandSeed() == UINT32_C(0x89abcdef), "GetRRandSeed host leaf returned sentinel");
    require(read_count == 1 && read_physical == UINT32_C(0x46c0),
            "GetRRandSeed passes physical 46C0 for source 046C:0000");

    printf("RNG_CONVERSION_PASS masks=524288 bounded_srand1=458752 rrand=%u zero_fault=1 dos_read=46c0\n",
           rrand_cases);
    return 0;
}
