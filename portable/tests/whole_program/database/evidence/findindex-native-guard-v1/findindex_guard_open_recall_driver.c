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

/* This test selects the real direct-file-I/O host edge; any EMS use is fatal. */
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
void Punt(char *format, ...)
{ fprintf(stderr, "unexpected source Punt: %s\n", format ? format : "(null)"); abort(); }
int16_t WinPrintf(char *format, ...)
{ fprintf(stderr, "unexpected source WinPrintf: %s\n", format ? format : "(null)"); abort(); return -1; }

static int portable_record_matches(const char *name, int16_t id, int16_t kind,
                                   const uint8_t *data, size_t size)
{
    char index_path[128], data_path[128];
    PortableDatabase db;
    PortableDbRecord record;
    int ok;
    memset(&db, 0, sizeof(db));
    memset(&record, 0, sizeof(record));
    (void)snprintf(index_path, sizeof(index_path), "%s.NDX", name);
    (void)snprintf(data_path, sizeof(data_path), "%s.DAT", name);
    if (portable_db_open_files(&db, index_path, data_path) != PORTABLE_DB_OK) return 0;
    ok = portable_db_load(&db, id, kind, &record) == PORTABLE_DB_OK &&
         record.size == size && (!size || memcmp(record.data, data, size) == 0);
    portable_db_record_free(&record);
    portable_db_close(&db);
    return ok;
}

static int check_resource(int16_t db, const char *name, int16_t id, int16_t kind)
{
    int16_t size = -1234;
    char *master = DBRecall(db, id, kind, &size);
    char *data;
    int ok;
    if (!master || size < 0) return 0;
    data = f_171C_1B84((char **)master);
    if (!data) return 0;
    ok = portable_record_matches(name, id, kind, (const uint8_t *)data, (uint16_t)size);
    if (f_171C_1BBA((char **)master) == NULL) return 0;
    f_171C_13E4((char **)master);
    return ok;
}

static int check_open_database(const char *name, int16_t id, int16_t kind)
{
    int16_t db = OpenDB((char *)name);
    int16_t count, miss_id, miss_kind, size;
    IndexEntry *last, *found;
    char *miss;
    if (db < 0 || db >= 4) return 1;
    count = fd_50F6_3958[db].indexHeader.count;
    if (count <= 0 || !fd_50F6_3958[db].index) return 2;
    last = &fd_50F6_3958[db].index[count - 1];
    if (FindIndex(db, last->id, last->kind) != last || fd_50F6_3956 != count - 1)
        return 3;
    /* Explicit above-maximum, invalid-kind, and last-row resource paths. */
    if (last->id < INT16_MAX) { miss_id = (int16_t)(last->id + 1); miss_kind = last->kind; }
    else { miss_id = INT16_MIN; miss_kind = (int16_t)(last->kind + 1); }
    found = FindIndex(db, miss_id, miss_kind);
    if (found || fd_50F6_3956 != count || fd_50F6_3952 != last + 1) return 4;
    size = 0x4567;
    miss = DBRecall(db, miss_id, miss_kind, &size);
    if (miss || size != 0x4567) return 5;
    if (DBRecall(db, INT16_MAX, 256, &size) != NULL) return 6;
    if (!check_resource(db, name, last->id, last->kind)) return 7;
    if (!check_resource(db, name, id, kind)) return 8;
    CloseDB(db);
    if (fd_50F6_3958[db].name[0] != '\0' ||
        sim_handles_global_last_status() != SIM_HANDLE_OK) return 9;
    printf("PASS,%s,count=%d,last=%d/%u,above_max=%d/%d,resources=2\n",
           name, count, last->id, last->kind, miss_id, miss_kind);
    return 0;
}

int main(int argc, char **argv)
{
    int rc;
    if (argc != 2 || dos_files_set_root(argv[1]) != 0) return 2;
    fd_50F6_3958[3].index = NULL;
    fd_50F6_3958[3].indexHeader.count = 0;
    if (FindIndex(3, 1, 1) != NULL || fd_50F6_3956 != 0) return 3;
    rc = check_open_database("HCEGANT", 0, 0);
    if (rc) { fprintf(stderr, "HCEGANT status %d\n", rc); return 10 + rc; }
    rc = check_open_database("SHARED", 128, 2); /* compressed */
    if (rc) { fprintf(stderr, "SHARED compressed status %d\n", rc); return 30 + rc; }
    rc = check_open_database("SHARED", 129, 2); /* uncompressed */
    if (rc) { fprintf(stderr, "SHARED raw status %d\n", rc); return 50 + rc; }
    rc = check_open_database("SOUND", 0, 5);
    if (rc) { fprintf(stderr, "SOUND status %d\n", rc); return 70 + rc; }
    dos_files_close_all();
    puts("PASS guarded actual-source open/read/decode/close and invalid-resource controls");
    return 0;
}
