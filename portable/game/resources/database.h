#ifndef SIMANT_PORTABLE_GAME_RESOURCES_DATABASE_H
#define SIMANT_PORTABLE_GAME_RESOURCES_DATABASE_H

#include <stddef.h>
#include <stdint.h>

/* Read-only portable view of the original SimAnt .NDX/.DAT resource format.
 * Paths passed to portable_db_open are database roots without an extension.
 */
typedef enum PortableDbStatus {
    PORTABLE_DB_OK = 0,
    PORTABLE_DB_NOT_FOUND,
    PORTABLE_DB_IO_ERROR,
    PORTABLE_DB_FORMAT_ERROR,
    PORTABLE_DB_UNSUPPORTED_COMPRESSION,
    PORTABLE_DB_DECOMPRESSION_ERROR,
    PORTABLE_DB_OUT_OF_MEMORY
} PortableDbStatus;

typedef struct PortableDbIndexEntry {
    uint32_t data_offset; /* Relative to the first record after the 14-byte DAT header. */
    int16_t id;
    uint8_t kind;
    uint8_t flags;
} PortableDbIndexEntry;

typedef struct PortableDatabase {
    uint8_t *index_file;
    size_t index_file_size;
    uint8_t *data_file;
    size_t data_file_size;
    PortableDbIndexEntry *entries;
    size_t entry_count;
    char error[192];
} PortableDatabase;

typedef struct PortableDbRecord {
    int16_t id;
    uint8_t kind;
    uint8_t index_flags;
    uint32_t data_offset;
    uint8_t *data; /* Owned by the record; release with portable_db_record_free. */
    size_t size;
} PortableDbRecord;

/* Open `<root>.NDX` and `<root>.DAT`; no DOS handles or allocator are retained. */
PortableDbStatus portable_db_open(PortableDatabase *db, const char *root);
/* Open explicit paths, useful to callers that keep databases in separate directories. */
PortableDbStatus portable_db_open_files(PortableDatabase *db,
                                        const char *index_path,
                                        const char *data_path);
void portable_db_close(PortableDatabase *db);

/* Lookup is lower-bound ordered by unsigned kind byte, then signed int16 id.
 * `kind` remains signed16 to match the DOS caller ABI; values outside 0..255 miss.
 * The returned index entry is borrowed from db and stable until close.
 */
PortableDbStatus portable_db_lookup(const PortableDatabase *db,
                                    int16_t id,
                                    int16_t kind,
                                    const PortableDbIndexEntry **entry,
                                    size_t *insertion_index);

/* Load a record and apply the DOS database-level storage flags. The returned
 * ordinary byte buffer is independent of db and remains valid until freed.
 */
PortableDbStatus portable_db_load(PortableDatabase *db,
                                  int16_t id,
                                  int16_t kind,
                                  PortableDbRecord *record);
void portable_db_record_free(PortableDbRecord *record);
const char *portable_db_error(const PortableDatabase *db);
const char *portable_db_status_string(PortableDbStatus status);

/* Exact safe representation of FindIndex's final index[low] read. DOS could
 * inspect a one-past entry when lower_bound == count. This helper permits a
 * caller to supply that adjacent entry explicitly; it never reads out of bounds.
 * Empty tables still follow FindIndex's early-return and ignore lookahead.
 */
PortableDbStatus portable_db_find_index_compat(const PortableDbIndexEntry *entries,
                                                size_t count,
                                                const PortableDbIndexEntry *lookahead,
                                                int16_t id,
                                                int16_t kind,
                                                const PortableDbIndexEntry **entry,
                                                size_t *matched_index);

#endif
