#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "../directory.h"
#include "../drive_directory.h"
#include "../dos_files.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "check failed: %s (%s:%d)\n", #condition, __FILE__, __LINE__); \
        return 2; \
    } \
} while (0)

typedef struct VisibleRow {
    unsigned char attrib;
    uint16_t time, date;
    int32_t size;
    char name[13];
} VisibleRow;

static VisibleRow baseline[256];
static size_t baseline_count;

static int capture_root(const char *root, int compare)
{
    char before[MAX_PATH + 1], after[MAX_PATH + 1], cwd[67];
    struct find_t item;
    VisibleRow rows[256];
    size_t count = 0, i;
    uint16_t status;
    DWORD n = GetCurrentDirectoryA((DWORD)sizeof before, before);
    assert(n > 0 && n < sizeof before);
    assert(sim_drive_set_root(root) == 1);
    assert(sim_drive_getdrive() == 3);
    assert(sim_drive_setdrive(3) == 0);
    assert(sim_drive_setdrive(4) == -1);
    assert(sim_drive_getdrive() == 3);
    memset(cwd, 0xA5, sizeof cwd);
    assert(f_1F66_00AF(3, cwd) == 1 && strcmp(cwd, "C:\\") == 0);
    assert(sim_drive_getcwd(0, cwd, sizeof cwd) == 1 && strcmp(cwd, "C:\\") == 0);
    assert(sim_drive_getcwd(0, cwd, 3) == 0);
    assert(sim_drive_chdir("FOLDER") == 0);
    assert(sim_drive_getcwd(3, cwd, sizeof cwd) == 1 && strcmp(cwd, "C:\\FOLDER") == 0);
    assert(sim_drive_chdir("..") == 0);
    assert(sim_drive_chdir("D:\\") == 15);
    assert(sim_drive_getcwd(3, cwd, sizeof cwd) == 1 && strcmp(cwd, "C:\\") == 0);
    assert(sim_drive_chdir("C:\\12345678\\12345678\\12345678\\12345678\\12345678\\12345678\\12345678") == 206);
    assert(_dos_findfirst("C:\\*.*", 0x10, &item) == 0);
    do {
        assert(count < sizeof rows / sizeof rows[0]);
        rows[count].attrib = (unsigned char)item.attrib;
        rows[count].time = item.wr_time;
        rows[count].date = item.wr_date;
        rows[count].size = item.size;
        memcpy(rows[count].name, item.name, sizeof rows[count].name);
        ++count;
        status = _dos_findnext(&item);
    } while (status == 0);
    assert(status == 18);
    assert(GetCurrentDirectoryA((DWORD)sizeof after, after) > 0);
    assert(strcmp(before, after) == 0);
    if (!compare) {
        memcpy(baseline, rows, count * sizeof rows[0]);
        baseline_count = count;
    } else {
        if (count != baseline_count) {
            fprintf(stderr, "enumeration count differs: %lu vs %lu\\n",
                    (unsigned long)baseline_count, (unsigned long)count);
            for (i = 0; i < count; ++i)
                fprintf(stderr, "deep[%lu]=%s\\n", (unsigned long)i, rows[i].name);
            for (i = 0; i < baseline_count; ++i)
                fprintf(stderr, "base[%lu]=%s\\n", (unsigned long)i, baseline[i].name);
        }
        assert(count == baseline_count);
        for (i = 0; i < count; ++i)
            assert(memcmp(&rows[i], &baseline[i], sizeof rows[i]) == 0);
    }
    return 0;
}

int main(int argc, char **argv)
{
    assert(argc == 3);
    assert(capture_root(argv[1], 0) == 0);
    assert(capture_root(argv[2], 1) == 0);
    puts("virtual DOS root, drive/CWD and deep-host-root negative control: PASS");
    return 0;
}
