#include "database.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    NDX_HEADER_BYTES = 20,
    NDX_RESERVED_ENTRIES = 32,
    DAT_HEADER_BYTES = 14,
    DAT_RECORD_HEADER_BYTES = 10,
    DAT_TRAILER_BYTES = 256,
    LZSS_RING_BYTES = 4096,
    LZSS_RING_MASK = 4095,
    LZSS_INITIAL_POS = 4096 - 18,
    LZSS_MAX_INPUT = 0x7fff
};

typedef struct RecordExtent {
    uint64_t begin;
    uint64_t end;
} RecordExtent;

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t read_le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int extent_compare(const void *a, const void *b)
{
    const RecordExtent *ea = (const RecordExtent *)a;
    const RecordExtent *eb = (const RecordExtent *)b;
    if (ea->begin < eb->begin) return -1;
    if (ea->begin > eb->begin) return 1;
    if (ea->end < eb->end) return -1;
    if (ea->end > eb->end) return 1;
    return 0;
}

static void set_error(PortableDatabase *db, const char *message)
{
    if (db == NULL) return;
    if (message == NULL) message = "";
    (void)snprintf(db->error, sizeof(db->error), "%s", message);
}

static PortableDbStatus fail(PortableDatabase *db,
                             PortableDbStatus status,
                             const char *message)
{
    set_error(db, message);
    return status;
}

static PortableDbStatus read_file(const char *path, uint8_t **bytes, size_t *size)
{
    FILE *f;
    long length;
    uint8_t *buffer;

    *bytes = NULL;
    *size = 0;
    f = fopen(path, "rb");
    if (f == NULL) return PORTABLE_DB_IO_ERROR;
    if (fseek(f, 0, SEEK_END) != 0 || (length = ftell(f)) < 0 ||
        fseek(f, 0, SEEK_SET) != 0) {
        (void)fclose(f);
        return PORTABLE_DB_IO_ERROR;
    }
    if ((unsigned long)length > (unsigned long)SIZE_MAX) {
        (void)fclose(f);
        return PORTABLE_DB_FORMAT_ERROR;
    }
    if (length == 0) {
        (void)fclose(f);
        return PORTABLE_DB_FORMAT_ERROR;
    }
    buffer = (uint8_t *)malloc((size_t)length);
    if (buffer == NULL) {
        (void)fclose(f);
        return PORTABLE_DB_OUT_OF_MEMORY;
    }
    if (fread(buffer, 1, (size_t)length, f) != (size_t)length) {
        free(buffer);
        (void)fclose(f);
        return PORTABLE_DB_IO_ERROR;
    }
    if (fclose(f) != 0) {
        free(buffer);
        return PORTABLE_DB_IO_ERROR;
    }
    *bytes = buffer;
    *size = (size_t)length;
    return PORTABLE_DB_OK;
}

static int entry_before(const PortableDbIndexEntry *a,
                        const PortableDbIndexEntry *b)
{
    if (a->kind != b->kind) return a->kind < b->kind;
    return a->id < b->id;
}

static size_t lower_bound(const PortableDbIndexEntry *entries,
                          size_t count,
                          int16_t id,
                          int16_t kind)
{
    size_t low = 0;
    size_t high = count;

    while (low < high) {
        size_t mid = low + (high - low) / 2;
        /* DOS FindIndex promotes entry.kind to signed int and compares the
         * entry id as signed 16-bit. Values outside byte-kind range therefore
         * sort before/after every real kind and cannot match.
         */
        if ((int16_t)entries[mid].kind < kind ||
            ((int16_t)entries[mid].kind == kind && entries[mid].id < id))
            low = mid + 1;
        else
            high = mid;
    }
    return low;
}

static PortableDbStatus validate_database(PortableDatabase *db)
{
    size_t expected_index_size;
    uint16_t index_count;
    uint16_t data_count;
    uint64_t previous_offset_end = 0;
    uint64_t max_record_end = 0;
    RecordExtent *extents = NULL;
    size_t i;

    if (db->index_file_size < NDX_HEADER_BYTES || db->data_file_size < DAT_HEADER_BYTES)
        return fail(db, PORTABLE_DB_FORMAT_ERROR, "index or data header is truncated");
    if (read_le32(db->data_file) != 0x12345678u)
        return fail(db, PORTABLE_DB_FORMAT_ERROR, "DAT magic is not 0x12345678");

    index_count = read_le16(db->index_file);
    data_count = read_le16(db->data_file + 4);
    if (index_count != data_count)
        return fail(db, PORTABLE_DB_FORMAT_ERROR, "NDX and DAT record counts differ");
    expected_index_size = NDX_HEADER_BYTES +
        ((size_t)index_count + NDX_RESERVED_ENTRIES) * 8u;
    if (db->index_file_size != expected_index_size)
        return fail(db, PORTABLE_DB_FORMAT_ERROR,
                    "NDX size does not include exactly 32 reserved entries");

    db->entries = (PortableDbIndexEntry *)calloc(index_count ? index_count : 1,
                                                  sizeof(*db->entries));
    extents = (RecordExtent *)calloc(index_count ? index_count : 1, sizeof(*extents));
    if (db->entries == NULL || extents == NULL) {
        free(extents);
        return fail(db, PORTABLE_DB_OUT_OF_MEMORY, "cannot allocate index metadata");
    }
    db->entry_count = index_count;

    for (i = 0; i < index_count; ++i) {
        const uint8_t *raw = db->index_file + NDX_HEADER_BYTES + i * 8u;
        PortableDbIndexEntry *entry = &db->entries[i];
        uint64_t header_at;
        uint64_t payload_at;
        uint64_t record_end;
        uint16_t stored_size;

        entry->data_offset = read_le32(raw);
        entry->id = (int16_t)read_le16(raw + 4);
        entry->kind = raw[6];
        entry->flags = raw[7];

        if (i != 0 && entry_before(entry, &db->entries[i - 1])) {
            free(extents);
            return fail(db, PORTABLE_DB_FORMAT_ERROR,
                        "NDX entries are not sorted by unsigned kind and signed id");
        }
        header_at = (uint64_t)DAT_HEADER_BYTES + entry->data_offset;
        if (header_at + DAT_RECORD_HEADER_BYTES > db->data_file_size) {
            free(extents);
            return fail(db, PORTABLE_DB_FORMAT_ERROR, "record header exceeds DAT bounds");
        }
        /* The six prefix bytes are a fixed record marker in the shipped DBs;
         * the stored length is the word at record-header offset +6, matching
         * DBRecall's DBRecordHeader.size access.
         */
        if (read_le32(db->data_file + header_at) != 0x12345678u ||
            read_le16(db->data_file + header_at + 4) != 0) {
            free(extents);
            return fail(db, PORTABLE_DB_FORMAT_ERROR, "record marker is invalid");
        }
        stored_size = read_le16(db->data_file + header_at + 6);
        payload_at = header_at + DAT_RECORD_HEADER_BYTES;
        record_end = payload_at + stored_size;
        if (record_end > db->data_file_size) {
            free(extents);
            return fail(db, PORTABLE_DB_FORMAT_ERROR, "record payload exceeds DAT bounds");
        }
        if ((entry->flags & 1u) != 0 && (entry->flags & 4u) == 0 && stored_size < 2) {
            free(extents);
            return fail(db, PORTABLE_DB_FORMAT_ERROR,
                        "LZSS record is missing its uncompressed-size prefix");
        }
        extents[i].begin = header_at;
        extents[i].end = record_end;
        if (record_end > max_record_end) max_record_end = record_end;
    }

    qsort(extents, index_count, sizeof(*extents), extent_compare);
    for (i = 0; i < index_count; ++i) {
        if (i != 0 && extents[i].begin < previous_offset_end) {
            free(extents);
            return fail(db, PORTABLE_DB_FORMAT_ERROR, "DAT record extents overlap");
        }
        previous_offset_end = extents[i].end;
    }
    free(extents);

    /* The known DOS databases reserve 256 trailing bytes after the active
     * records. They may contain allocator/free-space metadata and are not a
     * resource record. Require that region so a truncated last payload cannot
     * masquerade as a valid file.
     */
    if (max_record_end + DAT_TRAILER_BYTES > db->data_file_size)
        return fail(db, PORTABLE_DB_FORMAT_ERROR, "DAT reserved trailer is truncated");
    return PORTABLE_DB_OK;
}

PortableDbStatus portable_db_open_files(PortableDatabase *db,
                                        const char *index_path,
                                        const char *data_path)
{
    PortableDbStatus status;
    if (db == NULL || index_path == NULL || data_path == NULL)
        return PORTABLE_DB_FORMAT_ERROR;
    memset(db, 0, sizeof(*db));
    status = read_file(index_path, &db->index_file, &db->index_file_size);
    if (status != PORTABLE_DB_OK)
        return fail(db, status, "cannot read NDX file");
    status = read_file(data_path, &db->data_file, &db->data_file_size);
    if (status != PORTABLE_DB_OK) {
        portable_db_close(db);
        return fail(db, status, "cannot read DAT file");
    }
    status = validate_database(db);
    if (status != PORTABLE_DB_OK) {
        uint8_t *index_file = db->index_file;
        uint8_t *data_file = db->data_file;
        PortableDbIndexEntry *entries = db->entries;
        char error[sizeof(db->error)];
        (void)snprintf(error, sizeof(error), "%s", db->error);
        free(index_file);
        free(data_file);
        free(entries);
        memset(db, 0, sizeof(*db));
        set_error(db, error);
    }
    return status;
}

PortableDbStatus portable_db_open(PortableDatabase *db, const char *root)
{
    size_t n;
    char *ndx;
    char *dat;
    PortableDbStatus status;

    if (db == NULL || root == NULL) return PORTABLE_DB_FORMAT_ERROR;
    n = strlen(root);
    ndx = (char *)malloc(n + 5);
    dat = (char *)malloc(n + 5);
    if (ndx == NULL || dat == NULL) {
        free(ndx);
        free(dat);
        memset(db, 0, sizeof(*db));
        return fail(db, PORTABLE_DB_OUT_OF_MEMORY, "cannot allocate database paths");
    }
    (void)snprintf(ndx, n + 5, "%s.NDX", root);
    (void)snprintf(dat, n + 5, "%s.DAT", root);
    status = portable_db_open_files(db, ndx, dat);
    free(ndx);
    free(dat);
    return status;
}

void portable_db_close(PortableDatabase *db)
{
    if (db == NULL) return;
    free(db->entries);
    free(db->index_file);
    free(db->data_file);
    memset(db, 0, sizeof(*db));
}

PortableDbStatus portable_db_lookup(const PortableDatabase *db,
                                    int16_t id,
                                    int16_t kind,
                                    const PortableDbIndexEntry **entry,
                                    size_t *insertion_index)
{
    size_t low;
    if (entry != NULL) *entry = NULL;
    if (insertion_index != NULL) *insertion_index = 0;
    if (db == NULL || db->entries == NULL)
        return PORTABLE_DB_FORMAT_ERROR;
    low = lower_bound(db->entries, db->entry_count, id, kind);
    if (insertion_index != NULL) *insertion_index = low;
    /* DOS FindIndex performs a final `index[low]` read even when low == count.
     * That is outside the index allocation. Production lookup keeps the valid
     * table contract and never dereferences that one-past address; callers that
     * need to test the historical adjacent-memory behavior can use the explicit
     * safe compatibility function below.
     */
    if (low == db->entry_count || kind < 0 || kind > 255 ||
        db->entries[low].kind != (uint8_t)kind || db->entries[low].id != id)
        return PORTABLE_DB_NOT_FOUND;
    if (entry != NULL) *entry = &db->entries[low];
    return PORTABLE_DB_OK;
}

PortableDbStatus portable_db_find_index_compat(const PortableDbIndexEntry *entries,
                                                size_t count,
                                                const PortableDbIndexEntry *lookahead,
                                                int16_t id,
                                                int16_t kind,
                                                const PortableDbIndexEntry **entry,
                                                size_t *matched_index)
{
    size_t low;
    if (entry != NULL) *entry = NULL;
    if (matched_index != NULL) *matched_index = 0;
    if (count != 0 && entries == NULL) return PORTABLE_DB_FORMAT_ERROR;
    if (count == 0) return PORTABLE_DB_NOT_FOUND; /* DOS early return. */
    low = lower_bound(entries, count, id, kind);
    if (matched_index != NULL) *matched_index = low;
    if (low == count) {
        if (lookahead == NULL || kind < 0 || kind > 255 ||
            lookahead->id != id || lookahead->kind != (uint8_t)kind)
            return PORTABLE_DB_NOT_FOUND;
        if (entry != NULL) *entry = lookahead;
        return PORTABLE_DB_OK;
    }
    if (kind < 0 || kind > 255 || entries[low].kind != (uint8_t)kind || entries[low].id != id)
        return PORTABLE_DB_NOT_FOUND;
    if (entry != NULL) *entry = &entries[low];
    return PORTABLE_DB_OK;
}

static int lzss_decode(const uint8_t *input,
                       size_t input_size,
                       uint8_t *output,
                       size_t output_size)
{
    uint8_t ring[LZSS_RING_BYTES];
    size_t in_at = 0;
    size_t out_at = 0;
    size_t ring_pos = LZSS_INITIAL_POS;
    unsigned int flags = 0;

    memset(ring, 0x20, sizeof(ring));
    while (out_at < output_size) {
        unsigned int token_flags;
        if (((flags >>= 1) & 0x100u) == 0) {
            if (in_at >= input_size) return 0;
            flags = (unsigned int)input[in_at++] | 0xff00u;
        }
        token_flags = flags & 1u;
        if (token_flags != 0) {
            uint8_t value;
            if (in_at >= input_size) return 0;
            value = input[in_at++];
            output[out_at++] = value;
            ring[ring_pos] = value;
            ring_pos = (ring_pos + 1u) & LZSS_RING_MASK;
        } else {
            size_t read_pos;
            size_t length;
            size_t copied;
            uint8_t lo;
            uint8_t hi;
            if (input_size - in_at < 2) return 0;
            lo = input[in_at++];
            hi = input[in_at++];
            read_pos = (size_t)lo | ((size_t)(hi & 0xf0u) << 4);
            length = (size_t)(hi & 0x0fu) + 3u;
            for (copied = 0; copied < length && out_at < output_size; ++copied) {
                uint8_t value = ring[read_pos];
                read_pos = (read_pos + 1u) & LZSS_RING_MASK;
                output[out_at++] = value;
                ring[ring_pos] = value;
                ring_pos = (ring_pos + 1u) & LZSS_RING_MASK;
            }
        }
    }
    return 1;
}

PortableDbStatus portable_db_load(PortableDatabase *db,
                                  int16_t id,
                                  int16_t kind,
                                  PortableDbRecord *record)
{
    const PortableDbIndexEntry *entry;
    PortableDbStatus status;
    uint64_t header_at;
    uint64_t payload_at;
    size_t stored_size;
    const uint8_t *stored;

    if (record == NULL) return PORTABLE_DB_FORMAT_ERROR;
    memset(record, 0, sizeof(*record));
    if (db == NULL || db->data_file == NULL)
        return fail(db, PORTABLE_DB_FORMAT_ERROR, "database is not open");
    status = portable_db_lookup(db, id, kind, &entry, NULL);
    if (status != PORTABLE_DB_OK) {
        if (status == PORTABLE_DB_NOT_FOUND) {
            char message[96];
            (void)snprintf(message, sizeof(message), "resource id=%d kind=%d not found",
                           (int)id, (int)kind);
            return fail(db, status, message);
        }
        return fail(db, status, "invalid database lookup state");
    }
    header_at = (uint64_t)DAT_HEADER_BYTES + entry->data_offset;
    stored_size = read_le16(db->data_file + header_at + 6);
    payload_at = header_at + DAT_RECORD_HEADER_BYTES;
    stored = db->data_file + payload_at;

    record->id = id;
    record->kind = (uint8_t)kind;
    record->index_flags = entry->flags;
    record->data_offset = entry->data_offset;

    if ((entry->flags & 1u) == 0) {
        if (stored_size != 0) {
            record->data = (uint8_t *)malloc(stored_size);
            if (record->data == NULL)
                return fail(db, PORTABLE_DB_OUT_OF_MEMORY, "cannot allocate resource buffer");
            memcpy(record->data, stored, stored_size);
        }
        record->size = stored_size;
    } else if ((entry->flags & 4u) != 0) {
        if (stored_size > SIZE_MAX - 2u)
            return fail(db, PORTABLE_DB_FORMAT_ERROR, "wrapped resource size overflows");
        record->data = (uint8_t *)malloc(stored_size + 2u);
        if (record->data == NULL)
            return fail(db, PORTABLE_DB_OUT_OF_MEMORY, "cannot allocate wrapped resource buffer");
        record->data[0] = 0xff;
        record->data[1] = 0xff;
        if (stored_size != 0) memcpy(record->data + 2, stored, stored_size);
        record->size = stored_size + 2u;
    } else {
        size_t output_size;
        size_t compressed_size;
        if (stored_size < 2u)
            return fail(db, PORTABLE_DB_FORMAT_ERROR, "compressed resource size prefix is missing");
        output_size = read_le16(stored);
        compressed_size = stored_size - 2u;
        if (compressed_size > LZSS_MAX_INPUT)
            return fail(db, PORTABLE_DB_UNSUPPORTED_COMPRESSION,
                        "DOS LZSS source exceeds the original signed input limit");
        if (output_size != 0) {
            record->data = (uint8_t *)malloc(output_size);
            if (record->data == NULL)
                return fail(db, PORTABLE_DB_OUT_OF_MEMORY, "cannot allocate unpacked resource buffer");
        }
        if (!lzss_decode(stored + 2, compressed_size, record->data, output_size)) {
            portable_db_record_free(record);
            return fail(db, PORTABLE_DB_DECOMPRESSION_ERROR,
                        "DOS LZSS stream ended before its declared output length");
        }
        record->size = output_size;
    }
    set_error(db, "");
    return PORTABLE_DB_OK;
}

void portable_db_record_free(PortableDbRecord *record)
{
    if (record == NULL) return;
    free(record->data);
    memset(record, 0, sizeof(*record));
}

const char *portable_db_error(const PortableDatabase *db)
{
    return db == NULL ? "invalid database" : db->error;
}

const char *portable_db_status_string(PortableDbStatus status)
{
    switch (status) {
    case PORTABLE_DB_OK: return "ok";
    case PORTABLE_DB_NOT_FOUND: return "resource not found";
    case PORTABLE_DB_IO_ERROR: return "database I/O error";
    case PORTABLE_DB_FORMAT_ERROR: return "invalid database format";
    case PORTABLE_DB_UNSUPPORTED_COMPRESSION: return "unsupported database compression";
    case PORTABLE_DB_DECOMPRESSION_ERROR: return "database decompression failed";
    case PORTABLE_DB_OUT_OF_MEMORY: return "out of memory";
    default: return "unknown database error";
    }
}
