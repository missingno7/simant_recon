#include <stdint.h>
#include <string.h>

#include "../../game/simulation/spider_sim.h"

enum { SPIDER_FIELDS = 17, TICK_VALUES = 3, WORLD_VALUES = 7,
       ARRAY_BYTES = 128 * 64, ANT_BYTES = SIM_A_ANT_CAPACITY,
       RING_BYTES = 100 };

static int16_t route_stub(void *userdata, const SimGameWorld *world,
                          int16_t plane, int16_t x, int16_t y,
                          int16_t target_x, int16_t target_y)
{
    (void)world; (void)plane; (void)x; (void)y; (void)target_x; (void)target_y;
    return *(const int16_t *)userdata;
}

int spider_tick_test(const int16_t *in_spider, const int16_t *in_tick,
                     const int16_t *in_world, const int32_t *in_eaten,
                     const uint8_t *in_options, uint16_t seed,
                     int16_t route_result, int16_t ant_count,
                     const uint8_t *in_life, const uint8_t *in_map,
                     const uint8_t *in_ant_x, const uint8_t *in_ant_y,
                     const uint8_t *in_ant_type, const uint8_t *in_corpse_x,
                     const uint8_t *in_corpse_y, uint8_t *out_life,
                     uint8_t *out_map, uint8_t *out_ant_type,
                     uint8_t *out_corpse_x, uint8_t *out_corpse_y,
                     int16_t *out_spider, int16_t *out_tick,
                     int16_t *out_world, int32_t *out_eaten,
                     uint16_t *out_seed, uint16_t *out_event_count,
                     uint8_t *out_overflow, int16_t *out_status,
                     int16_t *out_events, int16_t *out_corpse_index)
{
    SimGameWorld world;
    SimSpiderState spider;
    SimSpiderTickState tick;
    SimSpiderTickServices services;
    SimSpiderTickEffects effects;
    SimRng rng = {seed, 0};
    SimSpiderTickStatus status;

    memset(&world, 0, sizeof(world));
    memset(&spider, 0, sizeof(spider));
    memset(&tick, 0, sizeof(tick));
    memset(&effects, 0, sizeof(effects));
    world.scenario = in_world[0];
    world.current_ant_plane = in_world[1];
    world.me_x = in_world[2];
    world.me_y = in_world[3];
    world.me_type = in_world[4];
    world.me_direction = in_world[5];
    world.tiles.terrain_set = in_world[6];
    world.ants_a.count = ant_count;
    memcpy(world.life_a, in_life, ARRAY_BYTES);
    memcpy(world.tiles.surface, in_map, ARRAY_BYTES);
    memcpy(world.ants_a.x, in_ant_x, ANT_BYTES);
    memcpy(world.ants_a.y, in_ant_y, ANT_BYTES);
    memcpy(world.ants_a.type, in_ant_type, ANT_BYTES);

    spider.direction = in_spider[0];
    spider.x16 = in_spider[1];
    spider.y16 = in_spider[2];
    spider.burp_count = in_spider[3];
    spider.eat_count = in_spider[4];
    spider.corpse_base = in_spider[5];
    spider.corpse_index = *out_corpse_index;
    spider.cycle = in_spider[6];
    spider.cycle2 = in_spider[7];
    spider.revenge = in_spider[8];
    spider.state_flag = in_spider[9];
    spider.target_mode = in_spider[10];
    spider.mode = in_spider[11];
    spider.aux_mode = in_spider[12];
    spider.target = in_spider[13];
    spider.target_life = in_spider[14];
    spider.user_x = in_spider[15];
    spider.user_y = in_spider[16];
    memcpy(spider.corpse_x, in_corpse_x, RING_BYTES);
    memcpy(spider.corpse_y, in_corpse_y, RING_BYTES);
    spider.sine_q15 = sim_spider_sine_table();

    tick.player_control = in_tick[0];
    tick.route_mode = in_tick[1];
    tick.death_count = in_tick[2];
    tick.red_ants_eaten = in_eaten[0];
    tick.black_ants_eaten = in_eaten[1];
    memcpy(tick.options, in_options, sizeof(tick.options));
    services.route_direction = route_stub;
    services.userdata = &route_result;
    status = sim_spider_tick(&world, &rng, &spider, &tick, &services, &effects);

    memcpy(out_life, world.life_a, ARRAY_BYTES);
    memcpy(out_map, world.tiles.surface, ARRAY_BYTES);
    memcpy(out_ant_type, world.ants_a.type, ANT_BYTES);
    memcpy(out_corpse_x, spider.corpse_x, RING_BYTES);
    memcpy(out_corpse_y, spider.corpse_y, RING_BYTES);
    out_spider[0] = spider.direction;
    out_spider[1] = spider.x16;
    out_spider[2] = spider.y16;
    out_spider[3] = spider.burp_count;
    out_spider[4] = spider.eat_count;
    out_spider[5] = spider.corpse_base;
    out_spider[6] = spider.cycle;
    out_spider[7] = spider.cycle2;
    out_spider[8] = spider.revenge;
    out_spider[9] = spider.state_flag;
    out_spider[10] = spider.target_mode;
    out_spider[11] = spider.mode;
    out_spider[12] = spider.aux_mode;
    out_spider[13] = spider.target;
    out_spider[14] = spider.target_life;
    out_spider[15] = spider.user_x;
    out_spider[16] = spider.user_y;
    out_tick[0] = tick.player_control;
    out_tick[1] = tick.route_mode;
    out_tick[2] = tick.death_count;
    out_world[0] = world.scenario;
    out_world[1] = world.current_ant_plane;
    out_world[2] = world.me_x;
    out_world[3] = world.me_y;
    out_world[4] = world.me_type;
    out_world[5] = world.me_direction;
    out_world[6] = world.tiles.terrain_set;
    out_eaten[0] = tick.red_ants_eaten;
    out_eaten[1] = tick.black_ants_eaten;
    *out_seed = rng.s_state;
    *out_event_count = effects.count;
    *out_overflow = effects.overflow;
    *out_status = (int16_t)status;
    *out_corpse_index = spider.corpse_index;
    {
        unsigned i, j;
        for (i = 0; i < SIM_SPIDER_EVENT_CAPACITY; ++i) {
            out_events[i * 6] = i < effects.count ? (int16_t)effects.events[i].kind : 0;
            for (j = 0; j < 5; ++j)
                out_events[i * 6 + 1 + j] = i < effects.count
                    ? effects.events[i].values[j] : 0;
        }
    }
    return 0;
}
