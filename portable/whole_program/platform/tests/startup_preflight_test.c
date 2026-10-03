#include "../dos_io.h"
#include "../startup_preflight.h"
#include "../startup_host.h"

#include <stdint.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void le32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

static void fixture(const char *path, size_t n)
{
    uint8_t bytes[270];
    FILE *f;
    size_t i;
    memset(bytes, 0, sizeof bytes);
    le32(bytes + 6, 0); /* Source seeks to headers + sizeof(WinFileHeader). */
    for (i = 14; i < sizeof bytes; ++i) bytes[i] = (uint8_t)(i ^ 0x5a);
    f = fopen(path, "wb");
    if (!f || fwrite(bytes, 1, n, f) != n || fclose(f) != 0) exit(30);
}

int main(int argc, char **argv)
{
    int16_t optional_fd = -9, opened = -9;
    uint8_t header[14];
    char valid[1024], short_file[1024];
    int16_t fd;

    if (argc != 3) return 2;
    if (dos_startup_preflight(argv[1], &optional_fd, &opened) != 0 ||
        opened != 5 || optional_fd != 0) return 10;

    optional_fd = -9;
    opened = -9;
    if (dos_startup_preflight("startup-preflight-file-does-not-exist.exe",
                              &optional_fd, &opened) != -1 ||
        opened != 0 || optional_fd != 0 || dos_errno != 2) return 11;

    if (snprintf(valid, sizeof valid, "%s/valid-install.exe", argv[2]) < 0 ||
        snprintf(short_file, sizeof short_file, "%s/short-install.exe", argv[2]) < 0)
        return 12;
    fixture(valid, 270);
    fixture(short_file, 269);

    if (dos_startup_preflight(valid, &optional_fd, &opened) != 0 ||
        opened != 5 || optional_fd <= 0) return 13;
    if (dos_read(optional_fd, header, sizeof header) != sizeof header ||
        header[6] != 0 || header[7] != 0 || header[8] != 0 || header[9] != 0)
        return 14;
    fd = optional_fd;
    dos_startup_close_optional(&optional_fd);
    if (optional_fd != 0 || dos_read(fd, header, 1) != -1 || dos_errno != 9)
        return 15;

    optional_fd = -9;
    if (dos_startup_preflight(short_file, &optional_fd, &opened) != 0 ||
        opened != 5 || optional_fd != 0) return 16;

    dos_host_retire_bios_reset_loop();
    dos_host_ignore_legacy_break();
    dos_host_ignore_legacy_interrupt();
#ifdef SIGBREAK
    if (signal(SIGBREAK, SIG_DFL) != SIG_IGN) return 17;
#endif
    if (signal(SIGINT, SIG_DFL) != SIG_IGN) return 19;

    fd = dos_open(argv[1], 0);
    if (fd <= 0) return 17;
    if (dos_read(fd, header, sizeof header) != sizeof header ||
        header[0] != 'M' || header[1] != 'Z') return 18;
    dos_close(fd);

    puts("startup preflight: actual install 5 opens; missing path; valid retained optional file; truncated optional file; close invalidation; retired BIOS reset; SIGBREAK/SIGINT ignore mapping: PASS");
    return 0;
}
