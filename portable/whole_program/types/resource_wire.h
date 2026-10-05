#ifndef SIMANT_NATIVE_RESOURCE_WIRE_H
#define SIMANT_NATIVE_RESOURCE_WIRE_H

#include <stddef.h>
#include <stdint.h>

/* Read-only portable view of the original SimAnt .NDX/.DAT resource format.
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
    uint8_t *data; /* Owned byte buffer for this record view. */
    size_t size;
} PortableDbRecord;


#endif
