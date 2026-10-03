#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/*
 * Database file reader with an EMS page cache (root module, code frame 19DC).
 * No direct Win16 counterpart (DOS-only EMS layer).
 */

typedef struct {
    uint16_t age;
    int16_t file;
    int16_t page;
} EmsSlot;

extern int8_t  fd_55B3_360C;
extern int16_t  fd_55B3_3612;
extern char  *  fd_55B3_360E;
extern char  *  fd_50F6_3B48;
extern EmsSlot  *  *  fd_50F6_3B4C;

extern void  Punt(char  *format, ...);
extern void  DosPunt(char  *message);
extern int16_t  atexit(void ( *func)(void));


extern void  f_195A_001D(void);
extern void  f_195A_0035(void);
extern int16_t  f_195A_004B(int16_t pages);
extern void  f_195A_0062(int16_t handle, int16_t logical, int16_t physical);
extern void  f_195A_007D(int16_t handle);
extern void  f_195A_01CB(int16_t handle, char  *name);
extern int16_t  f_195A_0260(void);
extern EmsSlot  *  *  f_2CFB_0002(int32_t size, int16_t flags, char  *name);

void  f_19DC_04B9(void);

static int16_t s_8C74;
int16_t g_389C = 0;
int16_t g_389E = 0;
int16_t g_38A0 = 0;

void  f_19DC_0008(void)
{
    if (g_389C)
        f_195A_007D(g_389C);
}

int16_t  f_19DC_001A(int32_t size)
{
    int16_t i;
    EmsSlot  *slot;
    int16_t pages;
    int16_t avail;

    if (g_389C)
        return 1;
    if (!f_195A_0260() || fd_55B3_360C < 0x40)
        return 0;
    f_195A_0035();
    pages = (int16_t)((size + 0x3FFF) >> 14);
    avail = fd_55B3_3612 - g_38A0;
    g_389E = avail > pages ? pages : avail;
    if (g_389E < 8) {
        g_389E = 0;
        return 0;
    }
    f_195A_001D();
    g_389C = f_195A_004B(g_389E);
    f_195A_01CB(g_389C, "DBEMSXXX");
    fd_50F6_3B48 = fd_55B3_360E - 0x4000;
    fd_50F6_3B4C = f_2CFB_0002((int32_t)g_389E * 6, 0, "DBEMSLIST");
    slot = *fd_50F6_3B4C;
    for (i = 0; i < g_389E; i++) {
        slot->age = 0;
        slot->file = slot->page = -1;
    }
    f_195A_0062(g_389C, 0, 3);
    atexit(f_19DC_0008);
    return 1;
}

int16_t g_38B6 = -1;
int16_t g_38B8 = -1;
int16_t g_38BA = -1;

char  *  f_19DC_0148(int16_t file, int16_t page)
{
    EmsSlot  *slot;
    int16_t i;
    int16_t freeSlot;
    int16_t found;
    uint16_t oldest;
    int16_t oldestSlot;

    freeSlot = -1;
    found = 0;
    oldest = 0;
    if (file == g_38B8 && page == g_38BA)
        return fd_50F6_3B48;
    slot = *fd_50F6_3B4C;
    for (i = 0; i < g_389E; i++, slot++) {
        if (slot->file == -1) {
            freeSlot = i;
            continue;
        }
        if (slot->file == file && slot->page == page) {
            f_195A_0062(g_389C, i, 3);
            g_38B6 = i;
            slot->age = 0;
            found = 1;
        }
        if (slot->age < 0xFFFF)
            slot->age++;
        if (slot->age > oldest) {
            oldest = slot->age;
            oldestSlot = i;
        }
    }
    if (!found) {
        i = freeSlot;
        if (i == -1)
            i = oldestSlot;
        slot = &(*fd_50F6_3B4C)[i];
        slot->file = file;
        slot->page = page;
        f_195A_0062(g_389C, i, 3);
        g_38B6 = i;
        slot->age = 0;
        while ((int16_t)dos_lseek(file, (int32_t)page << 14, 0) == -1)
            f_19DC_04B9();
        for (;;) {
            if (dos_read(file, fd_50F6_3B48, 0x4000) != -1)
                break;
            f_19DC_04B9();
        }
    }
    g_38B8 = file;
    g_38BA = page;
    return fd_50F6_3B48;
}


static int32_t s_8C76;

int16_t  f_19DC_02FB(int16_t file, int32_t offset, char  *buffer, int32_t count);

void  f_19DC_02D9(int16_t file, char  *buffer, int32_t count)
{
    f_19DC_02FB(file, s_8C76, buffer, count);
}

int16_t g_390C = 0;

#define CHECK_FILE() if (s_8C74 != file) Punt("Handle mismatch")

int16_t  f_19DC_02FB(int16_t file, int32_t offset, char  *buffer, int32_t count)
{
    int16_t page;
    uint16_t off;
    uint16_t chunk;
    uint16_t done;
    uint16_t left;
    char  *src;

    s_8C76 = offset + count;
    s_8C74 = file;
    if (count == 0L)
        return 0;
    if (g_390C || !f_19DC_001A(500000L))
        goto plain;
    page = (int16_t)(offset >> 14);
    off = (uint16_t)offset & 0x3FFF;
    chunk = 0x4000 - off;
    if (chunk > count)
        chunk = (uint16_t)count;
    CHECK_FILE();
    _fmemcpy(buffer, f_19DC_0148(file, page) + off, chunk);
    page++;
    done = chunk;
    left = (uint16_t)count - chunk;
    while (left >= 0x4000) {
        CHECK_FILE();
        src = f_19DC_0148(file, page);
        CHECK_FILE();
        _fmemcpy(buffer + done, src, 0x4000);
        done += 0x4000;
        page++;
        left -= 0x4000;
    }
    if (left) {
        CHECK_FILE();
        src = f_19DC_0148(file, page);
        CHECK_FILE();
        _fmemcpy(buffer + done, src, left);
    }
    return;
plain:
    g_390C = 1;
    dos_lseek(file, offset, 0);
    return dos_read(file, buffer, (uint16_t)count);
}

void  f_19DC_04B9(void)
{
    DosPunt("Database error");
}

#pragma pack(pop)
