#ifndef SIMANT_RECOVERED_MENU_ADAPTER_H
#define SIMANT_RECOVERED_MENU_ADAPTER_H

#include <stdint.h>

/* Requires the caller's active recovered state/RNG/host binding. The S11
 * event ABI differs from S22's edit event; this bridge constructs S11's
 * event explicitly and retains the full DOS command word. */
void sim_recovered_source_proc_menu_command(uint16_t command);

#endif
