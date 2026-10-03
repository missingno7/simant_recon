#include "seed_source.h"

#include <stdlib.h>

static PortableStartupSeedReader startup_reader;
static void *startup_context;

int portable_seed_source_bind(PortableStartupSeedReader reader, void *context)
{
    if (reader == NULL || startup_reader != NULL)
        return 0;
    startup_reader = reader;
    startup_context = context;
    return 1;
}

void portable_seed_source_unbind(void)
{
    startup_reader = NULL;
    startup_context = NULL;
}

uint32_t dos_host_read_u32(uint32_t physical_address)
{
    uint32_t value;
    if (physical_address != UINT32_C(0x46c0) || startup_reader == NULL ||
        !startup_reader(startup_context, &value))
        abort();
    return value;
}

_Noreturn void dos_host_divide_fault(void)
{
    abort();
}
