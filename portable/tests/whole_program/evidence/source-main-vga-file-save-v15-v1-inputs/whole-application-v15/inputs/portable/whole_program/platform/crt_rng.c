#include "crt_rng.h"
#include "portable/game/simulation/rng.h"

/* One runtime owner for every mechanically converted TU. Algorithm and DOS
 * evidence are preserved in game/simulation/rng.c and tests/rng/. The source
 * root:0093 TU retains its separate private SRand word; this never mirrors it. */
static SimRng runtime_rng = { 0, 1 };

void dos_crt_srand(uint16_t seed)
{
    runtime_rng.c_state = seed;
}

int16_t dos_crt_rand(void)
{
    return (int16_t)sim_rng_msc_rand(&runtime_rng);
}

uint32_t dos_crt_rng_state(void)
{
    return runtime_rng.c_state;
}

void dos_crt_rng_restore(uint32_t state)
{
    runtime_rng.c_state = state;
}
