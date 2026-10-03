#include "ems_dos_abi.h"

#include <stdlib.h>

#include "ems_host.h"

int8_t fd_55B3_360C = 0;
char *fd_55B3_360E = NULL;
int16_t fd_55B3_3612 = 0;
int16_t fd_55B3_3614 = 0;

int16_t f_195A_0260(void)
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

_Noreturn void f_195A_001D(void) { ems_operation_without_device(); }
_Noreturn void f_195A_0035(void) { ems_operation_without_device(); }
_Noreturn int16_t f_195A_004B(int16_t pages)
{
    (void)pages;
    ems_operation_without_device();
}
_Noreturn void f_195A_0062(int16_t handle, int16_t logical_page,
                           int16_t physical_page)
{
    (void)handle;
    (void)logical_page;
    (void)physical_page;
    ems_operation_without_device();
}
_Noreturn void f_195A_007D(int16_t handle)
{
    (void)handle;
    ems_operation_without_device();
}
_Noreturn void f_195A_00F8(int16_t handle)
{
    (void)handle;
    ems_operation_without_device();
}
_Noreturn void f_195A_010D(int16_t handle)
{
    (void)handle;
    ems_operation_without_device();
}
_Noreturn void f_195A_0122(int16_t handle, int16_t count,
                           int16_t *mapping)
{
    (void)handle;
    (void)count;
    (void)mapping;
    ems_operation_without_device();
}
_Noreturn void f_195A_01CB(int16_t handle, char *name)
{
    (void)handle;
    (void)name;
    ems_operation_without_device();
}
