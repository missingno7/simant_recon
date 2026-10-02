#ifndef SIMANT_GAME_SIMULATION_YARD_H
#define SIMANT_GAME_SIMULATION_YARD_H

#include <stdint.h>

/* Persistent fields explicitly written by S06 InitSimYard (DOS alias
 * o06_35F5_0000). This is not a blanket zeroed scene: every member maps to a
 * source global, and fields not assigned by InitSimYard do not belong here. */
typedef struct SimYardScene {
    int32_t boy_message_count; /* fd_50F6_109C */
    int16_t boy_x;             /* fd_3D57_0C2C */
    int16_t boy_y;             /* fd_3D57_0C2E */
    int16_t boy_turn_count;    /* fd_3D57_0C34 */
    int16_t boy_wait;          /* fd_3D57_0C2A */
    int32_t bird_delay;        /* fd_50F6_107E */
    int32_t cat_delay;         /* fd_50F6_0220 */
    int16_t dog_x;             /* fd_50F6_04BE */
    int16_t dog_y;             /* fd_50F6_04C6 */
    int16_t boy_direction;     /* fd_3D57_0C30 */
    int16_t dog_turn_count;    /* fd_50F6_0624 */
    int16_t boy_message_on;    /* fd_50F6_10B0 */
    int16_t boy_pixel_x;       /* fd_50F6_0246 */
    int16_t boy_pixel_y;       /* fd_50F6_023E */
    int16_t boy_frame;         /* fd_3D57_0C32 */
    int16_t boy_here;          /* fd_3D57_0C28 */
    int16_t boy_stand_count;   /* fd_3D57_0C40 */
    int16_t node_count;        /* fd_3D57_0C46 */
    int16_t node_number;       /* fd_3D57_0C48 */
    int16_t bird_on;           /* fd_50F6_10A0 */
    int16_t cat_cycle;         /* fd_50F6_022C */
    int16_t cat_frame;         /* fd_50F6_0244 */
    int16_t cat_on;            /* fd_50F6_0254 */
    int16_t dog_frame;         /* fd_50F6_04E4 */
    int16_t dog_direction;     /* fd_50F6_0506 */
    int16_t foot_here;         /* fd_3D57_0C3E */
    int16_t foot_toggle;       /* fd_3D57_0C42 */
    int16_t foot_x;            /* fd_50F6_03E0 */
    int16_t foot_y;            /* fd_50F6_046A */
    int16_t mower_x;           /* fd_50F6_0470 */
    int16_t mower_y;           /* fd_50F6_047A */
    int16_t boy_is_mowing;     /* fd_50F6_0202 */
    int16_t rain_on;           /* fd_50F6_0352 */
    int16_t swarm_delay_black; /* fd_50F6_105C */
    int16_t swarm_delay_red;   /* fd_50F6_1066 */
    int16_t bird_frame;        /* fd_50F6_108C */
    int16_t last_colony_pop_black; /* fd_50F6_0364 */
    int16_t last_colony_pop_red;   /* fd_50F6_036E */
    int16_t boy_message_offset;    /* fd_50F6_10BC */
    int16_t yard_cycle;            /* fd_50F6_07C2 */
} SimYardScene;

/* Exact scalar assignments from InitSimYard. It requests no assets and makes
 * no host calls; later drawing code owns the yard's animation resources. */
void sim_yard_init_scene(SimYardScene *scene);

#endif
