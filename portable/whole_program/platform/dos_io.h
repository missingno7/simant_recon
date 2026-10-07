/* Fixed-width DOS low-level file API for mechanically converted whole-program TUs.
 * These functions never expose a host CRT descriptor as a DOS `int`. */
#ifndef SIMANT_WHOLE_DOS_IO_H
#define SIMANT_WHOLE_DOS_IO_H
#include <stdint.h>
#include "dos_files.h"

typedef struct DosFileStream DosFileStream;

enum {
    DOS_O_WRONLY = 0x0001,
    DOS_O_RDWR = 0x0002,
    DOS_O_APPEND = 0x0008,
    DOS_O_NOINHERIT = 0x0080,
    DOS_O_CREAT = 0x0100,
    DOS_O_TRUNC = 0x0200,
    DOS_O_EXCL = 0x0400,
    DOS_O_TEXT = 0x4000,
    DOS_O_BINARY = 0x8000
};

/* MSC's _fmode default is text mode; binary source callers request 0x8000. */
extern int16_t dos_fmode;
int16_t dos_open(char *path, int16_t flags, ...);
int16_t dos_read(int16_t fd, void *buffer, uint16_t count);
int16_t dos_write(int16_t fd, void *buffer, uint16_t count);
int32_t dos_lseek(int16_t fd, int32_t offset, int16_t origin);
int16_t dos_close(int16_t fd);
int16_t dos_access(char *path, int16_t mode);
int16_t dos_chdir(char *path);
char *dos_getcwd(char *buffer, int16_t size);
int16_t dos_remove(char *path);
int16_t dos_stricmp(char *a, char *b);
DosFileStream *dos_fopen(char *path, char *mode);
uint16_t dos_fread(void *buffer, uint16_t size, uint16_t count,
                   DosFileStream *stream);
int16_t dos_fclose(DosFileStream *stream);

/* Test/host lifecycle hooks. The asset directory is mounted as virtual C:\\;
 * source paths are resolved there without changing process CWD. */
int16_t dos_files_set_root(const char *path);
void dos_files_close_all(void);

#endif
