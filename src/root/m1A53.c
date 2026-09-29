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
extern void far * far f_1A96_000C(int size);
extern char far * far f_1A96_01EC(int object, int kind, void far *table);
extern int far f_1A96_034E(int object, int kind, void far *table, char far *handle);
extern char far * far f_19A9_001D(int db, int object, int kind, int far *size);
extern void far f_171C_15A2(char far *handle, int type);
extern void far f_171C_13E4(char far *handle);
extern int far f_1A96_0159(char far *handle, void far *table, int far *object, int far *kind);
extern void far f_1A96_0421(int object, int kind, void far *table);
extern void far f_1A96_008C(int object, int kind, void far *table);
extern void far f_1A96_00EE(void far *table);
extern void far f_1A28_0149(int db);
extern void far f_19A9_031D(int db, int object, int kind);
extern void far f_19A9_0310(int db, int a4, int a5, int a6, int object, int kind, int a3);
extern int far fd_50F6_3B50[];

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
        db_cacheTable = f_1A96_000C(0);
    fd_50F6_3B50[db_numOfHandles] = OpenDB(name);
    handle = fd_50F6_3B50[db_numOfHandles++];
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
    handle = f_1A96_01EC(object, kind, db_cacheTable);
    if (!handle) {
        f_1B28_0068();
        for (i = 0; i < db_numOfHandles; i++) {
            if ((handle = f_19A9_001D(fd_50F6_3B50[i], object, kind, &size)) != 0L) {
                if (!f_1A96_034E(object, kind, db_cacheTable, handle))
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
    handle = f_1A96_01EC(object, kind, db_cacheTable);
    if (handle) {
        f_1A96_0421(object, kind, db_cacheTable);
        f_171C_13E4(handle);
    }
}

void far f_1A53_025F(char far *handle)
{
    int object;
    int kind;

    if (db_numOfHandles < 0)
        Punt("Purge attempt with database closed");
    if (f_1A96_0159(handle, db_cacheTable, &object, &kind)) {
        f_1A96_0421(object, kind, db_cacheTable);
        f_171C_13E4(handle);
    } else
        WinPrintf("\a\nPurge handle - handle not found!! handle=%p", handle);
}

void far f_1A53_02D5(char far *handle)
{
    f_171C_15A2(handle, 3);
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_1A53_02EB best draft: 99 vs 100 bytes.  Residue: the original pushes the lookup
 * handle's high word through AX (mov ax,[bp-2]; push ax) where this draft emits
 * push word ptr [bp-2]; everything else (DI for the low word, frame 4) matches. */
void far f_1A53_02EB(unsigned int object, int kind)
{
    char far *handle;

    if (object < 30000) {
        if (db_numOfHandles < 0)
            Punt("Purge attempt with database closed");
        handle = f_1A96_01EC(object, kind, db_cacheTable);
        if (handle)
            f_171C_15A2(handle, 3);
        else
            Punt("Release %d not in cache! ");
    }
}
/* SCAFFOLD END */

void far f_1A53_034F(int object, int kind)
{
    if (db_numOfHandles < 0)
        Punt("Unhook attempt with database closed");
    f_1A96_008C(object, kind, db_cacheTable);
}

void far f_1A53_037C(void)
{
    while (db_numOfHandles > 0) {
        --db_numOfHandles;
        f_1A28_0149(fd_50F6_3B50[db_numOfHandles]);
    }
    f_1A96_00EE(db_cacheTable);
    db_cacheTable = 0L;
}

void far f_1A53_03B6(int object, int kind, int a3, int a4, int a5, int a6)
{
    f_1B28_0068();
    f_19A9_031D(fd_50F6_3B50[0], object, kind);
    f_1A53_034F(object, kind);
    f_19A9_0310(fd_50F6_3B50[0], a4, a5, a6, object, kind, a3);
}

void far f_1A53_0404(int object, int kind, int a3, int a4, int a5, int a6)
{
    f_1B28_0068();
    f_1A53_034F(object, kind);
    f_19A9_0310(fd_50F6_3B50[0], a4, a5, a6, object, kind, a3);
}
