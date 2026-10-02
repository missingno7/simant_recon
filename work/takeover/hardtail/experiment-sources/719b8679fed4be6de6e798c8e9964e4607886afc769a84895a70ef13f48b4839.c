extern int idscan_pad0;
extern int idscan_pad1;
extern int idscan_pad2;
extern int idscan_pad3;
extern int idscan_pad4;
extern int idscan_pad5;
extern int idscan_pad6;
extern int idscan_pad7;
extern int idscan_pad8;
extern int idscan_pad9;
extern int idscan_pad10;
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

extern int far sprintf(char far *buffer, char far *format, ...);
extern int far open(char far *path, int flags, ...);
extern int far read(int fd, void far *buffer, unsigned int count);
extern int far close(int fd);
extern void far Punt(char far *format, ...);
extern void far DosPunt(char far *message);
extern void far * far * far f_171C_13CA(long size, int flags, char far *name);
extern void far free(void far *p);

void far OpenIndex(char far *path, int db)
{
    char name[100];
    int fd;
    unsigned int size;
    IndexEntry far *index;

    sprintf(name, "%s.ndx", path);
    fd = fd_50F6_3958[db].indexFile = open(name, 0x8002);
    if (fd <= 0)
        DosPunt("Index file missing");
    read(fd, &fd_50F6_3958[db].indexHeader, 20);
    size = fd_50F6_3958[db].indexHeader.count << 3;
    index = fd_50F6_3958[db].index = *f_171C_13CA((long)size, 0, name);
    if (index == 0L)
        Punt("Not enough memory to read index file in.");
    read(fd, index, size);
    close(fd);
}

void far CreateIndex(char far *name, int db)
{
}

void far CloseIndex(int db)
{
    if (fd_50F6_3958[db].index)
        free(fd_50F6_3958[db].index);
}

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
    if (fd_50F6_3952->id == id && fd_50F6_3952->kind == kind)
        return fd_50F6_3952;
    return 0L;
}

/* The index module's remaining write-side entry points (Win16 order after FindIndex:
 * DeleteCurrentIndex, AddIndex, DeleteIndex) are empty in the read-only DOS build, like
 * CreateIndex: three unreferenced retf at 1986:0235-0237 ending the object at 19A98. */
void far f_1986_0235(void)
{
}

void far f_1986_0236(void)
{
}

void far f_1986_0237(void)
{
}
