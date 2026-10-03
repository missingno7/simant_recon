/*
 * Object database front end (root module, code frame 1A53).
 * Win16 counterpart: unit simtwo_8176 (db_Exists .. db_CloseDataBase).
 * DOS memory handles are far pointers.
 */

extern int far sprintf(char far *buffer, char far *format, ...);
extern int far access(char far *path, int mode);
extern void far Punt(char far *format, ...);
extern int far WinPrintf(char far *format, ...);
extern int far OpenDB(char far *name);
extern void far f_1B28_0068(void);
extern void far * far ch_CreateTable(int size);
extern char far * far ch_LookUpId(int object, int kind, void far *table);
extern int far ch_AddEntry(int object, int kind, void far *table, char far *handle);
extern char far * far DBRecall(int db, int object, int kind, int far *size);
extern void far f_171C_15A2(char far *handle, int type);
extern void far f_171C_13E4(char far *handle);
extern int far ch_LookUpHandle(char far *handle, void far *table, int far *object, int far *kind);
extern void far ch_DeleteEntry(int object, int kind, void far *table);
extern void far ch_RemoveEntry(int object, int kind, void far *table);
extern void far ch_PurgeCache(void far *table);
extern void far CloseDB(int db);
extern void far DBDelete(int db, int object, int kind);
extern void far DBAdd(int db, int a4, int a5, int a6, int object, int kind, int a3);
extern int far db_handles[];

int db_numOfHandles = 0;
void far *db_cacheTable = 0L;
int db_closed = 1;

int far db_Exists(char far *name)
{
    char path[100];

    sprintf(path, "%s.dat", name);
    if (access(path, 0) != -1)
        return 1;
    return 0;
}

int far db_SetDataBase(char far *name)
{
    int handle;

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

char far * far db_LoadObject(int object, int kind);

char far * far f_1A53_00BA(int object, int kind)
{
    char far *handle;

    handle = db_LoadObject(object, kind);
    if (handle)
        f_171C_15A2(handle, 1);
    return handle;
}

char far * far f_1A53_00F0(int object, int kind, int type)
{
    char far *handle;

    handle = db_LoadObject(object, kind);
    if (handle)
        f_171C_15A2(handle, type);
    return handle;
}

char far * far db_LoadObject(int object, int kind)
{
    char far *handle;
    int size;
    int i;

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

void far db_PurgeObject(int object, int kind)
{
    char far *handle;

    if (db_numOfHandles < 0)
        Punt("Purge attempt with database closed");
    handle = ch_LookUpId(object, kind, db_cacheTable);
    if (handle) {
        ch_DeleteEntry(object, kind, db_cacheTable);
        f_171C_13E4(handle);
    }
}

void far db_PurgeHandle(char far *handle)
{
    int object;
    int kind;

    if (db_numOfHandles < 0)
        Punt("Purge attempt with database closed");
    if (ch_LookUpHandle(handle, db_cacheTable, &object, &kind)) {
        ch_DeleteEntry(object, kind, db_cacheTable);
        f_171C_13E4(handle);
    } else
        WinPrintf("\a\nPurge handle - handle not found!! handle=%p", handle);
}

void far db_ReleaseHandle(char far *handle)
{
    f_171C_15A2(handle, 3);
}

void far db_ReleaseObject(unsigned int object, int kind)
{
    char far *handle;

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

void far db_UnhookObject(int object, int kind)
{
    if (db_numOfHandles < 0)
        Punt("Unhook attempt with database closed");
    ch_RemoveEntry(object, kind, db_cacheTable);
}

void far db_CloseDataBase(void)
{
    while (db_numOfHandles > 0) {
        --db_numOfHandles;
        CloseDB(db_handles[db_numOfHandles]);
    }
    ch_PurgeCache(db_cacheTable);
    db_cacheTable = 0L;
}

void far db_ReplaceObject(int object, int kind, int a3, int a4, int a5, int a6)
{
    f_1B28_0068();
    DBDelete(db_handles[0], object, kind);
    db_UnhookObject(object, kind);
    DBAdd(db_handles[0], a4, a5, a6, object, kind, a3);
}

void far db_SaveObject(int object, int kind, int a3, int a4, int a5, int a6)
{
    f_1B28_0068();
    db_UnhookObject(object, kind);
    DBAdd(db_handles[0], a4, a5, a6, object, kind, a3);
}
