#include "startup_host.h"

#include <signal.h>

void dos_host_reset_disk_if_ready(uint8_t bios_drive)
{
    /* A host file is not a DOS BIOS drive. In particular, do not substitute
     * fsync, close/reopen, or any other filesystem operation for INT 13h. */
    (void)bios_drive;
}

void dos_host_retire_bios_reset_loop(void)
{
    /* The host has no INT 13h physical-drive reset to perform. */
}

void dos_host_ignore_legacy_break(void)
{
#ifdef SIGBREAK
    (void)signal(SIGBREAK, SIG_IGN);
#endif
}

void dos_host_ignore_legacy_interrupt(void)
{
    (void)signal(SIGINT, SIG_IGN);
}
