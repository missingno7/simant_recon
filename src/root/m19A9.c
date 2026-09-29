/*
 * Database record reader (root module, code frame 19A9).
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

extern OpenDBRec far fd_50F6_3958[];

extern int far sprintf(char far *buffer, char far *format, ...);
extern int far printf(char far *format, ...);
extern int far WinPrintf(char far *format, ...);
extern void far Punt(char far *format, ...);
extern IndexEntry far * far FindIndex(int db, int id, int kind);
extern void far f_19DC_02D9(int file, void far *buffer, long count);
extern void far f_19DC_02FB(int file, long offset, void far *buffer, long count);
extern char far * far f_171C_1B84(char far *handle);
extern void far f_171C_1BBA(char far *handle);
extern void far f_1B05_0008(char far *packed, int length);
extern unsigned int far f_1B05_0046(char far *dest, unsigned int length);
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

void far f_19A9_0005(void)
{
}

void far f_19A9_0006(void)
{
}

void far f_19A9_0007(void)
{
}

int far f_19A9_0008(char far * far *handle, int far *size, int object, int type)
{
    return 0;
}

void far f_19A9_000B(int (far *hook)(char far * far *handle, int far *size, int object, int type))
{
    g_36F2 = hook;
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * DBRecall (DBRecall) best draft (/Oeg): same instruction stream as the original except
 * (1) the frame is 0x6E vs 0x6A bytes (the original shares entry's high-word slot with the
 * unpack handle; every later home is 4 bytes lower), and (2) seven calls go through the
 * RTLink manager thunks 2CFB:0002 (jmp 171C:13CA), 2CFB:0007 (jmp 171C:13E4) and
 * 2CFB:002F (jmp 171C:15A2), which have no registered names; the f_2CFB_* externs below
 * are placeholders and cannot bind (tool gap, see REPORT.md). */
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
    file = fd_50F6_3958[db].file;
    f_19DC_02FB(file, entry->offset + 14, &header, 10L);
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
            p = f_171C_1B84(handle);
            if (!handle)
                Punt("Couldn't allocate a buffer for DBRecall");
            f_19DC_02D9(file, p + 2, (unsigned long)length);
            *(int far *)p = -1;
            length += 2;
            f_171C_1BBA(handle);
        } else {
            f_19DC_02D9(file, &unpacked, 2L);
            destHandle = f_2CFB_0002((unsigned long)unpacked, 1, name);
            handle = f_2CFB_0002((unsigned long)length + 2, 0, name);
            dest = f_171C_1B84(destHandle);
            f_19DC_02D9(file, p = f_171C_1B84(handle), (unsigned long)length - 2);
            f_1B05_0008(p, length - 2);
            if (f_1B05_0046(dest, unpacked) != unpacked) {
                printf("\a\aDBRecall Unpack error!!! - object=%d, type=%d", object, type);
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
        handle = f_2CFB_0002((unsigned long)length, 0, name);
        if (!handle)
            Punt("Couldn't allocate a buffer for DBRecall");
        f_19DC_02D9(file, f_171C_1B84(handle), (unsigned long)length);
        f_171C_1BBA(handle);
    }
    *size = length;
    (*g_36F2)(&handle, size, object, type);
    return handle;
}
/* SCAFFOLD END */

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
