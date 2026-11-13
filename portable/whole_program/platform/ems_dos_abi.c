#include "ems_dos_abi.h"

#include <stdlib.h>

#include "ems_host.h"

extern char *ems_page_frame_pointer ;

int16_t ems_initialize(void)
{
    EmsHostInfo info;
    (void)ems_host_probe(&info);
    /* The original no-device branch returns zero without reaching INT 67h. */
    return 0;
}

static _Noreturn void ems_operation_without_device(void)
{
    /* Original m195A.asm routes nonzero INT 67h status through Punt("EMS Error"). */
    _Exit(86);
}

_Noreturn void ems_query_page_frame(void) { ems_operation_without_device(); }
_Noreturn void ems_query_page_counts(void) { ems_operation_without_device(); }
_Noreturn int16_t ems_allocate_pages(int16_t pages)
{
    (void)pages;
    ems_operation_without_device();
}
_Noreturn void ems_map_page(int16_t handle, int16_t logical_page,
                           int16_t physical_page)
{
    (void)handle;
    (void)logical_page;
    (void)physical_page;
    ems_operation_without_device();
}
_Noreturn void ems_free_handle(int16_t handle)
{
    (void)handle;
    ems_operation_without_device();
}
_Noreturn void ems_save_handle_map(int16_t handle)
{
    (void)handle;
    ems_operation_without_device();
}
_Noreturn void ems_restore_handle_map(int16_t handle)
{
    (void)handle;
    ems_operation_without_device();
}
_Noreturn void ems_map_multiple_pages(int16_t handle, int16_t count,
                           int16_t *mapping)
{
    (void)handle;
    (void)count;
    (void)mapping;
    ems_operation_without_device();
}
_Noreturn void ems_set_handle_name(int16_t handle, char *name)
{
    (void)handle;
    (void)name;
    ems_operation_without_device();
}
