#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/types/database.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/*
 * Database index layer (root module, code frame 1986).
 * Win16 counterpart: unit simtwo_9A86 (OpenIndex, CreateIndex, CloseIndex, FindIndex).
 */







extern OpenDBRec  fd_50F6_3958[];
extern int16_t  fd_50F6_3956;
extern IndexEntry  *  fd_50F6_3952;



extern void  Punt(char  *format, ...);
extern void  DosPunt(char  *message);
extern void  *  *  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern void  dos_free(void  *p);

void  OpenIndex(char  *path, int16_t db)
{
    char name[100];
    int16_t fd;
    uint16_t size;
    IndexEntry  *index;

    dos_sprintf(name, "%s.ndx", path);
    fd = fd_50F6_3958[db].indexFile = dos_open(name, 0x8002);
    if (fd <= 0)
        DosPunt("Index file missing");
    dos_read(fd, &fd_50F6_3958[db].indexHeader, 20);
    size = fd_50F6_3958[db].indexHeader.count << 3;
    index = fd_50F6_3958[db].index = *f_171C_13CA((int32_t)size, 0, name);
    if (index == 0L)
        Punt("Not enough memory to read index file in.");
    dos_read(fd, index, size);
    dos_close(fd);
}

void  CreateIndex(char  *name, int16_t db)
{
}

void  CloseIndex(int16_t db)
{
    if (fd_50F6_3958[db].index)
        dos_free(fd_50F6_3958[db].index);
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * FindIndex (index binary search) best draft (/Oeg): equal length, 17 bytes differ.
 * Residue: the original lays out the probe test as jg -> top=mid-1 (first), jne/jl ->
 * lastTop=mid+1 (last, falling into the loop test) and loads id before the entry
 * pointer for the id compare; every spelling tried (||/&& forms, negations, else-if,
 * continue/goto, operand order) compiles to the mirrored layout. */
IndexEntry  *  FindIndex(int16_t db, int16_t id, int16_t kind)
{
    int16_t mid;
    int16_t top;

    fd_50F6_3956 = 0;
    top = fd_50F6_3958[db].indexHeader.count - 1;
    if (top == -1)
        return 0L;
    while (fd_50F6_3956 <= top) {
        mid = (fd_50F6_3956 + top) / 2;
        fd_50F6_3952 = &fd_50F6_3958[db].index[mid];
        if (!(fd_50F6_3952->kind < kind || (fd_50F6_3952->kind == kind && fd_50F6_3952->id < id)))
            top = mid - 1;
        else
            fd_50F6_3956 = mid + 1;
    }
    fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];
    if (fd_50F6_3956 == fd_50F6_3958[db].indexHeader.count) return 0L;
    if (fd_50F6_3952->id == id && fd_50F6_3952->kind == kind)
        return fd_50F6_3952;
    return 0L;
}
/* SCAFFOLD END */

/* The index module's remaining write-side entry points (Win16 order after FindIndex:
 * DeleteCurrentIndex, AddIndex, DeleteIndex) are empty in the read-only DOS build, like
 * CreateIndex: three unreferenced retf at 1986:0235-0237 ending the object at 19A98. */
void  f_1986_0235(void)
{
}

void  f_1986_0236(void)
{
}

void  f_1986_0237(void)
{
}

#pragma pack(pop)
