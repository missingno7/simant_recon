#include "yard.h"

void sim_yard_init_scene(SimYardScene *scene)
{
    if (scene == 0)
        return;

    scene->boy_message_count = 0;
    scene->boy_x = 0xb4;
    scene->boy_y = 0x49;
    scene->boy_turn_count = 0x0c;
    scene->boy_wait = 0x14;
    scene->bird_delay = 0;
    scene->cat_delay = 0;
    scene->dog_x = 0xfa;
    scene->dog_y = 0x96;
    scene->boy_direction = 2;
    scene->dog_turn_count = 2;
    scene->boy_message_on = 0;
    scene->boy_pixel_x = 0;
    scene->boy_pixel_y = 0;
    scene->boy_frame = 0;
    scene->boy_here = 0;
    scene->boy_stand_count = 0;
    scene->node_count = 0;
    scene->node_number = 0;
    scene->bird_on = 0;
    scene->cat_cycle = 0;
    scene->cat_frame = 0;
    scene->cat_on = 0;
    scene->dog_frame = 0;
    scene->dog_direction = 0;
    scene->foot_here = 0;
    scene->foot_toggle = 0;
    scene->foot_x = 0;
    scene->foot_y = 0;
    scene->mower_x = 0;
    scene->mower_y = 0;
    scene->boy_is_mowing = 0;
    scene->rain_on = 0;
    scene->swarm_delay_black = 0;
    scene->swarm_delay_red = 0;
    scene->bird_frame = 1;
    scene->last_colony_pop_black = 1;
    scene->last_colony_pop_red = 1;
    scene->boy_message_offset = -1;
    scene->yard_cycle = -1;
}
