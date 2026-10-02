#include "../../game/render/map.h"

#include <string.h>

typedef struct MapProbeInput {
    SimMapView view;
    int16_t column;
    int16_t row;
    uint8_t ground_tile;
    uint8_t life;
    uint8_t pheromone_value;
    uint8_t reserved;
} MapProbeInput;

typedef struct MapProbeOutput {
    int16_t status;
    SimMapDrawCommand command;
} MapProbeOutput;

void sim_map_probe(const MapProbeInput *input, MapProbeOutput *output)
{
    SimGameWorld world;
    int16_t x, y;

    memset(&world, 0, sizeof world);
    memset(output, 0, sizeof *output);
    if (input == 0 || output == 0)
        return;
    x = input->view.camera_x + input->column;
    y = input->view.camera_y + input->row;
    if (y > 0x3f) {
        x += 0x40;
        y &= 0x3f;
    }
    if (input->view.plane <= 1) {
        x &= 0x7f;
        world.tiles.surface[x][y] = input->ground_tile;
        world.life_a[x][y] = input->life;
        if (input->view.pheromone_mode == 0)
            world.pheromone_a[x >> 1][y >> 1] = input->pheromone_value;
        else if (input->view.pheromone_mode == 1)
            world.pheromone_b_nest[x >> 1][y >> 1] = input->pheromone_value;
        else if (input->view.pheromone_mode == 2)
            world.pheromone_b_trail[x >> 1][y >> 1] = input->pheromone_value;
        else if (input->view.pheromone_mode == 3)
            world.pheromone_r_nest[x >> 1][y >> 1] = input->pheromone_value;
        else if (input->view.pheromone_mode == 4)
            world.pheromone_r_trail[x >> 1][y >> 1] = input->pheromone_value;
    } else {
        x &= 0x3f;
        if (input->view.plane == 2) {
            world.tiles.nest_b[x][y] = (uint8_t)(input->ground_tile + 0x70);
            world.life_b[x][y] = input->life;
        } else {
            world.tiles.nest_r[x][y] = (uint8_t)(input->ground_tile + 0x70);
            world.life_r[x][y] = input->life;
        }
    }
    output->status = (int16_t)sim_map_select_cell(&world, &input->view,
                                                  input->column, input->row,
                                                  &output->command);
}
