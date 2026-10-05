#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/types/database.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/handles.h"

extern int16_t OpenDB(char *name);
extern void CloseDB(int16_t db);
extern IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind);
extern char *DBRecall(int16_t db, int16_t object, int16_t kind, int16_t *size);

/* DOS EMS configuration is an explicit unavailable test boundary. All other
 * mutable DB/index/resource objects come from current canonical owners. */
int8_t fd_55B3_360C;
int16_t fd_55B3_3612;
char *fd_55B3_360E;
int16_t f_195A_0260(void) { return 0; }
void f_195A_001D(void) { abort(); }
void f_195A_0035(void) { abort(); }
int16_t f_195A_004B(int16_t pages) { (void)pages; abort(); }
void f_195A_0062(int16_t handle, int16_t logical, int16_t physical)
{ (void)handle; (void)logical; (void)physical; abort(); }
void f_195A_007D(int16_t handle) { (void)handle; abort(); }
void f_195A_01CB(int16_t handle, char *name) { (void)handle; (void)name; abort(); }
int16_t WinPrintf(char *format, ...)
{ fprintf(stderr, "unexpected WinPrintf: %s\n", format); exit(90); }
void Punt(char *format, ...)
{ fprintf(stderr, "unexpected Punt: %s\n", format); exit(91); }

static uint32_t fnv1a(const uint8_t *bytes, size_t n)
{
    uint32_t h = 2166136261u;
    size_t i;
    for (i = 0; i < n; ++i) h = (h ^ bytes[i]) * 16777619u;
    return h;
}

static int read_exact(FILE *file, void *target, size_t size)
{ return fread(target, 1, size, file) == size; }

static int exercise(const char *stem, FILE *fixture)
{
    int16_t db, count;
    uint16_t expected_count;
    size_t i;
    if (!read_exact(fixture, &expected_count, sizeof expected_count)) return 10;
    db = OpenDB((char *)stem);
    if (db < 0 || db >= 4) return 11;
    count = fd_50F6_3958[db].indexHeader.count;
    if ((uint16_t)count != expected_count || !fd_50F6_3958[db].index) return 12;
    /* Actual converted FindIndex has a count guard. No sentinel allocation or
     * source count adjustment is applied by this fixture. */
    if (FindIndex(db, 32767, 256) != NULL || fd_50F6_3956 != count ||
        fd_50F6_3952 != fd_50F6_3958[db].index + count) return 13;
    for (i = 0; i < expected_count; ++i) {
        int16_t id;
        uint8_t kind, flags;
        uint32_t expected_size;
        uint8_t *expected;
        int16_t size = -1;
        char *handle;
        char *data;
        if (!read_exact(fixture, &id, sizeof id) || !read_exact(fixture, &kind, sizeof kind) ||
            !read_exact(fixture, &flags, sizeof flags) || !read_exact(fixture, &expected_size, sizeof expected_size) ||
            expected_size > UINT16_MAX) return 14;
        expected = (uint8_t *)malloc(expected_size ? expected_size : 1);
        if (!expected || !read_exact(fixture, expected, expected_size)) return 14;
        handle = DBRecall(db, id, kind, &size);
        if (!handle || (uint16_t)size != expected_size) return 15;
        data = f_171C_1B84((char **)handle);
        if (!data || memcmp(data, expected, expected_size) != 0) {
            fprintf(stderr, "payload mismatch %s id=%d kind=%u\n", stem, id, kind);
            return 16;
        }
        printf("RECORD,%s,%d,%u,%u,%zu,%08x\n", stem, id, kind,
               flags, (size_t)expected_size, fnv1a((const uint8_t *)data, expected_size));
        if (f_171C_1BBA((char **)handle) == NULL) return 17;
        f_171C_13E4((char **)handle);
        free(expected);
        if (sim_handles_global_last_status() != SIM_HANDLE_OK) return 18;
    }
    CloseDB(db);
    if (fd_50F6_3958[db].name[0] != '\0') return 19;
    printf("CLOSED,%s,%d\n", stem, count);
    return 0;
}

static int write_header(const char *root, const char *stem, int mutate)
{
    int16_t db = OpenDB((char *)stem);
    char path[512];
    uint8_t bytes[15];
    FILE *file;
    size_t i, size;
    if (db < 0 || db >= 4) return 30;
    if (mutate) {
        fd_50F6_3958[db].header.magic = 0x12345678;
        fd_50F6_3958[db].header.count = -7;
        fd_50F6_3958[db].header.freeBytes = 0x01020304;
        fd_50F6_3958[db].header.wastedBytes = 0x05060708;
        fd_50F6_3958[db].dirty = 1;
    }
    CloseDB(db);
    snprintf(path, sizeof path, "%s/%s.DAT", root, stem);
    file = fopen(path, "rb");
    if (!file) return 31;
    size = fread(bytes, 1, sizeof bytes, file);
    fclose(file);
    if (size != 14) return 32;
    printf("WRITE,%s,", stem);
    for (i = 0; i < size; ++i) printf("%02x", bytes[i]);
    printf(",%zu\n", size);
    return 0;
}

int main(int argc, char **argv)
{
    int rc;
    FILE *fixture;
    uint32_t magic;
    uint16_t datasets;
    if (argc == 3 && strcmp(argv[1], "--wire") == 0) {
        if (dos_files_set_root(argv[2]) != 0) return 2;
        if ((rc = write_header(argv[2], "NEW", 0)) != 0 ||
            (rc = write_header(argv[2], "EXIST", 1)) != 0) return rc;
        dos_files_close_all();
        puts("PASS actual OpenDB/CloseDB 14-byte header writes");
        return 0;
    }
    if (argc != 3 || dos_files_set_root(argv[1]) != 0 || (fixture = fopen(argv[2], "rb")) == NULL) return 2;
    if (!read_exact(fixture, &magic, sizeof magic) || magic != 0x31445257u ||
        !read_exact(fixture, &datasets, sizeof datasets) || datasets != 3) return 3;
    if ((rc = exercise("HCEGANT", fixture)) != 0 || (rc = exercise("SHARED", fixture)) != 0 ||
        (rc = exercise("SOUND", fixture)) != 0) {
        fprintf(stderr, "database integration failed %d\n", rc); return rc;
    }
    if (fgetc(fixture) != EOF) return 4;
    fclose(fixture);
    dos_files_close_all();
    puts("PASS actual canonical DB recall 840 resource records");
    return 0;
}
