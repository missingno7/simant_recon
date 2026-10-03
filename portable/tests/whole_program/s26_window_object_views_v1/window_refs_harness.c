#include "portable/whole_program/window_refs.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

int main(void)
{
    uint8_t bytes[0x34 + 2 * 0x28];
    char *handle = (char *)bytes;
    SimWindowRefRegistry registry;
    char **objects;

    memset(bytes, 0, sizeof(bytes));
    sim_window_wire_write_u16(bytes, 0x0c, 2);
    sim_window_wire_write_i16(bytes, 0x34 + 0x22, 0x28);
    sim_window_wire_write_i16(bytes, 0x5c + 0x22, 0x28);
    bytes[0x34 + 0x21] = 0x0c;
    bytes[0x5c + 0x21] = 0x12;

    sim_window_ref_registry_init(&registry);
    assert(sim_window_ref_registry_attach(&registry, 0, &handle,
                                           sizeof(bytes)) == SIM_WINDOW_REFS_OK);
    objects = sim_window_ref_registry_objects_for_buffer(&registry, handle);
    assert(objects != NULL);
    assert((uint8_t *)objects[0] == bytes + 0x34);
    assert((uint8_t *)objects[1] == bytes + 0x5c);
    assert(sim_window_ref_registry_objects_for_buffer(
               &registry, (const char *)bytes + 1) == NULL);
    sim_window_ref_registry_detach(&registry, 0);
    assert(sim_window_ref_registry_objects_for_buffer(&registry, handle) == NULL);
    return 0;
}
