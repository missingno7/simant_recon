#include "recovered_state.h"


#include "portable/game/simulation/rng.h"
#include <stdlib.h>

static _Thread_local SimRng *recovered_active_rng;
void recovered_rng_bind(SimRng *rng) { recovered_active_rng = rng; }
static SimRng *recovered_rng_require(void)
{
    if (recovered_active_rng == NULL) abort();
    return recovered_active_rng;
}

int16_t SRand1(uint16_t range)
{
    uint16_t value;
    if (sim_rng_s1(recovered_rng_require(), range, &value) == 0) abort();
    return (int16_t)value;
}
int16_t SRand2(void) { return (int16_t)sim_rng_s2(recovered_rng_require()); }
int16_t SRand4(void) { return (int16_t)sim_rng_s4(recovered_rng_require()); }
int16_t SRand8(void) { return (int16_t)sim_rng_s8(recovered_rng_require()); }
int16_t SRand16(void) { return (int16_t)sim_rng_s16(recovered_rng_require()); }
int16_t SRand32(void) { return (int16_t)sim_rng_s32(recovered_rng_require()); }
int16_t SRand64(void) { return (int16_t)sim_rng_s64(recovered_rng_require()); }
int16_t SRand128(void) { return (int16_t)sim_rng_s128(recovered_rng_require()); }
int16_t SRand256(void) { return (int16_t)sim_rng_s256(recovered_rng_require()); }
int16_t RRand(int16_t limit)
{
    int16_t value;
    if (sim_rng_r(recovered_rng_require(), limit, &value) == 0) abort();
    return value;
}
int16_t SGIRand(int16_t range)
{
    int16_t value;
    if (sim_rng_sg_i(recovered_rng_require(), (uint16_t)range, &value) == 0) abort();
    return value;
}
int16_t SGRand(int16_t range)
{
    int16_t value;
    if (sim_rng_sg(recovered_rng_require(), (uint16_t)range, &value) == 0) abort();
    return value;
}
int16_t SGSRand(int16_t range)
{
    int16_t value;
    if (sim_rng_sg_signed(recovered_rng_require(), range, &value) == 0) abort();
    return value;
}


#include "portable/game/simulation/movement.h"
#include <string.h>

int16_t o25_3BA4_1686(int16_t *rot, int16_t *dir, int16_t plane,
                     int16_t x, int16_t y, int16_t a, int16_t b)
{
    SimWorldTiles tiles;
    SimMoveContext context;
    SimRandDirBias bias;
    int16_t result;
    memcpy(tiles.surface, MapA, sizeof(tiles.surface));
    memcpy(tiles.nest_b, MapB, sizeof(tiles.nest_b));
    memcpy(tiles.nest_r, MapR, sizeof(tiles.nest_r));
    tiles.terrain_set = TERRAINset;
    context.mode = fd_50F6_0A8E == 2 ? 2 : 0;
    context.from_plane = fd_50F6_0AF8;
    context.from.x = fd_50F6_0AD6;
    context.from.y = fd_50F6_0AE8;
    context.previous.x = fd_50F6_0AB6;
    context.previous.y = fd_50F6_0AC6;
    bias.rot = *rot;
    bias.direction = *dir;
    result = sim_get_my_rand_dirs(&tiles, &context, plane,
                                  (SimGridPos){x, y}, (SimGridPos){a, b},
                                  &bias, NULL);
    *rot = bias.rot;
    *dir = bias.direction;
    return result;
}
