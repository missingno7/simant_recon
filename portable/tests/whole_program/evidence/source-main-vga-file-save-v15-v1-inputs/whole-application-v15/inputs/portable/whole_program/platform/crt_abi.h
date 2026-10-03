#ifndef SIMANT_WHOLE_PROGRAM_CRT_ABI_H
#define SIMANT_WHOLE_PROGRAM_CRT_ABI_H

#include <stdint.h>

/* Native names used only by the whole-program source adapter. */
extern char *sim_sys_errlist[38];
extern int16_t sim_sys_nerr;

/* The original process registered this handler for DOS INT 24. Native file
 * operations report errors directly; registration is retained for source
 * observability, but no host filesystem callback fabricates an INT 24 event. */
typedef int16_t (*SimCrtHardErrorHandler)(void);
void sim_crt_harderr_install(SimCrtHardErrorHandler handler);
SimCrtHardErrorHandler sim_crt_harderr_registered(void);
int16_t sim_crt_harderr_retired_result(void);

/* Source use is limited to testing MSC's _LOWER flag for byte-valued resource
 * text. ASCII is supported from original-table observation; other bytes fail
 * closed until their table behavior is separately admitted. */
int sim_msc_ctype_is_lower_ascii(int value);

#endif
