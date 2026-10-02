#include <stdint.h>
#include <string.h>

#include "../../game/simulation/spider.h"

int16_t spider_test_scan(int16_t direction, int16_t x16, int16_t y16,
                         uint16_t seed, int16_t ant_count, uint8_t terrain_set,
                         const uint8_t *life_a, const uint8_t *map_a,
                         const uint8_t *ant_x, const uint8_t *ant_y,
                         const uint8_t *ant_type, const uint8_t *corpse_x,
                         const uint8_t *corpse_y, int16_t corpse_base, int16_t corpse_index,
                         uint8_t *out_life_a,
                         uint8_t *out_map_a, uint8_t *out_ant_type,
                         uint8_t *out_corpse_x, uint8_t *out_corpse_y,
                         int16_t *out_corpse_base, int16_t *out_corpse_index, uint16_t *out_seed,
                         int16_t *out_laser)
{
    SimGameWorld world;
    SimSpiderState spider;
    SimRng rng = {seed, 0};
    SimSpiderLaser laser;
    int16_t result;
    int i;

    memset(&world, 0, sizeof(world));
    memset(&spider, 0, sizeof(spider));
    memcpy(world.life_a, life_a, sizeof(world.life_a));
    memcpy(world.tiles.surface, map_a, sizeof(world.tiles.surface));
    memcpy(world.ants_a.x, ant_x, SIM_A_ANT_CAPACITY);
    memcpy(world.ants_a.y, ant_y, SIM_A_ANT_CAPACITY);
    memcpy(world.ants_a.type, ant_type, SIM_A_ANT_CAPACITY);
    world.ants_a.count = ant_count;
    world.tiles.terrain_set = terrain_set;
    sim_spider_init(&spider, &world);
    spider.direction = direction;
    spider.x16 = x16;
    spider.y16 = y16;
    spider.corpse_base = corpse_base;
    spider.corpse_index = corpse_index;
    memcpy(spider.corpse_x, corpse_x, sizeof(spider.corpse_x));
    memcpy(spider.corpse_y, corpse_y, sizeof(spider.corpse_y));
    result = sim_spider_scan(&spider, &world, &rng, &laser);
    memcpy(out_life_a, world.life_a, sizeof(world.life_a));
    memcpy(out_map_a, world.tiles.surface, sizeof(world.tiles.surface));
    memcpy(out_ant_type, world.ants_a.type, SIM_A_ANT_CAPACITY);
    memcpy(out_corpse_x, spider.corpse_x, sizeof(spider.corpse_x));
    memcpy(out_corpse_y, spider.corpse_y, sizeof(spider.corpse_y));
    *out_corpse_base = spider.corpse_base;
    *out_corpse_index = spider.corpse_index;
    *out_seed = rng.s_state;
    out_laser[0] = laser.from_x16;
    out_laser[1] = laser.from_y16;
    out_laser[2] = laser.to_x16;
    out_laser[3] = laser.to_y16;
    out_laser[4] = laser.fired;
    for (i = 5; i < 8; ++i)
        out_laser[i] = 0;
    return result;
}
