#include "dos_io.h"
#include "drive_directory.h"

#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <sys/stat.h>
#define host_open _open
#define host_read _read
#define host_write _write
#define host_close _close
#define host_access _access
#define host_unlink _unlink
#define host_lseek64 _lseeki64
#define HOST_BINARY _O_BINARY
#define HOST_TEXT _O_TEXT
#define HOST_APPEND _O_APPEND
#define HOST_CREAT _O_CREAT
#define HOST_TRUNC _O_TRUNC
#define HOST_EXCL _O_EXCL
#define HOST_NOINHERIT _O_NOINHERIT
#define HOST_RDONLY _O_RDONLY
#define HOST_WRONLY _O_WRONLY
#define HOST_RDWR _O_RDWR
#define HOST_IREAD _S_IREAD
#define HOST_IWRITE _S_IWRITE
#define HOST_IEXEC _S_IEXEC
#else
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <strings.h>
#define host_open open
#define host_read read
#define host_write write
#define host_close close
#define host_access access
#define host_unlink unlink
#define host_lseek64 lseek
#define HOST_BINARY 0
#define HOST_TEXT 0
#define HOST_APPEND O_APPEND
#define HOST_CREAT O_CREAT
#define HOST_TRUNC O_TRUNC
#define HOST_EXCL O_EXCL
#define HOST_NOINHERIT 0
#define HOST_RDONLY O_RDONLY
#define HOST_WRONLY O_WRONLY
#define HOST_RDWR O_RDWR
#define HOST_IREAD S_IRUSR
#define HOST_IWRITE S_IWUSR
#define HOST_IEXEC S_IXUSR
#endif

struct DosFileStream {
    FILE *native;
};

#define DOS_HANDLE_FIRST 3
#define DOS_HANDLE_LIMIT 32768

int16_t dos_errno;
int16_t dos_fmode = DOS_O_TEXT;
static int host_handles[DOS_HANDLE_LIMIT];
static uint8_t handle_initialized[DOS_HANDLE_LIMIT];

static int16_t map_errno(int e)
{
    switch (e) {
    case 0: return 0;
    case EPERM: return 1;
    case ENOENT: return 2;
    case EINTR: return 4;
    case EIO: return 5;
    case ENXIO: return 6;
    case ENOEXEC: return 8;
    case EBADF: return 9;
    case EAGAIN: return 11;
    case ENOMEM: return 12;
    case EACCES: return 13;
#ifdef ENODEV
    case ENODEV: return 19;
#endif
#ifdef EFAULT
    case EFAULT: return 14;
#endif
    case EEXIST: return 17;
    case EXDEV: return 18;
    case ENOTDIR: return 20;
    case EISDIR: return 21;
    case EINVAL: return 22;
    case ENFILE: return 23;
    case EMFILE: return 24;
    case ENOSPC: return 28;
    case ESPIPE: return 29;
    case EROFS: return 30;
#ifdef EOVERFLOW
    case EOVERFLOW: return 22;
#endif
#ifdef EPIPE
    case EPIPE: return 32;
#endif
    case ERANGE: return 34;
    default: return 5; /* MSC EIO: no guessed DOS code for host-only failures. */
    }
}

static int16_t record_error(void)
{
    dos_errno = map_errno(errno);
    return -1;
}

static int resolve_source_path(const char *source_path, char *host_path,
                               size_t capacity)
{
    uint16_t dos_error;
    if (sim_drive_resolve_path(source_path, host_path, capacity, 0,
                               &dos_error))
        return 0;
    errno = sim_drive_error_to_errno(dos_error);
    return -1;
}

static int host_fd(int16_t fd)
{
    if (fd < DOS_HANDLE_FIRST || !handle_initialized[(uint16_t)fd]) {
        errno = EBADF;
        return -1;
    }
    return host_handles[(uint16_t)fd];
}

static int allocate_dos_fd(int hfd)
{
    int i;
    for (i = DOS_HANDLE_FIRST; i < DOS_HANDLE_LIMIT; ++i) {
        if (!handle_initialized[i]) {
            host_handles[i] = hfd;
            handle_initialized[i] = 1;
            return i;
        }
    }
    errno = EMFILE;
    return -1;
}

static int flags_to_host(int16_t flags, int *host_flags)
{
    unsigned f = (uint16_t)flags;
    unsigned known = DOS_O_WRONLY | DOS_O_RDWR | DOS_O_APPEND | DOS_O_NOINHERIT |
                     DOS_O_CREAT | DOS_O_TRUNC | DOS_O_EXCL | DOS_O_TEXT | DOS_O_BINARY;
    unsigned access = f & (DOS_O_WRONLY | DOS_O_RDWR);
    unsigned translation = f & (DOS_O_TEXT | DOS_O_BINARY);
    int result;
    if ((f & ~known) || access == (DOS_O_WRONLY | DOS_O_RDWR) ||
        translation == (DOS_O_TEXT | DOS_O_BINARY) ||
        ((f & DOS_O_TRUNC) && access == 0)) {
        errno = EINVAL;
        return -1;
    }
    result = access == DOS_O_WRONLY ? HOST_WRONLY :
             access == DOS_O_RDWR ? HOST_RDWR : HOST_RDONLY;
    if (f & DOS_O_APPEND) result |= HOST_APPEND;
    if (f & DOS_O_CREAT) result |= HOST_CREAT;
    if (f & DOS_O_TRUNC) result |= HOST_TRUNC;
    if (f & DOS_O_EXCL) result |= HOST_EXCL;
    if (f & DOS_O_NOINHERIT) result |= HOST_NOINHERIT;
    if (translation == DOS_O_BINARY || (!translation && (dos_fmode & DOS_O_BINARY)))
        result |= HOST_BINARY;
    else
        result |= HOST_TEXT;
    *host_flags = result;
    return 0;
}

int16_t dos_open(char *path, int16_t flags, ...)
{
    int host_flags, hfd, dfd, mode = HOST_IREAD | HOST_IWRITE;
    unsigned f = (uint16_t)flags;
    char host_path[32768];
    if (!path) { errno = EFAULT; return record_error(); }
    if (flags_to_host(flags, &host_flags) < 0)
        return record_error();
    if (resolve_source_path(path, host_path, sizeof host_path) < 0)
        return record_error();
    if (f & DOS_O_CREAT) {
        int dos_mode;
        va_list ap;
        va_start(ap, flags);
        dos_mode = va_arg(ap, int);
        va_end(ap);
        mode = 0;
        if (dos_mode & 0x0100) mode |= HOST_IREAD;
        if (dos_mode & 0x0080) mode |= HOST_IWRITE;
        if (dos_mode & 0x0040) mode |= HOST_IEXEC;
        if ((dos_mode & ~0x01C0) != 0) {
            errno = EINVAL;
            return record_error();
        }
    }
    hfd = host_open(host_path, host_flags, mode);
    if (hfd < 0) return record_error();
    dfd = allocate_dos_fd(hfd);
    if (dfd < 0) {
        int saved = errno;
        host_close(hfd);
        errno = saved;
        return record_error();
    }
    dos_errno = 0;
    return (int16_t)dfd;
}

int16_t dos_read(int16_t fd, void *buffer, uint16_t count)
{
    int hfd = host_fd(fd), n;
    if (hfd < 0) return record_error();
    if (!buffer && count) { errno = EFAULT; return record_error(); }
    n = host_read(hfd, buffer, (unsigned)count);
    if (n < 0) return record_error();
    dos_errno = 0;
    return (int16_t)(uint16_t)n;
}

int16_t dos_write(int16_t fd, void *buffer, uint16_t count)
{
    int hfd = host_fd(fd), n;
    if (hfd < 0) return record_error();
    if (!buffer && count) { errno = EFAULT; return record_error(); }
    n = host_write(hfd, buffer, (unsigned)count);
    if (n < 0) return record_error();
    dos_errno = 0;
    return (int16_t)(uint16_t)n;
}

int32_t dos_lseek(int16_t fd, int32_t offset, int16_t origin)
{
    int hfd = host_fd(fd);
    int64_t result;
    int whence = origin == 0 ? SEEK_SET : origin == 1 ? SEEK_CUR : origin == 2 ? SEEK_END : -1;
    if (hfd < 0) { record_error(); return -1; }
    if (whence < 0) { errno = EINVAL; record_error(); return -1; }
    result = host_lseek64(hfd, offset, whence);
    if (result < 0) { record_error(); return -1; }
    if (result > INT32_MAX) { errno = EOVERFLOW; record_error(); return -1; }
    dos_errno = 0;
    return (int32_t)result;
}

int16_t dos_close(int16_t fd)
{
    int hfd = host_fd(fd);
    if (hfd < 0) return record_error();
    handle_initialized[(uint16_t)fd] = 0;
    host_handles[(uint16_t)fd] = -1;
    if (host_close(hfd) < 0) return record_error();
    dos_errno = 0;
    return 0;
}

int16_t dos_access(char *path, int16_t mode)
{
    char host_path[32768];
    if (!path) { errno = EFAULT; return record_error(); }
    if (mode & ~7) { errno = EINVAL; return record_error(); }
    if (resolve_source_path(path, host_path, sizeof host_path) < 0)
        return record_error();
    if (host_access(host_path, mode) < 0) return record_error();
    dos_errno = 0;
    return 0;
}

int16_t dos_chdir(char *path)
{
    uint16_t dos_error;
    if (!path) { errno = EFAULT; return record_error(); }
    dos_error = sim_drive_chdir(path);
    if (dos_error) {
        errno = sim_drive_error_to_errno(dos_error);
        return record_error();
    }
    dos_errno = 0;
    return 0;
}

char *dos_getcwd(char *buffer, int16_t size)
{
    size_t n = size > 0 ? (size_t)(uint16_t)size : 0;
    char local[65];
    char *result = buffer;
    if (size < 0) { errno = EINVAL; record_error(); return NULL; }
    if (buffer == NULL) {
        if (size == 0) n = sizeof local;
        result = (char *)malloc(n);
        if (!result) { errno = ENOMEM; record_error(); return NULL; }
    } else if (n == 0) {
        errno = EINVAL;
        record_error();
        return NULL;
    }
    if (!sim_drive_getcwd(0, result, n)) {
        if (buffer == NULL) free(result);
        errno = ERANGE;
        record_error();
        return NULL;
    }
    dos_errno = 0;
    return result;
}

int16_t dos_remove(char *path)
{
    char host_path[32768];
    if (!path) { errno = EFAULT; return record_error(); }
    if (resolve_source_path(path, host_path, sizeof host_path) < 0)
        return record_error();
    if (host_unlink(host_path) < 0) return record_error();
    dos_errno = 0;
    return 0;
}

static unsigned char ascii_lower(unsigned char c)
{
    if (c >= 'A' && c <= 'Z') return (unsigned char)(c + ('a' - 'A'));
    return c;
}

int16_t dos_stricmp(char *a, char *b)
{
    const unsigned char *x = (const unsigned char *)a;
    const unsigned char *y = (const unsigned char *)b;
    if (!x || !y) { errno = EINVAL; return record_error(); }
    while (*x && ascii_lower(*x) == ascii_lower(*y)) { ++x; ++y; }
    dos_errno = 0;
    return (int16_t)ascii_lower(*x) - (int16_t)ascii_lower(*y);
}

DosFileStream *dos_fopen(char *path, char *mode)
{
    DosFileStream *stream;
    char host_path[32768];
    if (!path || !mode) { errno = EFAULT; record_error(); return NULL; }
    if (resolve_source_path(path, host_path, sizeof host_path) < 0) {
        record_error();
        return NULL;
    }
    stream = (DosFileStream *)malloc(sizeof *stream);
    if (!stream) { errno = ENOMEM; record_error(); return NULL; }
    stream->native = fopen(host_path, mode);
    if (!stream->native) {
        int saved = errno;
        free(stream);
        errno = saved;
        record_error();
        return NULL;
    }
    dos_errno = 0;
    return stream;
}

uint16_t dos_fread(void *buffer, uint16_t size, uint16_t count,
                   DosFileStream *stream)
{
    size_t n;
    if (!stream || !stream->native || (!buffer && size && count)) {
        errno = (!stream || !stream->native) ? EBADF : EFAULT;
        record_error();
        return 0;
    }
    n = fread(buffer, (size_t)size, (size_t)count, stream->native);
    if (ferror(stream->native)) record_error();
    else dos_errno = 0;
    return (uint16_t)n;
}

int16_t dos_fclose(DosFileStream *stream)
{
    if (!stream) { errno = EBADF; return record_error(); }
    if (fclose(stream->native) != 0) {
        int saved = errno;
        free(stream);
        errno = saved;
        return record_error();
    }
    free(stream);
    dos_errno = 0;
    return 0;
}

int16_t dos_files_set_root(const char *path)
{
    if (!sim_drive_set_root(path)) { errno = ENOENT; return record_error(); }
    dos_files_close_all();
    dos_errno = 0;
    return 0;
}

void dos_files_close_all(void)
{
    int i;
    for (i = DOS_HANDLE_FIRST; i < DOS_HANDLE_LIMIT; ++i) {
        if (handle_initialized[i]) {
            (void)host_close(host_handles[i]);
            handle_initialized[i] = 0;
            host_handles[i] = -1;
        }
    }
    dos_errno = 0;
}
