#ifndef SIMANT_WHOLE_CRT_RNG_H
#define SIMANT_WHOLE_CRT_RNG_H
#include <stdint.h>
void dos_crt_srand(uint16_t seed);
int16_t dos_crt_rand(void);
/* Checkpoint access to this runtime's state, separate from source SRand seed. */
uint32_t dos_crt_rng_state(void);
void dos_crt_rng_restore(uint32_t state);
#endif
