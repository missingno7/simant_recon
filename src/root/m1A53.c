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

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * db_LoadObject best draft: 216 vs 218 bytes.  Residue: the original keeps the lookup
 * handle's high word in the DBRecall result's home ([bp-8]) and reloads it into DI for the
 * final mem_SetType/return; this draft gives it a separate home.  Declaration order is
 * irrelevant (24 permutations tried). */
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
/* SCAFFOLD END */
