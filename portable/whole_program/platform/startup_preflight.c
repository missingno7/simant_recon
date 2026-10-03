#include "startup_preflight.h"

#include "dos_io.h"

#include <stdint.h>

enum { INSTALL_PROBE_COUNT = 5, WIN_HEADER_BYTES = 14, WIN_BLOCK_BYTES = 256 };

static uint32_t read_le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int16_t find_optional_window_headers(char *path)
{
    uint8_t header[WIN_HEADER_BYTES];
    int16_t fd;
    int16_t n;
    int32_t end;
    uint32_t offset;

    fd = dos_open(path, 0);
    if (fd <= 0) {
        dos_errno = 0;
        return 0;
    }

    n = dos_read(fd, header, WIN_HEADER_BYTES);
    if (n != WIN_HEADER_BYTES) {
        dos_close(fd);
        dos_errno = 0;
        return 0;
    }

    /* The DOS source consumes the 32-bit `headers` field at byte offset 6.
     * Validate that its following 256-byte block exists before retaining a
     * descriptor for m00BA's optional read. The other header words are not
     * interpreted by that caller. */
    offset = read_le32(header + 6);
    end = dos_lseek(fd, 0, 2);
    if (end < 0 || offset > (uint32_t)end ||
        (uint32_t)end - offset < WIN_HEADER_BYTES + WIN_BLOCK_BYTES ||
        dos_lseek(fd, 0, 0) != 0) {
        dos_close(fd);
        dos_errno = 0;
        return 0;
    }
    return fd;
}

int16_t dos_startup_preflight(char *path, int16_t *optional_fd,
                              int16_t *opened_before_failure)
{
    int16_t opened[INSTALL_PROBE_COUNT];
    int16_t count = 0;
    int i;

    if (optional_fd) *optional_fd = 0;
    if (opened_before_failure) *opened_before_failure = 0;
    if (!path || !optional_fd || !opened_before_failure) {
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
    for (i = 0; i < INSTALL_PROBE_COUNT; ++i) dos_close(opened[i]);

    /* Do not reuse one of the just-closed numeric descriptor values. DOS main
     * stored fh[0] after closing it; startup later reuses that slot for live
     * database files. A valid optional block therefore gets its own live open. */
    *optional_fd = find_optional_window_headers(path);
    *opened_before_failure = INSTALL_PROBE_COUNT;
    dos_errno = 0;
    return 0;
}

void dos_startup_close_optional(int16_t *optional_fd)
{
    if (!optional_fd || *optional_fd <= 0) return;
    dos_close(*optional_fd);
    *optional_fd = 0;
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
