#ifndef SIMANT_WHOLE_EMS_DOS_ABI_H
#define SIMANT_WHOLE_EMS_DOS_ABI_H

#include <stdint.h>
#include "../state/asm_shared_state.h"

/* Native host pointer replacing the far page-frame pointer when EMS is absent. */
extern char *ems_page_frame_pointer;

/* Source-compatible native entry points used by m0250.c and m19DC.c. */
int16_t ems_initialize(void);
_Noreturn void ems_query_page_frame(void);
_Noreturn void ems_query_page_counts(void);
_Noreturn int16_t ems_allocate_pages(int16_t pages);
_Noreturn void ems_map_page(int16_t handle, int16_t logical_page,
                           int16_t physical_page);
_Noreturn void ems_free_handle(int16_t handle);
_Noreturn void ems_save_handle_map(int16_t handle);
_Noreturn void ems_restore_handle_map(int16_t handle);
_Noreturn void ems_map_multiple_pages(int16_t handle, int16_t count,
                           int16_t *mapping);
_Noreturn void ems_set_handle_name(int16_t handle, char *name);

#endif
