#include "../../game/resources/database.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures;

#define CHECK(expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); \
        ++failures; \
    } \
} while (0)

static uint64_t fnv1a64(const uint8_t *bytes, size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t i;
    for (i = 0; i < size; ++i) {
        hash ^= bytes[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static void check_database(const char *asset_dir,
                           const char *stem,
                           size_t expected_count,
                           size_t *loaded_count,
                           size_t *lzss_count,
                           uint64_t *aggregate)
{
    char ndx[512];
    char dat[512];
    PortableDatabase db;
    PortableDbStatus status;
    size_t i;
    size_t local_loaded = 0;

    (void)snprintf(ndx, sizeof(ndx), "%s/%s.NDX", asset_dir, stem);
    (void)snprintf(dat, sizeof(dat), "%s/%s.DAT", asset_dir, stem);
    memset(&db, 0, sizeof(db));
    status = portable_db_open_files(&db, ndx, dat);
    if (status != PORTABLE_DB_OK) {
        fprintf(stderr, "%s open failed: %s (%s)\n", stem,
                portable_db_status_string(status), portable_db_error(&db));
        CHECK(status == PORTABLE_DB_OK);
        return;
    }
    CHECK(db.entry_count == expected_count);

    for (i = 0; i < db.entry_count; ++i) {
        const PortableDbIndexEntry *entry = &db.entries[i];
        PortableDbRecord record;
        status = portable_db_load(&db, entry->id, entry->kind, &record);
        if (status != PORTABLE_DB_OK) {
            fprintf(stderr, "%s id=%d kind=%u load failed: %s (%s)\n", stem,
                    (int)entry->id, (unsigned)entry->kind,
                    portable_db_status_string(status), portable_db_error(&db));
            CHECK(status == PORTABLE_DB_OK);
            continue;
        }
        CHECK(record.id == entry->id);
        CHECK(record.kind == entry->kind);
        CHECK(record.index_flags == entry->flags);
        CHECK(record.data != NULL || record.size == 0);
        *aggregate ^= fnv1a64(record.data, record.size) +
                      ((uint64_t)(uint16_t)record.id << 32) + record.kind;
        *aggregate *= UINT64_C(1099511628211);
        if ((entry->flags & 1u) != 0 && (entry->flags & 4u) == 0)
            ++*lzss_count;
        ++local_loaded;
        portable_db_record_free(&record);
    }
    CHECK(local_loaded == expected_count);
    *loaded_count += local_loaded;

    if (db.entry_count != 0) {
        const PortableDbIndexEntry *entry = NULL;
        CHECK(portable_db_lookup(&db, db.entries[0].id, db.entries[0].kind,
                                 &entry, NULL) == PORTABLE_DB_OK);
        CHECK(entry == &db.entries[0]);
        CHECK(portable_db_lookup(&db, db.entries[0].id, -1, &entry, NULL) ==
              PORTABLE_DB_NOT_FOUND);
        CHECK(entry == NULL);
        CHECK(portable_db_lookup(&db, db.entries[0].id, 256, &entry, NULL) ==
              PORTABLE_DB_NOT_FOUND);
        CHECK(entry == NULL);
    }
    portable_db_close(&db);
}

static void check_known_hcegant(const char *asset_dir)
{
    char ndx[512];
    char dat[512];
    PortableDatabase db;
    PortableDbRecord record;
    char root[512];

    (void)snprintf(ndx, sizeof(ndx), "%s/HCEGANT.NDX", asset_dir);
    (void)snprintf(dat, sizeof(dat), "%s/HCEGANT.DAT", asset_dir);
    memset(&db, 0, sizeof(db));
    CHECK(portable_db_open_files(&db, ndx, dat) == PORTABLE_DB_OK);

    CHECK(portable_db_load(&db, 1200, 2, &record) == PORTABLE_DB_OK);
    CHECK(record.size == 1032);
    CHECK(record.data != NULL && record.data[0] == 0x03 && record.data[1] == 0x00);
    portable_db_record_free(&record);

    CHECK(portable_db_load(&db, 1210, 2, &record) == PORTABLE_DB_OK);
    CHECK(record.size == 5368);
    CHECK(record.data != NULL && record.data[0] == 0x00 && record.data[1] == 0x00);
    portable_db_record_free(&record);

    CHECK(portable_db_load(&db, 1, 15, &record) == PORTABLE_DB_OK);
    CHECK(record.size == 21);
    CHECK(record.data != NULL && record.data[0] == 0x10 && record.data[1] == 0x01);
    portable_db_record_free(&record);
    portable_db_close(&db);

    (void)snprintf(root, sizeof(root), "%s/HCEGANT", asset_dir);
    memset(&db, 0, sizeof(db));
    CHECK(portable_db_open(&db, root) == PORTABLE_DB_OK);
    CHECK(db.entry_count == 271);
    portable_db_close(&db);
}

static void check_find_index_lookahead(void)
{
    const PortableDbIndexEntry entries[] = {
        { 0, 1, 2, 0 }, { 1, 4, 2, 0 }
    };
    const PortableDbIndexEntry hit = { 2, 9, 2, 0 };
    const PortableDbIndexEntry miss = { 2, 10, 2, 0 };
    const PortableDbIndexEntry *found = NULL;
    size_t matched = 0;

    CHECK(portable_db_find_index_compat(entries, 2, &hit, 9, 2,
                                        &found, &matched) == PORTABLE_DB_OK);
    CHECK(found == &hit && matched == 2);
    CHECK(portable_db_find_index_compat(entries, 2, &miss, 9, 2,
                                        &found, &matched) == PORTABLE_DB_NOT_FOUND);
    CHECK(found == NULL && matched == 2);
    CHECK(portable_db_find_index_compat(NULL, 0, &hit, 9, 2,
                                        &found, &matched) == PORTABLE_DB_NOT_FOUND);
    CHECK(found == NULL && matched == 0);
}

int main(int argc, char **argv)
{
    const char *asset_dir = argc > 1 ? argv[1] : "assets";
    size_t loaded_count = 0;
    size_t lzss_count = 0;
    uint64_t aggregate = UINT64_C(14695981039346656037);

    check_database(asset_dir, "HCEGANT", 271, &loaded_count, &lzss_count, &aggregate);
    check_database(asset_dir, "SHARED", 449, &loaded_count, &lzss_count, &aggregate);
    check_database(asset_dir, "SOUND", 120, &loaded_count, &lzss_count, &aggregate);
    check_known_hcegant(asset_dir);
    check_find_index_lookahead();

    CHECK(loaded_count == 840);
    CHECK(lzss_count == 205);
    CHECK(aggregate == UINT64_C(0x2cd5f2c76ee8a96e));
    if (failures != 0) {
        fprintf(stderr, "%d database test(s) failed\n", failures);
        return 1;
    }
    printf("PASS databases=3 records_loaded=%zu lzss_records=%zu aggregate=%016llx\n",
           loaded_count, lzss_count, (unsigned long long)aggregate);
    return 0;
}
