#ifndef SIMANT_WHOLE_EMS_DOS_ABI_H
#define SIMANT_WHOLE_EMS_DOS_ABI_H

#include <stdint.h>

/* Native storage for the public DGROUP values exported by original m195A.asm. */
extern int8_t fd_55B3_360C;
extern char *fd_55B3_360E;
extern int16_t fd_55B3_3612;
extern int16_t fd_55B3_3614;

/* Source-compatible native entry points used by m0250.c and m19DC.c. */
int16_t f_195A_0260(void);
_Noreturn void f_195A_001D(void);
_Noreturn void f_195A_0035(void);
_Noreturn int16_t f_195A_004B(int16_t pages);
_Noreturn void f_195A_0062(int16_t handle, int16_t logical_page,
                           int16_t physical_page);
_Noreturn void f_195A_007D(int16_t handle);
_Noreturn void f_195A_00F8(int16_t handle);
_Noreturn void f_195A_010D(int16_t handle);
_Noreturn void f_195A_0122(int16_t handle, int16_t count,
                           int16_t *mapping);
_Noreturn void f_195A_01CB(int16_t handle, char *name);

#endif
