#ifndef SIMANT_GAME_SIMULATION_RNG_H
#define SIMANT_GAME_SIMULATION_RNG_H

#include <stdint.h>

typedef struct SimRng {
    uint16_t s_state;
    uint32_t c_state;
} SimRng;

/* The source exposes a private 16-bit LFSR and the MSC C runtime rand stream.
 * Tick values are injected at the old BIOS boundary; no host clock is read. */
void sim_rng_set_s_seed(SimRng *rng, int16_t seed);
void sim_rng_seed_s_from_tick(SimRng *rng, uint32_t tick);
/* Program-startup boundary for the original SeedRRand sequence. The game
 * does not reseed these streams on each NewGame/RandYard call. */
void sim_rng_seed_startup(SimRng *rng, uint32_t lfsr_tick,
                          uint32_t c_runtime_tick);
/* Retained compatibility spelling; identical to sim_rng_seed_startup. */
void sim_rng_seed_r(SimRng *rng, uint32_t lfsr_tick, uint32_t c_runtime_tick);
uint16_t sim_rng_get_s_seed(const SimRng *rng);
uint32_t sim_rng_get_c_seed(const SimRng *rng);

int sim_rng_s1(SimRng *rng, uint16_t range, uint16_t *value);
uint16_t sim_rng_s2(SimRng *rng);
uint16_t sim_rng_s4(SimRng *rng);
uint16_t sim_rng_s8(SimRng *rng);
uint16_t sim_rng_s16(SimRng *rng);
uint16_t sim_rng_s32(SimRng *rng);
uint16_t sim_rng_s64(SimRng *rng);
uint16_t sim_rng_s128(SimRng *rng);
uint16_t sim_rng_s256(SimRng *rng);
int sim_rng_sg_i(SimRng *rng, uint16_t range, int16_t *value);
int sim_rng_sg(SimRng *rng, uint16_t range, int16_t *value);
int sim_rng_sg_signed(SimRng *rng, int16_t range, int16_t *value);

/* Mirrors MSC rand() (15-bit result) and the game's abs(value) % limit. A
 * nonpositive limit is reported as invalid instead of invoking C UB. */
uint16_t sim_rng_msc_rand(SimRng *rng);
int sim_rng_r(SimRng *rng, int16_t limit, int16_t *value);

#endif
