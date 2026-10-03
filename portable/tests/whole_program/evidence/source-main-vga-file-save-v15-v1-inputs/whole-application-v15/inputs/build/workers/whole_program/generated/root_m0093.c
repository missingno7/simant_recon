#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
#include <stdint.h>

extern uint32_t dos_host_read_u32(uint32_t physical_address);
_Noreturn void dos_host_divide_fault(void);
extern void dos_crt_srand(uint16_t seed_value);
extern int16_t dos_crt_rand(void);

/*
 * Random numbers (root module, code frame 0093; linear 0x932-0xBA1).
 * Profile: MSC 6.00 /AL /Os /Oe.  /Oe (global register allocation) is required:
 * plain autos land in SI/DI while their unused BP homes remain, which is the
 * frame shape of SGSRand, SeedRRand and RRand.
 *
 * Same translation unit as the Win16 build's SetSRandSeed..SRand256 group
 * (simantw_recon unit simone_1506): an LFSR "S" generator with feedback
 * 0x1BF5 whose state is this module's private seed, and an "R" generator on
 * the C runtime rand().  The DOS module additionally holds three two-draw
 * helpers and a BIOS tick reader.  SRand1..SRand256 are inline assembly in
 * the original (dead "mov dx, 0" and flag-based branch no C form produces).
 */

extern uint32_t  TickCount(void);
extern void dos_crt_srand(uint16_t seed);
extern int16_t dos_crt_rand(void);

int16_t  SRand1(uint16_t range);
int16_t  SRand2(void);
int16_t  SRand128(void);

static uint16_t seed;

static uint16_t rng_advance_seed(void)
{
    uint16_t ax = seed;
    uint16_t carry = (uint16_t)(ax & UINT16_C(0x8000));
    ax = (uint16_t)(ax << 1);
    if (carry != 0)
        ax ^= UINT16_C(0x1bf5);
    seed = ax;
    return ax;
}


int16_t  SGIRand(int16_t range)
{
    int16_t first;
    int16_t second;

    first = SRand1(range);
    second = SRand1(range);
    if (second < first)
        return first;
    return second;
}

int16_t  SGRand(int16_t range)
{
    int16_t first;
    int16_t second;

    first = SRand1(range);
    second = SRand1(range);
    if (second > first)
        return first;
    return second;
}

int16_t  SGSRand(int16_t range)
{
    int16_t first;
    int16_t second;

    first = SRand1(range);
    second = SRand1(range);
    if (second > first)
        second = first;
    if (SRand2())
        second = -second;
    return second;
}

void  SetSRandSeed(int16_t value)
{
    seed = value;
}

uint32_t  GetSRandSeed(void)
{
    return seed;
}

void  SetRRandSeed(void)
{
}

uint32_t GetRRandSeed(void)
{
    return dos_host_read_u32(UINT32_C(0x46c0));
}

void  SeedSRand(void)
{
    seed = (uint16_t)TickCount() ^ 0x3751;
}

void  SeedRRand(void)
{
    int16_t count;
    int16_t i;

    SeedSRand();
    count = SRand128();
    dos_crt_srand((uint16_t)TickCount());
    for (i = 0; i < count; i++)
        dos_crt_rand();
}

int16_t  RRand(int16_t limit)
{
    int16_t value;

    value = dos_crt_rand();
    if (value < 0)
        value = -value;
    return value % limit;
}

int16_t SRand1(uint16_t range)
{
    uint16_t ax = rng_advance_seed();
    if (range == 0)
        dos_host_divide_fault();
    return (int16_t)(ax % range);
}

int16_t SRand2(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x0001));
}

int16_t SRand4(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x0003));
}

int16_t SRand8(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x0007));
}

int16_t SRand16(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x000f));
}

int16_t SRand32(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x001f));
}

int16_t SRand64(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x003f));
}

int16_t SRand128(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x007f));
}

int16_t SRand256(void)
{
    uint16_t ax = rng_advance_seed();
    return (int16_t)(ax & UINT16_C(0x00ff));
}
#pragma pack(pop)
