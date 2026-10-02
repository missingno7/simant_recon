#ifndef SIMANT_GAME_STATE_WORLD_H
#define SIMANT_GAME_STATE_WORLD_H

#include <stdint.h>
#include "../simulation/movement.h"

#define SIM_WORLD_WIDTH 128
#define SIM_WORLD_HEIGHT 64
#define SIM_NEST_WIDTH 64
#define SIM_NEST_HEIGHT 64
#define SIM_PHEROMONE_WIDTH 64
#define SIM_PHEROMONE_HEIGHT 32
#define SIM_A_ANT_CAPACITY 1000
#define SIM_B_ANT_CAPACITY 500
#define SIM_R_ANT_CAPACITY 500

/* These arrays retain the original x-major logical indexing, but use native
 * flat addresses. Coordinates and source `int` fields are explicitly 16-bit. */
typedef struct SimAntList {
    uint8_t x[SIM_A_ANT_CAPACITY + 1];
    uint8_t y[SIM_A_ANT_CAPACITY + 1];
    uint8_t mode[SIM_A_ANT_CAPACITY + 1];
    uint8_t type[SIM_A_ANT_CAPACITY + 1];
    uint8_t state[SIM_A_ANT_CAPACITY + 1];
    int16_t count;
} SimAntList;

typedef struct SimSmallAntList {
    uint8_t x[SIM_B_ANT_CAPACITY + 1];
    uint8_t y[SIM_B_ANT_CAPACITY + 1];
    uint8_t mode[SIM_B_ANT_CAPACITY + 1];
    uint8_t type[SIM_B_ANT_CAPACITY + 1];
    uint8_t state[SIM_B_ANT_CAPACITY + 1];
    int16_t count;
} SimSmallAntList;

typedef struct SimWorldDirtyRect {
    int16_t x;
    int16_t y;
    int16_t columns;
    int16_t rows;
    uint8_t valid;
} SimWorldDirtyRect;

typedef struct SimAntLion {
    uint8_t x;
    uint8_t y;
    uint8_t mode;
    uint8_t seconds;
    uint8_t timer;
} SimAntLion;

typedef struct SimGameWorld {
    SimWorldTiles tiles;
    uint8_t exit_b[SIM_NEST_WIDTH][SIM_NEST_HEIGHT];
    uint8_t exit_r[SIM_NEST_WIDTH][SIM_NEST_HEIGHT];
    uint8_t life_a[SIM_WORLD_WIDTH][SIM_WORLD_HEIGHT];
    uint8_t life_b[SIM_NEST_WIDTH][SIM_NEST_HEIGHT];
    uint8_t life_r[SIM_NEST_WIDTH][SIM_NEST_HEIGHT];
    uint8_t pheromone_a[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    uint8_t pheromone_b_nest[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    uint8_t pheromone_b_trail[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    uint8_t pheromone_r_nest[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    uint8_t pheromone_r_trail[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    uint8_t pheromone_aux[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    uint8_t hole_b[SIM_NEST_WIDTH];
    uint8_t hole_r[SIM_NEST_WIDTH];
    uint16_t random_seed_grid[16 * 12];
    uint8_t build_black[12][16];
    union {
        uint8_t build_red[12][16]; /* Source fd_3D57_0164, 192 bytes. */
        struct {
            uint8_t source_red_grid_prefix[2][16];
            /* Source fd_3D57_0184 is the same storage at offset 32. */
            uint8_t lifetime_graph[10][16];
        };
    };
    SimAntList ants_a;
    SimSmallAntList ants_b;
    SimSmallAntList ants_r;
    SimAntLion ant_lions[10];
    int16_t ant_lion_count;
    int16_t initial_ant_lions;
    int16_t ants_eaten_by_lions;
    int16_t sow_x[3];
    int16_t sow_y[3];
    int16_t sow_direction[3];
    int16_t sow_saved_tile[3];
    int16_t pillar_state;
    int16_t pillar_x;
    int16_t pillar_y;
    int16_t pillar_segment;
    int16_t pillar_direction;
    int16_t pillar_map[6];

    /* Raw scenario selector from fd_50F6_0EAC. Keep numeric until the
     * source/UI mapping is established independently. */
    int16_t scenario;
    int16_t map_plane;
    int16_t selected_map_plane;
    int16_t current_ant_plane;
    int16_t me_x;
    int16_t me_y;
    /* SetMyLife and population counting both read/write source global
     * fd_50F6_04C2. Keep the compatibility names as one physical value. */
    union {
        int16_t me_type;
        int16_t player_caste_type;
    };
    int16_t me_direction;
    int16_t me_health;
    int16_t health_warning_threshold; /* fd_50F6_0FBA */
    int16_t colony_health_warning_threshold; /* fd_50F6_0FFE */
    uint8_t health_warning;
    uint8_t health_death;
    int16_t health_force_full; /* fd_3D57_0C16, source word not boolean */
    int16_t player_flags;
    int16_t player_mode;
    int16_t player_needs_init;
    int16_t player_spawn_x;
    int16_t player_spawn_y;
    int16_t player_update_code;
    int16_t map_view_x;
    int16_t map_view_y;
    int16_t nest_preset_x[2];
    int16_t nest_preset_y[2];
    int16_t requested_preset_x;
    int16_t requested_preset_y;
    int16_t map_focus[3][2];
    int16_t black_nest_size;
    int16_t red_nest_size;
    int16_t yard_mode;
    int16_t world_kind;
    int16_t map_width;
    int16_t current_ground_tile_id;
    int16_t drop_direction;
    int16_t overlay_type;
    int16_t overlay_id;
    int16_t overlay_resource_set;
    int16_t overlay_width;
    int16_t difficulty;
    int16_t simulation_speed_index; /* fd_3D57_07CC */
    int16_t tick_count_delays[4]; /* fd_3D57_07CE[0..3] */
    int16_t current_experiment_tool;
    int16_t experience_flags[2];
    int16_t world_state_flag;
    int16_t cycle;
    int16_t food_black;
    int16_t food_red;
    int16_t food_added_terrain; /* fd_50F6_1040: accepted surface-food tiles */
    int16_t health_black;
    int16_t health_red;
    uint32_t source_state_0214; /* fd_50F6_0214 */
    uint32_t source_state_0204; /* fd_50F6_0204 */
    int16_t source_state_0228; /* fd_50F6_0228 */
    int16_t source_state_0478; /* fd_50F6_0478 */
    int16_t source_state_0504; /* fd_50F6_0504 */
    int16_t source_state_0c44; /* fd_3D57_0C44 */
    int16_t source_state_0c18; /* fd_3D57_0C18 */
    int16_t source_state_0c14; /* fd_3D57_0C14 */
    int16_t source_state_049a; /* fd_50F6_049A */
    int16_t source_state_0c22; /* fd_3D57_0C22 */
    int16_t source_state_104e; /* fd_50F6_104E */
    int16_t source_state_07be; /* fd_3D57_07BE */
    int16_t source_state_04c4; /* fd_50F6_04C4 */
    int16_t queen_black_x;
    int16_t queen_black_y;
    int16_t queen_red_x;
    int16_t queen_red_y;
    int16_t queens_black;
    int16_t queens_red;
    int16_t ants_by_type[32];
    int16_t population_black[6];
    int16_t population_red[6];
    int16_t player_death_plane; /* fd_50F6_04E2 */
    int16_t population_new_game; /* fd_50F6_0354 */
    int16_t population_lifetime_graph_enabled; /* fd_50F6_0400 */
    int16_t population_selection_pending; /* fd_50F6_0376 */
    int16_t population_selection_colony; /* fd_50F6_0366 */
    int16_t lifetime_graph_preset[2]; /* fd_50F6_07CA[0..1] */
    int16_t total_population_black;
    int16_t total_population_red;
    int16_t source_counter_0242; /* fd_50F6_0242 */
    uint32_t source_counter_0472; /* fd_50F6_0472 */
    int16_t source_counter_09fa; /* fd_50F6_09FA */
    int16_t source_counter_0a00; /* fd_50F6_0A00 */
    int16_t player_selection_plane;
    int16_t player_selection_x;
    int16_t player_selection_y;
    int16_t food_center_x;
    int16_t food_center_y;
    uint32_t world_ticks;
    SimWorldDirtyRect dirty_map;
} SimGameWorld;

/* The original ClrArrays clears these fields and deliberately leaves ant
 * coordinates and list counts alone. */
void sim_world_clear_arrays(SimGameWorld *world);
void sim_world_init_sim_vars(SimGameWorld *world);

#endif
