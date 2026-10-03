/* Functional FAR_BSS owner for the two independent FindIndex state objects. */
typedef union IndexKey {
    char far *data;               /* m1986 view of the first four index bytes */
    long offset;                  /* m19A9 view used to read the .DAT record */
} IndexKey;

typedef struct IndexEntry {
    IndexKey key;
    int id;
    unsigned char kind;
    unsigned char flags;
} IndexEntry;

IndexEntry far * far fd_50F6_3952;
int far fd_50F6_3956;
