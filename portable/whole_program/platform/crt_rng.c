#include "crt_rng.h"

/* MSC runtime recurrence; root:0093 retains its canonical private SRand word. */
static uint32_t runtime_rng_state = 1;

void dos_crt_srand(uint16_t seed)
{
    runtime_rng_state = seed;
}

int16_t dos_crt_rand(void)
{
    runtime_rng_state = runtime_rng_state * UINT32_C(214013) + UINT32_C(2531011);
    return (int16_t)((runtime_rng_state >> 16) & UINT32_C(0x7fff));
}

uint32_t dos_crt_rng_state(void)
{
    return runtime_rng_state;
}

void dos_crt_rng_restore(uint32_t state)
{
    runtime_rng_state = state;
}
