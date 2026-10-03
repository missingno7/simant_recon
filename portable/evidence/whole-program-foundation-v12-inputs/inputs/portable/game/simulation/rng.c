#include "rng.h"

static uint16_t lfsr_next(SimRng *rng)
{
    uint16_t value = (uint16_t)(rng->s_state << 1);
    if ((rng->s_state & 0x8000u) != 0)
        value ^= 0x1bf5u;
    rng->s_state = value;
    return value;
}

void sim_rng_set_s_seed(SimRng *rng, int16_t seed)
{
    if (rng != 0)
        rng->s_state = (uint16_t)seed;
}

void sim_rng_seed_s_from_tick(SimRng *rng, uint32_t tick)
{
    if (rng != 0)
        rng->s_state = (uint16_t)tick ^ 0x3751u;
}

void sim_rng_seed_startup(SimRng *rng, uint32_t lfsr_tick,
                          uint32_t c_runtime_tick)
{
    uint16_t warmup;
    uint16_t i;

    if (rng == 0)
        return;
    sim_rng_seed_s_from_tick(rng, lfsr_tick);
    warmup = sim_rng_s128(rng);
    rng->c_state = (uint16_t)c_runtime_tick;
    for (i = 0; i < warmup; ++i)
        (void)sim_rng_msc_rand(rng);
}

void sim_rng_seed_r(SimRng *rng, uint32_t lfsr_tick, uint32_t c_runtime_tick)
{
    sim_rng_seed_startup(rng, lfsr_tick, c_runtime_tick);
}

uint16_t sim_rng_get_s_seed(const SimRng *rng)
{
    return rng == 0 ? 0 : rng->s_state;
}

uint32_t sim_rng_get_c_seed(const SimRng *rng)
{
    return rng == 0 ? 0 : rng->c_state;
}

int sim_rng_s1(SimRng *rng, uint16_t range, uint16_t *value)
{
    uint16_t next;
    if (rng == 0 || value == 0 || range == 0)
        return 0;
    next = lfsr_next(rng);
    *value = (uint16_t)(next % range);
    return 1;
}

#define SIM_MASK_DRAW(name, mask) \
    uint16_t name(SimRng *rng) \
    { \
        return rng == 0 ? 0 : (uint16_t)(lfsr_next(rng) & (mask)); \
    }

SIM_MASK_DRAW(sim_rng_s2, 0x0001u)
SIM_MASK_DRAW(sim_rng_s4, 0x0003u)
SIM_MASK_DRAW(sim_rng_s8, 0x0007u)
SIM_MASK_DRAW(sim_rng_s16, 0x000fu)
SIM_MASK_DRAW(sim_rng_s32, 0x001fu)
SIM_MASK_DRAW(sim_rng_s64, 0x003fu)
SIM_MASK_DRAW(sim_rng_s128, 0x007fu)
SIM_MASK_DRAW(sim_rng_s256, 0x00ffu)

int sim_rng_sg_i(SimRng *rng, uint16_t range, int16_t *value)
{
    uint16_t first, second;
    if (value == 0 || !sim_rng_s1(rng, range, &first) ||
        !sim_rng_s1(rng, range, &second))
        return 0;
    *value = (int16_t)(second < first ? first : second);
    return 1;
}

int sim_rng_sg(SimRng *rng, uint16_t range, int16_t *value)
{
    uint16_t first, second;
    if (value == 0 || !sim_rng_s1(rng, range, &first) ||
        !sim_rng_s1(rng, range, &second))
        return 0;
    *value = (int16_t)(second > first ? first : second);
    return 1;
}

int sim_rng_sg_signed(SimRng *rng, int16_t range, int16_t *value)
{
    uint16_t first, second;
    if (value == 0 || range <= 0 ||
        !sim_rng_s1(rng, (uint16_t)range, &first) ||
        !sim_rng_s1(rng, (uint16_t)range, &second))
        return 0;
    if (second > first)
        second = first;
    *value = sim_rng_s2(rng) ? (int16_t)-(int16_t)second : (int16_t)second;
    return 1;
}

uint16_t sim_rng_msc_rand(SimRng *rng)
{
    if (rng == 0)
        return 0;
    rng->c_state = rng->c_state * 214013u + 2531011u;
    return (uint16_t)((rng->c_state >> 16) & 0x7fffu);
}

int sim_rng_r(SimRng *rng, int16_t limit, int16_t *value)
{
    uint16_t draw;
    if (rng == 0 || value == 0 || limit <= 0)
        return 0;
    draw = sim_rng_msc_rand(rng);
    *value = (int16_t)(draw % (uint16_t)limit);
    return 1;
}
