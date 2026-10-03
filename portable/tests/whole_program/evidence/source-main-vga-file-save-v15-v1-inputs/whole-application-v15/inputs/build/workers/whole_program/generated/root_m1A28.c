#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/types/database.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/crt_abi.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/*
 * Database file layer (root module, code frame 1A28).
 * Win16 counterpart: OpenDB / DosPunt (simtwo).
 */





extern OpenDBRec  fd_50F6_3958[];
extern int16_t  dos_errno;
extern char  *  sim_sys_errlist[];







extern void  Punt(char  *format, ...);
extern void  OpenIndex(char  *name, int16_t db);
extern void  CreateIndex(char  *name, int16_t db);
extern void  CloseIndex(int16_t db);

static int16_t s_394E = 0;

int16_t  GetFreeHandle(void);
void  CopyRootName(char  *dst, char  *src);
void  DosPunt(char  *message);

int16_t  OpenDB(char  *name)
{
    char path[100];
    int16_t db;

    db = GetFreeHandle();
    if (db == -1) Punt("Out of handles.");
    CopyRootName(fd_50F6_3958[db].name, name);
    dos_sprintf(path, "%s.dat", fd_50F6_3958[db].name);
    if ((fd_50F6_3958[db].file = dos_open(path, 0x8002)) <= 0) {
        if ((fd_50F6_3958[db].file = dos_open(path, 0x8102, 0x180)) <= 0)
            DosPunt("Cannot create data file.");
        fd_50F6_3958[db].header.magic = 0x12345678L;
        fd_50F6_3958[db].header.freeBytes = 0L;
        fd_50F6_3958[db].header.wastedBytes = 0L;
        CreateIndex(fd_50F6_3958[db].name, db);
        fd_50F6_3958[db].dirty = 1;
    } else {
        dos_read(fd_50F6_3958[db].file, &fd_50F6_3958[db].header, 14);
        OpenIndex(fd_50F6_3958[db].name, db);
        fd_50F6_3958[db].dirty = 0;
    }
    return db;
}

void  f_1A28_0148(void)
{
}

void  CloseDB(int16_t db)
{
    int16_t file;

    file = fd_50F6_3958[db].file;
    if (fd_50F6_3958[db].dirty) {
        dos_lseek(file, 0L, 0);
        dos_write(file, &fd_50F6_3958[db].header, 14);
    }
    dos_close(file);
    CloseIndex(db);
    fd_50F6_3958[db].name[0] = 0;
}

void  CopyRootName(char  *dst, char  *src)
{
    char  *dot;

    _fstrncpy(dst, src, 79);
    dst[79] = 0;
    while (*dst == '.')
        dst++;
    if ((dot = _fstrrchr(dst, '.')) != 0L && _fstrrchr(dst, '\\') < dot)
        *dot = 0;
}

int16_t  GetFreeHandle(void)
{
    int16_t i;

    if (!s_394E) {
        s_394E = 1;
        for (i = 0; i < 4; i++)
            fd_50F6_3958[i].name[0] = 0;
    }
    for (i = 0; i < 4; i++)
        if (fd_50F6_3958[i].name[0] == 0)
            return i;
    return -1;
}

void  DosPunt(char  *message)
{
    if (dos_errno == 24)
        Punt("Too many files open.  You need a statement 'FILES=12' in\nyour config.sys file.  Please refer to your dos manual\nfor more information.");
    Punt("%s\nDos error: %d: %s", message, dos_errno, sim_sys_errlist[dos_errno]);
}

#pragma pack(pop)
