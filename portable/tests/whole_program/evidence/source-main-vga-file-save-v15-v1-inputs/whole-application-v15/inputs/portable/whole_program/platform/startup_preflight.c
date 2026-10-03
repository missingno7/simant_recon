#include "startup_preflight.h"

#include "dos_io.h"

#include <stdint.h>

enum { INSTALL_PROBE_COUNT = 5 };

int16_t dos_startup_preflight(char *path, int16_t *closed_fd_slot,
                              int16_t *opened_before_failure)
{
    int16_t opened[INSTALL_PROBE_COUNT];
    int16_t count = 0;
    int i;

    if (closed_fd_slot) *closed_fd_slot = 0;
    if (opened_before_failure) *opened_before_failure = 0;
    if (!path || !closed_fd_slot || !opened_before_failure) {
        /* Match a target invalid-argument failure through the DOS wrapper. */
        (void)dos_open(NULL, 0);
        return -1;
    }

    for (i = 0; i < INSTALL_PROBE_COUNT; ++i) {
        opened[i] = dos_open(path, 0);
        if (opened[i] <= 0) {
            int16_t saved_error = dos_errno;
            int j;
            *opened_before_failure = count;
            for (j = 0; j < count; ++j) dos_close(opened[j]);
            dos_errno = saved_error;
            return -1;
        }
        ++count;
    }
    /* DOS main stores fh[0] after closing all five probes. The descriptor is
     * a number, not an INSTALL.EXE identity: MSC/DOS reuses the lowest free
     * virtual handle, so the first retained database data open (language if
     * present, otherwise SHARED) receives this same number. */
    *closed_fd_slot = opened[0];
    for (i = 0; i < INSTALL_PROBE_COUNT; ++i) dos_close(opened[i]);
    *opened_before_failure = INSTALL_PROBE_COUNT;
    dos_errno = 0;
    return 0;
}

char *dos_startup_error_text(int16_t error)
{
    static char unknown[] = "Unknown DOS error";
    static char *const messages[] = {
        "No error", "Invalid function", "File not found", "Path not found",
        "Too many open files", "Access denied", "Invalid handle", "Memory control blocks destroyed",
        "Insufficient memory", "Invalid memory block address", "Invalid environment",
        "Invalid format", "Invalid access code", "Invalid data", "Unknown unit",
        "Invalid disk drive", "Attempt to remove current directory", "Not same device",
        "No more files", "Write protected disk", "Unknown unit", "Drive not ready",
        "Unknown command", "Data error", "Bad request structure", "Seek error",
        "Unknown media type", "Sector not found", "Printer out of paper", "Write fault",
        "Read fault", "General failure", "Sharing violation", "Lock violation",
        "Wrong disk", "FCB unavailable"
    };
    if (error >= 0 && (unsigned)error < sizeof messages / sizeof messages[0])
        return messages[(unsigned)error];
    return unknown;
}
