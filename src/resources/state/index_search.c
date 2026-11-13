/*
 * Defines the current database index entry pointer and its index state word. FindIndex updates
 * these objects while searching resource keys.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

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

IndexEntry far * far db_index_search_entry;
int far db_index_lower_bound;
