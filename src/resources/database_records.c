/*
 * Database record reader (root module, code frame 19A9; the object starts at 19A9:0008).
 * The three empty functions at 19A95-19A97 end the index module 1986 (CODEALIGN-1:
 * an MSC code segment is WORD aligned, so this object cannot start at the odd 19A95).
 * Win16 counterpart: DBRecall.  The DOS game opens the database read-only:
 * add/delete/pack are stubs that Punt.
 */

typedef struct {
    long offset;
    int id;
    unsigned char kind;
    unsigned char flags;
} IndexEntry;

typedef struct {
    int id;
    int type;
    int flags;
    int size;
    int extra;
} DBRecordHeader;

typedef struct {
    char name[0x50];
    IndexEntry far *index;
    char indexHeader[20];
    char dbHeader[14];
    int indexFile;
    int file;
    int dirty;
} OpenDBRec;

extern OpenDBRec far openDBData[];

extern int far sprintf(char far *buffer, char far *format, ...);
extern int far printf(char far *format, ...);
extern int far WinPrintf(char far *format, ...);
extern void far Punt(char far *format, ...);
extern IndexEntry far * far FindIndex(int db, int id, int kind);
extern void far db_read_at_cursor(int file, void far *buffer, unsigned long count);
extern void far db_read_cached_range(int file, long offset, void far *buffer, long count);
extern char far * far mem_Lock(char far *handle);
extern void far mem_Unlock(char far *handle);
extern void far UnpackInit(char far *packed, int length);
extern unsigned int far Unpack(char far *dest, unsigned int length);
extern char far * far f_2CFB_0002(unsigned long size, int flags, char far *name);
extern void far f_2CFB_0007(char far *handle);
extern void far f_2CFB_002F(char far *handle, int type);

int far f_19A9_0008(char far * far *handle, int far *size, int object, int type);

int (far *g_36F2)(char far * far *handle, int far *size, int object, int type) = f_19A9_0008;
char far *g_36F6[] = {
    "WIN", "WINLABEL", "BITMAP", "STR", "STRS", "PCM", "MENU", "CSRMASK",
    "CSRPIC", "HEXA", "TEXT", "FONT", "ANIM", "ANIMDLT", "SCREEN", "PALETTE",
    "INST", "CARD", "SONG", "CARDTITLE", "MIDI", "STYLE", "PATS",
    "", "", "", "", "", ""
};

int far f_19A9_0008(char far * far *handle, int far *size, int object, int type)
{
    return 0;
}

void far f_19A9_000B(int (far *hook)(char far * far *handle, int far *size, int object, int type))
{
    g_36F2 = hook;
}

char far * far DBRecall(int db, int object, int type, int far *size)
{
    IndexEntry far *entry;
    int file;
    DBRecordHeader header;
    char name[64];
    unsigned int length;
    char far *handle;
    char far *p;
    unsigned int unpacked;
    char far *destHandle;
    char far *dest;

    entry = FindIndex(db, object, type);
    if (!entry)
        return 0L;
    file = openDBData[db].file;
    db_read_cached_range(file, entry->offset + 14, &header, 10L);
    length = header.size;
    if (type <= 22)
        sprintf(name, "%s,%d", g_36F6[type], object);
    else
        sprintf(name, "%d:%d", type, object);
    if (length == 0) {
        handle = f_2CFB_0002(2L, 0, name);
    } else if (entry->flags & 1) {
        if (entry->flags & 4) {
            handle = f_2CFB_0002((unsigned long)length + 2, 0, name);
            p = mem_Lock(handle);
            if (!handle)
                Punt("Couldn't allocate a buffer for DBRecall");
            db_read_at_cursor(file, p + 2, (unsigned long)length);
            *(int far *)p = -1;
            length += 2;
            mem_Unlock(handle);
        } else {
            db_read_at_cursor(file, &unpacked, 2L);
            destHandle = f_2CFB_0002((unsigned long)unpacked, 1, name);
            handle = f_2CFB_0002((unsigned long)length + 2, 0, name);
            dest = mem_Lock(destHandle);
            db_read_at_cursor(file, p = mem_Lock(handle), (unsigned long)length - 2);
            UnpackInit(p, length - 2);
            if (Unpack(dest, unpacked) != unpacked) {
                printf("\a\aDBRecall Unpack error!!! - object=%d, type=%d", object, type);
                WinPrintf("\a\aDBRecall Unpack error!!! - object=%d, type=%d", object, type);
            }
            mem_Unlock(handle);
            mem_Unlock(destHandle);
            f_2CFB_0007(handle);
            f_2CFB_002F(destHandle, 0);
            handle = destHandle;
            length = unpacked;
        }
    } else {
        handle = f_2CFB_0002((unsigned long)length, 0, name);
        if (!handle)
            Punt("Couldn't allocate a buffer for DBRecall");
        db_read_at_cursor(file, mem_Lock(handle), (unsigned long)length);
        mem_Unlock(handle);
    }
    *size = length;
    (*g_36F2)(&handle, size, object, type);
    return handle;
}

void far DBAdd(void)
{
    Punt("Attempt to ADD during a READ-ONLY run");
}

void far DBDelete(void)
{
    Punt("Attempt to DELETE during a READ-ONLY run");
}

void far DBPack(void)
{
    Punt("Attempt to PACK during a READ-ONLY run");
}
