/*
 * Database index layer (root module, code frame 1986).
 * Win16 counterpart: unit simtwo_9A86 (OpenIndex, CreateIndex, CloseIndex, FindIndex).
 */

typedef struct {
    char far *data;
    int id;
    unsigned char kind;
    unsigned char spare;
} IndexEntry;

typedef struct {
    int count;
    int spare;
    long stat1;
    long stat2;
    long stat3;
    int field8;
    int field9;
} IndexHeader;

typedef struct {
    char name[0x50];
    IndexEntry far *index;
    IndexHeader indexHeader;
    char dbHeader[14];
    int indexFile;
    int file;
    int dirty;
} OpenDBRec;

extern OpenDBRec far fd_50F6_3958[];
extern int far fd_50F6_3956;
extern IndexEntry far * far fd_50F6_3952;

IndexEntry far * far FindIndex(int db, int id, int kind)
{
    int mid;
    int top;

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
