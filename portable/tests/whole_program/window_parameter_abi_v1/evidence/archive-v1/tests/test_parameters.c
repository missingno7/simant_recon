#include "../../../whole_program/window_parameters.h"
#include <stdio.h>
#include <string.h>

static int failures;
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "check failed: %s:%d: %s\n", __FILE__, __LINE__, #x); ++failures; } } while (0)

static void put16(uint8_t *p, size_t at, uint16_t v)
{
    p[at] = (uint8_t)v;
    p[at + 1] = (uint8_t)(v >> 8);
}

static void setup(SimWindowRefRegistry *registry, uint8_t *wire, char **handle,
                  uint16_t count)
{
    memset(wire, 0, 0x80);
    *handle = (char *)wire;
    put16(wire, 0x0c, count);
    if (count != 0) {
        size_t i;
        for (i = 0; i < count; ++i) {
            size_t object = 0x30u + i * 0x28u;
            put16(wire, 0x2c + i * 4u, (uint16_t)object);
            put16(wire, object + 0x22, 0x28);
        }
    }
    sim_window_ref_registry_init(registry);
    CHECK(sim_window_ref_registry_attach(registry, 16, handle, 0x80) == SIM_WINDOW_REFS_OK);
}

static void test_no_optional_parameters(void)
{
    SimWindowRefRegistry registry;
    uint8_t wire[0x80];
    char *handle;
    setup(&registry, wire, &handle, 1);
    CHECK(sim_window_parameters_store_open(&registry, 0x1000, handle, 0,
                                           0, 0, 0, 0) == SIM_WINDOW_PARAMETERS_OK);
    CHECK(sim_window_wire_read_i16(wire, 0x10) == 0);
    CHECK(sim_window_wire_read_i16(wire, 0x12) == 0);
    CHECK(sim_window_wire_read_i16(wire, 0x14) == 0);
    CHECK(sim_window_wire_read_i16(wire, 0x16) == 0);
    sim_window_ref_registry_detach(&registry, 16);
}

static void test_two_parameters(void)
{
    SimWindowRefRegistry registry;
    uint8_t wire[0x80];
    char *handle;
    uint8_t *object;
    setup(&registry, wire, &handle, 1);
    object = wire + 0x30;
    sim_window_wire_write_i16(object, 0x18, 5);
    sim_window_wire_write_i16(object, 0x1a, 5);
    sim_window_wire_write_i16(object, 0x10, 0);
    sim_window_wire_write_i16(object, 0x12, 1);
    CHECK(sim_window_parameters_store_open(&registry, 0x1000, handle, 2,
                                           -8, 17, 0, 0) == SIM_WINDOW_PARAMETERS_OK);
    CHECK(sim_window_wire_read_i16(wire, 0x10) == -8);
    CHECK(sim_window_wire_read_i16(wire, 0x12) == 17);
    CHECK(sim_window_wire_read_i16(wire, 0x14) == 0);
    CHECK(sim_window_wire_read_i16(wire, 0x16) == 0);
    sim_window_ref_registry_detach(&registry, 16);
}

static void test_four_parameters(void)
{
    SimWindowRefRegistry registry;
    uint8_t wire[0x80];
    char *handle;
    uint8_t *object;
    int16_t expected[4] = { 11, -22, 33, -44 };
    unsigned i;
    setup(&registry, wire, &handle, 1);
    object = wire + 0x30;
    for (i = 0; i < 4; ++i) {
        sim_window_wire_write_i16(object, 0x18u + 2u * i, 5);
        sim_window_wire_write_i16(object, 0x10u + 2u * i, (int16_t)i);
    }
    CHECK(sim_window_parameters_store_open(&registry, 0x1000, handle, 4,
                                           expected[0], expected[1],
                                           expected[2], expected[3]) == SIM_WINDOW_PARAMETERS_OK);
    for (i = 0; i < 4; ++i)
        CHECK(sim_window_wire_read_i16(wire, 0x10u + 2u * i) == expected[i]);
    sim_window_ref_registry_detach(&registry, 16);
}

static void test_missing_parameter_is_atomic(void)
{
    SimWindowRefRegistry registry;
    uint8_t wire[0x80];
    char *handle;
    uint8_t *object;
    unsigned i;
    setup(&registry, wire, &handle, 1);
    object = wire + 0x30;
    for (i = 0; i < 4; ++i) {
        sim_window_wire_write_i16(wire, 0x10u + 2u * i, (int16_t)(0x1111u + i));
        sim_window_wire_write_i16(object, 0x18u + 2u * i, 5);
        sim_window_wire_write_i16(object, 0x10u + 2u * i, (int16_t)i);
    }
    CHECK(sim_window_parameters_store_open(&registry, 0x1000, handle, 2,
                                           1, 2, 3, 4) == SIM_WINDOW_PARAMETERS_MISSING_SOURCE_PARAMETER);
    for (i = 0; i < 4; ++i)
        CHECK(sim_window_wire_read_i16(wire, 0x10u + 2u * i) == (int16_t)(0x1111u + i));
    sim_window_ref_registry_detach(&registry, 16);
}

static void test_unreferenced_and_invalid_count(void)
{
    SimWindowRefRegistry registry;
    uint8_t wire[0x80];
    char *handle;
    uint8_t *object;
    setup(&registry, wire, &handle, 1);
    object = wire + 0x30;
    sim_window_wire_write_i16(object, 0x18, 4);
    sim_window_wire_write_i16(object, 0x10, 99);
    CHECK(sim_window_parameters_store_open(&registry, 0x1000, handle, 0,
                                           0, 0, 0, 0) == SIM_WINDOW_PARAMETERS_OK);
    CHECK(sim_window_parameters_store_open(&registry, 0x1000, handle, 3,
                                           1, 2, 3, 4) == SIM_WINDOW_PARAMETERS_BAD_SUPPLIED_COUNT);
    sim_window_ref_registry_detach(&registry, 16);
}

int main(void)
{
    test_no_optional_parameters();
    test_two_parameters();
    test_four_parameters();
    test_missing_parameter_is_atomic();
    test_unreferenced_and_invalid_count();
    if (failures != 0) return 1;
    puts("window parameter helper tests: PASS");
    return 0;
}
