#ifndef SIMANT_WHOLE_STARTUP_HOST_H
#define SIMANT_WHOLE_STARTUP_HOST_H

#include <stdint.h>

/* The source asks BIOS INT 13h to reset physical DOS drives. Native builds
 * have no such drive namespace; this policy intentionally performs no host I/O. */
void dos_host_reset_disk_if_ready(uint8_t bios_drive);

/* Whole-program converter retires the BIOS status/reset loop on native hosts. */
void dos_host_retire_bios_reset_loop(void);

/* Preserve MSC startup's ignored Ctrl-Break and Ctrl-C policy in call order. */
void dos_host_ignore_legacy_break(void);
void dos_host_ignore_legacy_interrupt(void);

#endif
