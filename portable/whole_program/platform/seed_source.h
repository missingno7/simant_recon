#ifndef SIMANT_WHOLE_SEED_SOURCE_H
#define SIMANT_WHOLE_SEED_SOURCE_H

#include <stdint.h>

/* GetRRandSeed's original far read is 046C:0000 (physical 0x46c0),
 * distinct from the BIOS tick counter at 0000:046C. The modern application
 * supplies its startup seed policy explicitly; this does not emulate RAM. */
typedef int (*PortableStartupSeedReader)(void *context, uint32_t *value);
int portable_seed_source_bind(PortableStartupSeedReader reader, void *context);
void portable_seed_source_unbind(void);
uint32_t dos_host_read_u32(uint32_t physical_address);
_Noreturn void dos_host_divide_fault(void);

#endif
