#include "window_runtime_owner.h"

SimWindowRefRegistry sim_window_ref_registry;

int sim_window_runtime_owner_init(void)
{
    size_t i;
    for (i = 0; i < SIM_WINDOW_REF_REGISTRY_CAPACITY; ++i)
        if (sim_window_ref_registry.entries[i].bound)
            return 0;
    sim_window_ref_registry_init(&sim_window_ref_registry);
    return 1;
}
