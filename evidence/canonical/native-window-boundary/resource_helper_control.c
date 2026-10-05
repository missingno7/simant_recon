#include "window_parameters.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    SimWindowRefRegistry registry;
    FILE *input;
    char *wire;
    size_t extent;
    int rid, count;
    unsigned axis;
    unsigned char before[8];
    if (argc != 6) return 1;
    input = fopen(argv[1], "rb");
    extent = (size_t)strtoul(argv[3], NULL, 10);
    rid = atoi(argv[4]); count = atoi(argv[5]);
    wire = malloc(extent);
    if (!input || !wire || fseek(input, atol(argv[2]), SEEK_SET) ||
        fread(wire, 1, extent, input) != extent) return 2;
    fclose(input);
    sim_window_ref_registry_init(&registry);
    if (sim_window_ref_registry_attach(&registry, (uint16_t)rid, &wire,
                                     extent) != SIM_WINDOW_REFS_OK) return 3;
    memcpy(before, wire + 0x10, 8);
    if (count && sim_window_parameters_store_open(&registry,
            (int16_t)(rid << 8), wire, 0, 100, 200, 300, 400) !=
            SIM_WINDOW_PARAMETERS_MISSING_SOURCE_PARAMETER) return 4;
    if (count && memcmp(before, wire + 0x10, 8)) return 5;
    if (sim_window_parameters_store_open(&registry, (int16_t)(rid << 8),
            wire, 1, 100, 200, 300, 400) !=
            SIM_WINDOW_PARAMETERS_BAD_SUPPLIED_COUNT) return 6;
    if (memcmp(before, wire + 0x10, 8)) return 7;
    if (sim_window_parameters_store_open(&registry, (int16_t)(rid << 8),
            wire, (int16_t)count, 100, 200, 300, 400) !=
            SIM_WINDOW_PARAMETERS_OK) return 8;
    for (axis = 0; axis < 4; ++axis)
        if (sim_window_wire_read_i16(wire, 0x10 + 2 * axis) !=
            (int16_t)(100 * (axis + 1))) return 9;
    sim_window_ref_registry_detach(&registry, (uint16_t)rid);
    free(wire);
    return 0;
}
