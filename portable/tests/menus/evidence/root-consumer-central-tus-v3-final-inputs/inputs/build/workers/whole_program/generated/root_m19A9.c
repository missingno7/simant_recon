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
 * Database record reader (root module, code frame 19A9; the object starts at 19A9:0008).
 * The three empty functions at 19A95-19A97 end the index module 1986 (CODEALIGN-1:
 * an MSC code segment is WORD aligned, so this object cannot start at the odd 19A95).
 * Win16 counterpart: DBRecall.  The DOS game opens the database read-only:
 * add/delete/pack are stubs that Punt.
 */







extern OpenDBRec  fd_50F6_3958[];
extern int16_t  WinPrintf(char  *format, ...);
extern void  Punt(char  *format, ...);
extern IndexEntry  *  FindIndex(int16_t db, int16_t id, int16_t kind);
extern void  f_19DC_02D9(int16_t file, void  *buffer, uint32_t count);
extern void  f_19DC_02FB(int16_t file, int32_t offset, void  *buffer, int32_t count);
extern char  *  f_171C_1B84(char  *handle);
extern void  f_171C_1BBA(char  *handle);
extern void  f_1B05_0008(char  *packed, int16_t length);
extern uint16_t  f_1B05_0046(char  *dest, uint16_t length);
extern char  *  f_2CFB_0002(uint32_t size, int16_t flags, char  *name);
extern void  f_2CFB_0007(char  *handle);
extern void  f_2CFB_002F(char  *handle, int16_t type);

int16_t  f_19A9_0008(char  *  *handle, int16_t  *size, int16_t object, int16_t type);

int16_t ( *g_36F2)(char  *  *handle, int16_t  *size, int16_t object, int16_t type) = f_19A9_0008;
char  *g_36F6[] = {
    "WIN", "WINLABEL", "BITMAP", "STR", "STRS", "PCM", "MENU", "CSRMASK",
    "CSRPIC", "HEXA", "TEXT", "FONT", "ANIM", "ANIMDLT", "SCREEN", "PALETTE",
    "INST", "CARD", "SONG", "CARDTITLE", "MIDI", "STYLE", "PATS",
    "", "", "", "", "", ""
};

int16_t  f_19A9_0008(char  *  *handle, int16_t  *size, int16_t object, int16_t type)
{
    return 0;
}

void  f_19A9_000B(int16_t ( *hook)(char  *  *handle, int16_t  *size, int16_t object, int16_t type))
{
    g_36F2 = hook;
}

char  *  DBRecall(int16_t db, int16_t object, int16_t type, int16_t  *size)
{
    IndexEntry  *entry;
    int16_t file;
    DBRecordHeader header;
    char name[64];
    uint16_t length;
    char  *handle;
    char  *p;
    uint16_t unpacked;
    char  *destHandle;
    char  *dest;

    entry = FindIndex(db, object, type);
    if (!entry)
        return 0L;
    file = fd_50F6_3958[db].file;
    f_19DC_02FB(file, entry->offset + 14, &header, 10L);
    length = header.size;
    if (type <= 22)
        dos_sprintf(name, "%s,%d", g_36F6[type], object);
    else
        dos_sprintf(name, "%d:%d", type, object);
    if (length == 0) {
        handle = f_2CFB_0002(2L, 0, name);
    } else if (entry->flags & 1) {
        if (entry->flags & 4) {
            handle = f_2CFB_0002((uint32_t)length + 2, 0, name);
            p = f_171C_1B84(handle);
            if (!handle)
                Punt("Couldn't allocate a buffer for DBRecall");
            f_19DC_02D9(file, p + 2, (uint32_t)length);
            *(int16_t  *)p = -1;
            length += 2;
            f_171C_1BBA(handle);
        } else {
            f_19DC_02D9(file, &unpacked, 2L);
            destHandle = f_2CFB_0002((uint32_t)unpacked, 1, name);
            handle = f_2CFB_0002((uint32_t)length + 2, 0, name);
            dest = f_171C_1B84(destHandle);
            f_19DC_02D9(file, p = f_171C_1B84(handle), (uint32_t)length - 2);
            f_1B05_0008(p, length - 2);
            if (f_1B05_0046(dest, unpacked) != unpacked) {
                dos_printf("\a\aDBRecall Unpack error!!! - object=%d, type=%d", object, type);
                WinPrintf("\a\aDBRecall Unpack error!!! - object=%d, type=%d", object, type);
            }
            f_171C_1BBA(handle);
            f_171C_1BBA(destHandle);
            f_2CFB_0007(handle);
            f_2CFB_002F(destHandle, 0);
            handle = destHandle;
            length = unpacked;
        }
    } else {
        handle = f_2CFB_0002((uint32_t)length, 0, name);
        if (!handle)
            Punt("Couldn't allocate a buffer for DBRecall");
        f_19DC_02D9(file, f_171C_1B84(handle), (uint32_t)length);
        f_171C_1BBA(handle);
    }
    *size = length;
    (*g_36F2)(&handle, size, object, type);
    return handle;
}

void  DBAdd(void)
{
    Punt("Attempt to ADD during a READ-ONLY run");
}

void  DBDelete(void)
{
    Punt("Attempt to DELETE during a READ-ONLY run");
}

void  DBPack(void)
{
    Punt("Attempt to PACK during a READ-ONLY run");
}

#pragma pack(pop)
