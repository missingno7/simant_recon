#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/*
 * Object database front end (root module, code frame 1A53).
 * Win16 counterpart: unit simtwo_8176 (db_Exists .. db_CloseDataBase).
 * DOS memory handles are far pointers.
 */

extern void  Punt(char  *format, ...);
extern int16_t  WinPrintf(char  *format, ...);
extern int16_t  OpenDB(char  *name);
extern void  f_1B28_0068(void);
extern void  *  ch_CreateTable(int16_t size);
extern char  *  ch_LookUpId(int16_t object, int16_t kind, void  *table);
extern int16_t  ch_AddEntry(int16_t object, int16_t kind, void  *table, char  *handle);
extern char  *  DBRecall(int16_t db, int16_t object, int16_t kind, int16_t  *size);
extern void  f_171C_15A2(char  *handle, int16_t type);
extern void  f_171C_13E4(char  *handle);
extern int16_t  ch_LookUpHandle(char  *handle, void  *table, int16_t  *object, int16_t  *kind);
extern void  ch_DeleteEntry(int16_t object, int16_t kind, void  *table);
extern void  ch_RemoveEntry(int16_t object, int16_t kind, void  *table);
extern void  ch_PurgeCache(void  *table);
extern void  CloseDB(int16_t db);
extern void  DBDelete(int16_t db, int16_t object, int16_t kind);
extern void  DBAdd(int16_t db, int16_t a4, int16_t a5, int16_t a6, int16_t object, int16_t kind, int16_t a3);


int16_t db_numOfHandles = 0;
void  *db_cacheTable = 0L;
int16_t db_closed = 1;

int16_t  db_Exists(char  *name)
{
    char path[100];

    dos_sprintf(path, "%s.dat", name);
    if (dos_access(path, 0) != -1)
        return 1;
    return 0;
}

int16_t  db_SetDataBase(char  *name)
{
    int16_t handle;

    db_closed = 0;
    if (db_numOfHandles)
        f_1B28_0068();
    if (db_cacheTable == 0L)
        db_cacheTable = ch_CreateTable(0);
    db_handles[db_numOfHandles] = OpenDB(name);
    handle = db_handles[db_numOfHandles++];
    if (handle < 0)
        Punt("Cannot open database %s", name);
    return handle;
}

char  *  db_LoadObject(int16_t object, int16_t kind);

char  *  f_1A53_00BA(int16_t object, int16_t kind)
{
    char  *handle;

    handle = db_LoadObject(object, kind);
    if (handle)
        f_171C_15A2(handle, 1);
    return handle;
}

char  *  f_1A53_00F0(int16_t object, int16_t kind, int16_t type)
{
    char  *handle;

    handle = db_LoadObject(object, kind);
    if (handle)
        f_171C_15A2(handle, type);
    return handle;
}

char  *  db_LoadObject(int16_t object, int16_t kind)
{
    char  *handle;
    int16_t size;
    int16_t i;

    if (db_numOfHandles <= 0)
        Punt("Load attempt with database closed");
    handle = ch_LookUpId(object, kind, db_cacheTable);
    if (!handle) {
        f_1B28_0068();
        for (i = 0; i < db_numOfHandles; i++) {
            if ((handle = DBRecall(db_handles[i], object, kind, &size)) != 0L) {
                if (!ch_AddEntry(object, kind, db_cacheTable, handle))
                    Punt("Cache table full, can't load object");
                return handle;
            }
        }
        WinPrintf("Memory full or object missing - cannot load object:id=%d, type=%d", object, kind);
        return 0L;
    }
    f_171C_15A2(handle, 0);
    return handle;
}

void  db_PurgeObject(int16_t object, int16_t kind)
{
    char  *handle;

    if (db_numOfHandles < 0)
        Punt("Purge attempt with database closed");
    handle = ch_LookUpId(object, kind, db_cacheTable);
    if (handle) {
        ch_DeleteEntry(object, kind, db_cacheTable);
        f_171C_13E4(handle);
    }
}

void  db_PurgeHandle(char  *handle)
{
    int16_t object;
    int16_t kind;

    if (db_numOfHandles < 0)
        Punt("Purge attempt with database closed");
    if (ch_LookUpHandle(handle, db_cacheTable, &object, &kind)) {
        ch_DeleteEntry(object, kind, db_cacheTable);
        f_171C_13E4(handle);
    } else
        WinPrintf("\a\nPurge handle - handle not found!! handle=%p", handle);
}

void  db_ReleaseHandle(char  *handle)
{
    f_171C_15A2(handle, 3);
}

void  db_ReleaseObject(uint16_t object, int16_t kind)
{
    char  *handle;

    if (object < 30000) {
        if (db_numOfHandles < 0)
            Punt("Purge attempt with database closed");
        handle = ch_LookUpId(object, kind, db_cacheTable);
        if (handle)
            f_171C_15A2(handle, 3);
        else
            Punt("Release %d not in cache! ");
    }
}

void  db_UnhookObject(int16_t object, int16_t kind)
{
    if (db_numOfHandles < 0)
        Punt("Unhook attempt with database closed");
    ch_RemoveEntry(object, kind, db_cacheTable);
}

void  db_CloseDataBase(void)
{
    while (db_numOfHandles > 0) {
        --db_numOfHandles;
        CloseDB(db_handles[db_numOfHandles]);
    }
    ch_PurgeCache(db_cacheTable);
    db_cacheTable = 0L;
}

void  db_ReplaceObject(int16_t object, int16_t kind, int16_t a3, int16_t a4, int16_t a5, int16_t a6)
{
    f_1B28_0068();
    DBDelete(db_handles[0], object, kind);
    db_UnhookObject(object, kind);
    DBAdd(db_handles[0], a4, a5, a6, object, kind, a3);
}

void  db_SaveObject(int16_t object, int16_t kind, int16_t a3, int16_t a4, int16_t a5, int16_t a6)
{
    f_1B28_0068();
    db_UnhookObject(object, kind);
    DBAdd(db_handles[0], a4, a5, a6, object, kind, a3);
}

#pragma pack(pop)
