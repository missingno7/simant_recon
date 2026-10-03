#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "drive_directory.h"

#include <stdlib.h>
#include <string.h>

#ifndef _WIN32
#error "The drive-CWD provider requires Win32 per-drive path semantics"
#endif

/* GetFullPathNameA("X:.") applies Windows' process-local per-drive CWD rule.
 * Verify the resulting drive and directory exist before exposing it, since a
 * lexical expansion alone would invent a usable path for an absent drive. */
int16_t sim_drive_getcwd(int16_t drive, char *path, size_t capacity)
{
    char current[MAX_PATH + 1];
    char drive_relative[4];
    char *expanded = NULL;
    DWORD needed, written, attributes;
    char expected_drive = 0;
    int ok = 0;

    if (!path || capacity == 0 || drive < 0 || drive > 26) return 0;

    if (drive == 0) {
        DWORD n = GetCurrentDirectoryA((DWORD)sizeof current, current);
        if (n == 0 || n >= sizeof current ||
            !((current[0] >= 'A' && current[0] <= 'Z') ||
              (current[0] >= 'a' && current[0] <= 'z')) ||
            current[1] != ':' || current[2] != '\\')
            return 0;
        expected_drive = (char)(current[0] >= 'a' && current[0] <= 'z' ?
                                current[0] - ('a' - 'A') : current[0]);
        drive_relative[0] = expected_drive;
    } else {
        expected_drive = (char)('A' + drive - 1);
        drive_relative[0] = expected_drive;
    }
    drive_relative[1] = ':';
    drive_relative[2] = '.';
    drive_relative[3] = '\0';

    needed = GetFullPathNameA(drive_relative, 0, NULL, NULL);
    if (needed == 0 || needed > 32768u) return 0;
    expanded = (char *)malloc((size_t)needed);
    if (!expanded) return 0;
    written = GetFullPathNameA(drive_relative, needed, expanded, NULL);
    if (written == 0 || written >= needed ||
        expanded[0] != expected_drive || expanded[1] != ':' ||
        expanded[2] != '\\')
        goto done;
    attributes = GetFileAttributesA(expanded);
    if (attributes == INVALID_FILE_ATTRIBUTES ||
        !(attributes & FILE_ATTRIBUTE_DIRECTORY))
        goto done;
    if ((size_t)written + 1u > capacity) goto done;

    memcpy(path, expanded, (size_t)written + 1u);
    ok = 1;
done:
    free(expanded);
    return (int16_t)ok;
}

int16_t f_1F66_00AF(int16_t drive, char *path)
{
    return sim_drive_getcwd(drive, path, 67u);
}
