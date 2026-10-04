/* Source-functional FAR_BSS owner for the four successful database slots. */
typedef union IndexKey {
    char far *data;               /* m1986 view of the first four index bytes */
    long offset;                  /* m19A9 view used for the .DAT record offset */
} IndexKey;

typedef struct IndexEntry {
    IndexKey key;
    int id;
    unsigned char kind;
    unsigned char flags;
} IndexEntry;

typedef struct IndexHeader {
    int count;
    int spare;
    long stat1;
    long stat2;
    long stat3;
    int field8;
    int field9;
} IndexHeader;

typedef struct DBHeader {
    long magic;
    int count;
    long freeBytes;
    long wastedBytes;
} DBHeader;

typedef struct OpenDBIndexView {
    IndexEntry far *index;
    IndexHeader header;
} OpenDBIndexView;

typedef union OpenDBIndexArea {
    OpenDBIndexView typed;
    char bytes[0x18];           /* m1A28/m19A9 raw 24-byte view */
} OpenDBIndexArea;

typedef union OpenDBIndexFileView {
    int indexFile;
    char bytes[2];               /* m1A28's pad[2] view */
} OpenDBIndexFileView;

typedef struct OpenDBRec {
    char name[0x50];
    OpenDBIndexArea indexArea;
    DBHeader dbHeader;
    OpenDBIndexFileView indexFileArea;
    int file;
    int dirty;
} OpenDBRec;

OpenDBRec far fd_50F6_3958[4];
int far db_handles[4];
