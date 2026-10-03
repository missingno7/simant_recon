#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "../drive_directory.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    char current[MAX_PATH + 1];
    char path[67];
    char too_small[4] = { 'K', 'e', 'e', 'p' };
    DWORD cwd_len = GetCurrentDirectoryA((DWORD)sizeof current, current);
    DWORD drives = GetLogicalDrives();
    unsigned current_drive, i, available = 0, successful = 0;

    assert(cwd_len > 2 && cwd_len < sizeof current);
    assert(current[1] == ':');
    current_drive = (unsigned)(current[0] >= 'a' ? current[0] - 'a' :
                               current[0] - 'A') + 1u;

    memset(path, 0xA5, sizeof path);
    assert(f_1F66_00AF((int16_t)current_drive, path) == 1);
    assert(path[0] == current[0] && path[1] == ':' && path[2] == '\\');
    assert(strlen(path) < sizeof path);
    assert(strcmp(path, current) == 0);
    successful++;

    memset(path, 0xA5, sizeof path);
    assert(sim_drive_getcwd(0, path, sizeof path) == 1);
    assert(strcmp(path, current) == 0);
    successful++;

    assert(sim_drive_getcwd(0, too_small, 3) == 0);
    assert(memcmp(too_small, "Keep", sizeof too_small) == 0);
    assert(sim_drive_getcwd(-1, path, sizeof path) == 0);
    assert(sim_drive_getcwd(27, path, sizeof path) == 0);
    assert(sim_drive_getcwd(1, NULL, sizeof path) == 0);
    successful += 4;

    for (i = 0; i < 26; ++i) {
        char candidate[67];
        if (!(drives & (1u << i))) continue;
        available++;
        memset(candidate, 0x5A, sizeof candidate);
        if (sim_drive_getcwd((int16_t)(i + 1u), candidate, sizeof candidate)) {
            char query[4] = { (char)('A' + i), ':', '.', '\0' };
            char expanded[MAX_PATH + 1];
            DWORD n = GetFullPathNameA(query, (DWORD)sizeof expanded,
                                       expanded, NULL);
            assert(n > 0 && n < sizeof expanded);
            assert(strcmp(candidate, expanded) == 0);
            successful++;
        }
    }

    printf("PASS: current-drive and available-drive Win32 CWD paths (%u drives, %u successful checks); bounds and invalid-input controls passed\n",
           available, successful);
    return 0;
}
