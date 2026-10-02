#include "../../game/simulation/yard.h"

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

static void test_init_scene_assignments(void)
{
    SimYardScene scene;
    memset(&scene, 0xa5, sizeof scene);

    sim_yard_init_scene(&scene);
#define CHECK(field, value) assert(scene.field == (value))
    CHECK(boy_message_count, 0);
    CHECK(boy_x, 0xb4);
    CHECK(boy_y, 0x49);
    CHECK(boy_turn_count, 0x0c);
    CHECK(boy_wait, 0x14);
    CHECK(bird_delay, 0);
    CHECK(cat_delay, 0);
    CHECK(dog_x, 0xfa);
    CHECK(dog_y, 0x96);
    CHECK(boy_direction, 2);
    CHECK(dog_turn_count, 2);
    CHECK(boy_message_on, 0);
    CHECK(boy_pixel_x, 0);
    CHECK(boy_pixel_y, 0);
    CHECK(boy_frame, 0);
    CHECK(boy_here, 0);
    CHECK(boy_stand_count, 0);
    CHECK(node_count, 0);
    CHECK(node_number, 0);
    CHECK(bird_on, 0);
    CHECK(cat_cycle, 0);
    CHECK(cat_frame, 0);
    CHECK(cat_on, 0);
    CHECK(dog_frame, 0);
    CHECK(dog_direction, 0);
    CHECK(foot_here, 0);
    CHECK(foot_toggle, 0);
    CHECK(foot_x, 0);
    CHECK(foot_y, 0);
    CHECK(mower_x, 0);
    CHECK(mower_y, 0);
    CHECK(boy_is_mowing, 0);
    CHECK(rain_on, 0);
    CHECK(swarm_delay_black, 0);
    CHECK(swarm_delay_red, 0);
    CHECK(bird_frame, 1);
    CHECK(last_colony_pop_black, 1);
    CHECK(last_colony_pop_red, 1);
    CHECK(boy_message_offset, -1);
    CHECK(yard_cycle, -1);
#undef CHECK
    sim_yard_init_scene(0);
}

int main(void)
{
    test_init_scene_assignments();
    puts("yard tests passed");
    return 0;
}
