/*
 * Database file layer (root module, code frame 1A28).
 * Win16 counterpart: OpenDB / DosPunt (simtwo).
 */

typedef struct {
    long magic;
    int count;
    long freeBytes;
    long wastedBytes;
} DBHeader;

typedef struct {
    char name[0x50];
    char index[0x18];
    DBHeader header;
    char pad[2];
    int file;
    int dirty;
} OpenDBRec;

extern OpenDBRec far fd_50F6_3958[];
extern int near errno;
extern char far * near sys_errlist[];

extern int far sprintf(char far *buffer, char far *format, ...);
extern int far open(char far *path, int flags, ...);
extern int far read(int fd, void far *buffer, unsigned int count);
extern int far write(int fd, void far *buffer, unsigned int count);
extern int far close(int fd);
extern long far lseek(int fd, long offset, int origin);
extern char far * far _fstrncpy(char far *dst, char far *src, unsigned int n);
extern char far * far _fstrrchr(char far *s, int c);
extern void far Punt(char far *format, ...);
extern void far OpenIndex(char far *name, int db);
extern void far CreateIndex(char far *name, int db);
extern void far CloseIndex(int db);

static int s_394E = 0;

int far f_1A28_0224(void);
void far f_1A28_01B4(char far *dst, char far *src);
void far DosPunt(char far *message);

int far OpenDB(char far *name)
{
    char path[100];
    int db;

    db = f_1A28_0224();
    if (db == -1)
        Punt("Out of handles.");
    f_1A28_01B4(fd_50F6_3958[db].name, name);
    sprintf(path, "%s.dat", fd_50F6_3958[db].name);
    if ((fd_50F6_3958[db].file = open(path, 0x8002)) <= 0) {
        if ((fd_50F6_3958[db].file = open(path, 0x8102, 0x180)) <= 0)
            DosPunt("Cannot create data file.");
        fd_50F6_3958[db].header.magic = 0x12345678L;
        fd_50F6_3958[db].header.freeBytes = 0L;
        fd_50F6_3958[db].header.wastedBytes = 0L;
        CreateIndex(fd_50F6_3958[db].name, db);
        fd_50F6_3958[db].dirty = 1;
    } else {
        read(fd_50F6_3958[db].file, &fd_50F6_3958[db].header, 14);
        OpenIndex(fd_50F6_3958[db].name, db);
        fd_50F6_3958[db].dirty = 0;
    }
    return db;
}

void far f_1A28_0148(void)
{
}

void far CloseDB(int db)
{
    int file;

    file = fd_50F6_3958[db].file;
    if (fd_50F6_3958[db].dirty) {
        lseek(file, 0L, 0);
        write(file, &fd_50F6_3958[db].header, 14);
    }
    close(file);
    CloseIndex(db);
    fd_50F6_3958[db].name[0] = 0;
}

void far f_1A28_01B4(char far *dst, char far *src)
{
    char far *dot;

    _fstrncpy(dst, src, 79);
    dst[79] = 0;
    while (*dst == '.')
        dst++;
    if ((dot = _fstrrchr(dst, '.')) != 0L && _fstrrchr(dst, '\\') < dot)
        *dot = 0;
}

int far f_1A28_0224(void)
{
    int i;

    if (!s_394E) {
        s_394E = 1;
        for (i = 0; i < 4; i++)
            fd_50F6_3958[i].name[0] = 0;
    }
    for (i = 0; i < 4; i++)
        if (fd_50F6_3958[i].name[0] == 0)
            return i;
    return -1;
}

void far DosPunt(char far *message)
{
    if (errno == 24)
        Punt("Too many files open.  You need a statement 'FILES=12' in\nyour config.sys file.  Please refer to your dos manual\nfor more information.");
    Punt("%s\nDos error: %d: %s", message, errno, sys_errlist[errno]);
}
