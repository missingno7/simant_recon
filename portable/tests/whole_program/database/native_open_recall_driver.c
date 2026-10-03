#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/types/database.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/game/resources/database.h"

extern int16_t OpenDB(char *name);
extern void CloseDB(int16_t db);
extern IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind);
extern char *DBRecall(int16_t db, int16_t object, int16_t kind, int16_t *size);

/* This bounded host fixture explicitly selects direct file IO and reports EMS
 * unavailable. EMS page-cache entries are therefore never executed. */
typedef struct { uint16_t age; int16_t file, page; } EmsSlot;
int8_t fd_55B3_360C;
int16_t fd_55B3_3612;
char *fd_55B3_360E;
char *fd_50F6_3B48;
EmsSlot **fd_50F6_3B4C;
int16_t f_195A_0260(void) { return 0; }
void f_195A_001D(void) { abort(); }
void f_195A_0035(void) { abort(); }
int16_t f_195A_004B(int16_t pages) { (void)pages; abort(); }
void f_195A_0062(int16_t handle, int16_t logical, int16_t physical)
{ (void)handle; (void)logical; (void)physical; abort(); }
void f_195A_007D(int16_t handle) { (void)handle; abort(); }
void f_195A_01CB(int16_t handle, char *name)
{ (void)handle; (void)name; abort(); }
void WinPrintf(char *format, ...)
{ fprintf(stderr, "unexpected source WinPrintf: %s\n", format ? format : "(null)"); abort(); }

void Punt(char *format, ...)
{
    fprintf(stderr, "unexpected source Punt: %s\n", format ? format : "(null)");
    exit(90);
}

static uint32_t fnv1a(const uint8_t *bytes, size_t n)
{
    uint32_t h = 2166136261u;
    size_t i;
    for (i = 0; i < n; ++i) h = (h ^ bytes[i]) * 16777619u;
    return h;
}

/* The source OpenIndex allocates count*8 active bytes, while source FindIndex
 * forms index[count] on a miss above the final key. Give this native fixture a
 * defined zero sentinel while preserving every active row and the source count.
 * The sentinel is a host safety boundary, not a claim about DOS heap residue. */
static int install_defined_native_sentinel(int16_t db)
{
    size_t count = (uint16_t)fd_50F6_3958[db].indexHeader.count;
    size_t active = count * sizeof(IndexEntry);
    uint8_t *old_data = (uint8_t *)fd_50F6_3958[db].index;
    uint8_t *new_data;
    if (!count || !old_data || active > UINT16_MAX - sizeof(IndexEntry)) return 0;
    new_data = (uint8_t *)dos_malloc((uint16_t)(active + sizeof(IndexEntry)));
    if (!new_data) return 0;
    memcpy(new_data, old_data, active);
    memset(new_data + active, 0, sizeof(IndexEntry));
    dos_free(old_data);
    fd_50F6_3958[db].index = (IndexEntry *)new_data;
    return 1;
}

static int exercise_database(const char *name, int16_t object, int16_t kind)
{
    int16_t db = OpenDB((char *)name);
    int16_t count, size = -1;
    IndexEntry *last, *miss;
    char *handle;
    char *data;
    uint32_t hash;
    char index_path[512], data_path[512];
    PortableDatabase model;
    PortableDbRecord model_record;
    PortableDbStatus model_status;
    memset(&model, 0, sizeof(model));
    memset(&model_record, 0, sizeof(model_record));
    if (db < 0 || db >= 4) return 10;
    if (snprintf(index_path, sizeof(index_path), "%s.NDX", name) < 0 ||
        snprintf(data_path, sizeof(data_path), "%s.DAT", name) < 0)
        return 18;
    model_status = portable_db_open_files(&model, index_path, data_path);
    if (model_status != PORTABLE_DB_OK) {
        fprintf(stderr, "model open failed %s: %d %s\n", name, model_status,
                portable_db_error(&model));
        return 18;
    }
    count = fd_50F6_3958[db].indexHeader.count;
    if (count <= 0 || !fd_50F6_3958[db].index ||
        !install_defined_native_sentinel(db)) return 11;
    last = &fd_50F6_3958[db].index[count - 1];
    if (FindIndex(db, last->id, last->kind) != last) return 12;
    if (last->id < INT16_MAX) miss = FindIndex(db, (int16_t)(last->id + 1), last->kind);
    else if (last->kind < UINT8_MAX) miss = FindIndex(db, INT16_MIN, (int16_t)(last->kind + 1));
    else miss = FindIndex(db, 0, 0);
    if (miss != NULL) return 13;

    handle = DBRecall(db, object, kind, &size);
    if (!handle || size <= 0) return 14;
    data = f_171C_1B84((char **)handle);
    if (!data) return 15;
    model_status = portable_db_load(&model, object, kind, &model_record);
    if (model_status != PORTABLE_DB_OK || model_record.size != (uint16_t)size ||
        memcmp(data, model_record.data, (size_t)size) != 0) return 19;
    hash = fnv1a((const uint8_t *)data, (uint16_t)size);
    printf("%s,%d,%d,%d,%08x,%02x%02x%02x%02x\n", name, object, kind,
           size, hash, (uint8_t)data[0], (uint8_t)data[size > 1 ? 1 : 0],
           (uint8_t)data[size > 2 ? 2 : 0], (uint8_t)data[size > 3 ? 3 : 0]);
    if (f_171C_1BBA((char **)handle) == NULL) return 16;
    f_171C_13E4((char **)handle);
    portable_db_record_free(&model_record);
    portable_db_close(&model);
    CloseDB(db);
    if (fd_50F6_3958[db].name[0] != '\0' ||
        sim_handles_global_last_status() != SIM_HANDLE_OK) return 17;
    return 0;
}

int main(int argc, char **argv)
{
    int rc;
    if (argc != 2 || dos_files_set_root(argv[1]) != 0) return 2;
    rc = exercise_database("HCEGANT", 0, 0);
    if (rc) { fprintf(stderr, "HCEGANT probe failed %d\n", rc); return 20; }
    rc = exercise_database("SHARED", 128, 2);
    if (rc) { fprintf(stderr, "SHARED compressed probe failed %d\n", rc); return 21; }
    rc = exercise_database("SHARED", 129, 2);
    if (rc) { fprintf(stderr, "SHARED raw probe failed %d\n", rc); return 22; }
    rc = exercise_database("SOUND", 0, 5);
    if (rc) { fprintf(stderr, "SOUND probe failed %d\n", rc); return 23; }
    dos_files_close_all();
    puts("PASS actual OpenDB/OpenIndex/FindIndex/DBRecall/CloseDB; native sentinel misses defined");
    return 0;
}
