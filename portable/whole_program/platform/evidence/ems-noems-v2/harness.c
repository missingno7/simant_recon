#include "dos_io.h"
#include "ems_dos_abi.h"
#include "ems_host.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int f_0250_012D(void);
int f_19DC_001A(long size);
int f_19DC_02FB(int file, long offset, char *buffer, long count);

int g_19D0;
int g_389C, g_389E, g_390C;

typedef struct {
    unsigned age;
    int file;
    int page;
} EmsSlot;

EmsSlot **f_2CFB_0002(long size, int flags, char *name);
void f_19DC_0008(void);

char *fd_50F6_3B48;
EmsSlot **fd_50F6_3B4C;

static int unexpected_ems_service;
static int unexpected_ems_cache;
static int s_8C74;
static long s_8C76;
int g_38A0;

#define CHECK_FILE() if (s_8C74 != file) Punt("Handle mismatch")

int WinPrintf(char *format, ...)
{
    (void)format;
    return 0;
}

void Punt(char *format, ...)
{
    (void)format;
    abort();
}

void DosPunt(char *message)
{
    (void)message;
    abort();
}

char *f_19DC_0148(int file, int page)
{
    (void)file;
    (void)page;
    ++unexpected_ems_cache;
    return NULL;
}

void f_0250_0114(void)
{
    ++unexpected_ems_service;
}

EmsSlot **f_2CFB_0002(long size, int flags, char *name)
{
    (void)size;
    (void)flags;
    (void)name;
    ++unexpected_ems_service;
    return NULL;
}

void f_19DC_0008(void)
{
    ++unexpected_ems_service;
}

void *_fmemcpy(void *dst, const void *src, int count)
{
    return memmove(dst, src, (size_t)(unsigned)count);
}

long lseek(int fd, long offset, int origin)
{
    return (long)dos_lseek((int16_t)fd, (int32_t)offset, (int16_t)origin);
}

int read(int fd, void *buffer, unsigned count)
{
    return (int)dos_read((int16_t)fd, buffer, (uint16_t)count);
}

/* RUNNER_INSERTS_ACTUAL_CALLER_FUNCTIONS_HERE */

int main(int argc, char **argv)
{
    EmsHostInfo info = { 0xff, 0xffff, 0xffff, 0xffff };
    uint16_t free_pages = 99, total_pages = 99, frame = 99, handle = 99;
    uint8_t actual[16], expected[16];
    int16_t fd;
    long read_count;
    EmsHostStatus status;

    if (argc == 2) {
        if (strcmp(argv[1], "frame") == 0) f_195A_001D();
        else if (strcmp(argv[1], "pages") == 0) f_195A_0035();
        else if (strcmp(argv[1], "allocate") == 0) (void)f_195A_004B(1);
        else if (strcmp(argv[1], "map") == 0) f_195A_0062(1, 0, 0);
        else if (strcmp(argv[1], "free") == 0) f_195A_007D(1);
        else if (strcmp(argv[1], "save") == 0) f_195A_00F8(1);
        else if (strcmp(argv[1], "restore") == 0) f_195A_010D(1);
        else if (strcmp(argv[1], "map-list") == 0) f_195A_0122(1, 1, NULL);
        else if (strcmp(argv[1], "name") == 0) f_195A_01CB(1, "NOEMS");
        else return 90;
        return 91;
    }

    if (argc != 1) return 89;

    if (f_195A_0260() != 0 || fd_55B3_360C != 0 || fd_55B3_360E != NULL ||
        fd_55B3_3612 != 0 || fd_55B3_3614 != 0) return 9;

    status = ems_host_probe(&info);
    if (status != EMS_HOST_UNAVAILABLE || info.version || info.total_pages ||
        info.free_pages || info.page_frame_segment) return 10;
    if (ems_host_query_pages(&free_pages, &total_pages) != EMS_HOST_UNAVAILABLE ||
        free_pages || total_pages) return 11;
    if (ems_host_page_frame(&frame) != EMS_HOST_UNAVAILABLE || frame) return 12;
    if (ems_host_allocate(3, &handle) != EMS_HOST_UNAVAILABLE || handle) return 13;
    if (ems_host_map(1, 0, 0) != EMS_HOST_UNAVAILABLE ||
        ems_host_free(1) != EMS_HOST_UNAVAILABLE ||
        ems_host_set_name(1, "NOEMS") != EMS_HOST_UNAVAILABLE) return 14;
    if (ems_host_allocate(0, &handle) != EMS_HOST_INVALID_ARGUMENT ||
        ems_host_map(0, 0, 0) != EMS_HOST_INVALID_HANDLE ||
        ems_host_free(0) != EMS_HOST_INVALID_HANDLE ||
        ems_host_set_name(0, "NOEMS") != EMS_HOST_INVALID_HANDLE ||
        ems_host_set_name(1, NULL) != EMS_HOST_INVALID_ARGUMENT) return 15;

    fd_55B3_360C = 0;
    fd_55B3_3612 = fd_55B3_3614 = 0;
    fd_55B3_360E = NULL;
    g_19D0 = 0;
    if (f_0250_012D() != 0 || g_19D0 != 0 || unexpected_ems_service) return 20;

    g_389C = 0;
    g_389E = 0;
    g_390C = 0;
    if (f_19DC_001A(500000L) != 0 || g_389C != 0 || g_389E != 0 ||
        fd_55B3_360C || fd_55B3_3612 || fd_55B3_3614 ||
        (uintptr_t)fd_55B3_360E || unexpected_ems_service) return 21;

    fd = dos_open("assets/SHARED.DAT", DOS_O_BINARY);
    if (fd <= 0) return 22;
    if (dos_lseek(fd, 14, 0) != 14 || dos_read(fd, expected, sizeof expected) != sizeof expected ||
        dos_lseek(fd, 14, 0) != 14) return 23;
    read_count = f_19DC_02FB(fd, 14, (char *)actual, sizeof actual);
    if (read_count != sizeof actual || memcmp(actual, expected, sizeof actual) != 0 ||
        g_390C != 1 || unexpected_ems_service || unexpected_ems_cache) return 24;
    dos_close(fd);

    puts("EMS host no-EMS query, explicit operation failures, actual m0250/m19DC gates, and m19DC plain file-cache fallback: PASS");
    return 0;
}
