#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "drive_directory.h"

#include <ctype.h>
#include <string.h>

#ifndef _WIN32
#error "The virtual DOS drive provider currently requires the Win32 host filesystem"
#endif

enum {
    DOS_E_FILE_NOT_FOUND = 2,
    DOS_E_PATH_NOT_FOUND = 3,
    DOS_E_ACCESS_DENIED = 5,
    DOS_E_INVALID_DRIVE = 15,
    DOS_E_FILENAME_RANGE = 206,
    DOS_E_OUT_OF_MEMORY = 8,
    DOS_DRIVE_C = 3,
    HOST_PATH_CAPACITY = 32768
};

#define DOS_PATH_CHARS 64u

/* Host paths stay in this private provider state. Guest-visible paths are
 * canonical DOS strings rooted at C:\ and never contain this value. */
static char host_root[HOST_PATH_CAPACITY];
static char drive_cwd[26][DOS_PATH_CHARS + 1u];
static unsigned current_drive = DOS_DRIVE_C;
static int root_ready;

static char upper_ascii(char ch)
{
    if (ch >= 'a' && ch <= 'z') return (char)(ch - ('a' - 'A'));
    return ch;
}

static int valid_dos_char(unsigned char ch, int allow_wildcards)
{
    if (ch < 0x21 || ch > 0x7e) return 0;
    if (strchr("\"/\\:<>|", (int)ch) != NULL) return 0;
    if (!allow_wildcards && (ch == '*' || ch == '?')) return 0;
    return 1;
}

static int valid_component(const char *name, size_t length, int allow_wildcards)
{
    size_t i, base = 0, extension = 0;
    int seen_dot = 0;
    if (length == 0) return 0;
    if ((length == 1 && name[0] == '.') ||
        (length == 2 && name[0] == '.' && name[1] == '.')) return 1;
    for (i = 0; i < length; ++i) {
        unsigned char ch = (unsigned char)name[i];
        if (!valid_dos_char(ch, allow_wildcards)) return 0;
        if (ch == '.') {
            if (seen_dot || base == 0) return 0;
            seen_dot = 1;
        } else if (seen_dot) {
            ++extension;
        } else {
            ++base;
        }
    }
    return base <= 8u && (!seen_dot || extension <= 3u) &&
           (allow_wildcards || !seen_dot || extension != 0u);
}

static unsigned requested_drive(const char *path, const char **tail,
                                int *absolute)
{
    const unsigned char *p = (const unsigned char *)path;
    unsigned drive = current_drive;
    *tail = path;
    *absolute = 0;
    if (((p[0] >= 'A' && p[0] <= 'Z') || (p[0] >= 'a' && p[0] <= 'z')) &&
        p[1] == ':') {
        drive = (unsigned)(upper_ascii((char)p[0]) - 'A') + 1u;
        *tail = path + 2;
        if (**tail == '\\') {
            *absolute = 1;
            ++*tail;
        }
    } else if (p[0] == '\\') {
        *absolute = 1;
        *tail = path + 1;
    }
    return drive;
}

static unsigned canonicalize(const char *path, int allow_wildcards,
                             char canonical[DOS_PATH_CHARS + 1u],
                             unsigned *drive_out)
{
    char parts[26][13];
    size_t count = 0, used = 0, i;
    const char *tail;
    int absolute;
    unsigned drive;
    const char *initial;

    if (!path || !*path) return DOS_E_PATH_NOT_FOUND;
    drive = requested_drive(path, &tail, &absolute);
    if (drive != DOS_DRIVE_C || !root_ready) return DOS_E_INVALID_DRIVE;
    if (drive_out) *drive_out = drive;

    if (!absolute) {
        initial = drive_cwd[drive - 1u];
        while (*initial) {
            size_t length = 0;
            while (initial[length] && initial[length] != '\\') ++length;
            if (length == 0 || length > 12u || count >= 26u)
                return DOS_E_PATH_NOT_FOUND;
            memcpy(parts[count], initial, length);
            parts[count][length] = '\0';
            ++count;
            initial += length;
            if (*initial == '\\') ++initial;
        }
    }

    while (*tail) {
        const char *begin;
        size_t length;
        while (*tail == '\\') ++tail;
        if (!*tail) break;
        begin = tail;
        while (*tail && *tail != '\\') {
            if (*tail == '/') return DOS_E_PATH_NOT_FOUND;
            ++tail;
        }
        length = (size_t)(tail - begin);
        if (!valid_component(begin, length, allow_wildcards))
            return DOS_E_FILENAME_RANGE;
        if (length == 1u && begin[0] == '.') continue;
        if (length == 2u && begin[0] == '.' && begin[1] == '.') {
            if (count) --count;
            continue;
        }
        if (count >= 26u) return DOS_E_PATH_NOT_FOUND;
        memcpy(parts[count], begin, length);
        parts[count][length] = '\0';
        for (i = 0; i < length; ++i) parts[count][i] = upper_ascii(parts[count][i]);
        ++count;
        if (allow_wildcards && *tail) {
            const char *rest = tail;
            while (*rest == '\\') ++rest;
            if (*rest) return DOS_E_FILENAME_RANGE;
        }
    }

    canonical[used++] = 'C';
    canonical[used++] = ':';
    canonical[used++] = '\\';
    for (i = 0; i < count; ++i) {
        size_t length = strlen(parts[i]);
        if (i) {
            if (used >= DOS_PATH_CHARS) return DOS_E_FILENAME_RANGE;
            canonical[used++] = '\\';
        }
        if (length > DOS_PATH_CHARS - used) return DOS_E_FILENAME_RANGE;
        memcpy(canonical + used, parts[i], length);
        used += length;
    }
    if (used > DOS_PATH_CHARS) return DOS_E_FILENAME_RANGE;
    canonical[used] = '\0';
    return 0;
}

static int dos_name_equal(const char *left, const char *right)
{
    while (*left && *right) {
        if (upper_ascii(*left++) != upper_ascii(*right++)) return 0;
    }
    return *left == 0 && *right == 0;
}

static int find_host_name(const char *parent, const char *dos_name,
                          char *host_name, size_t capacity)
{
    char pattern[HOST_PATH_CAPACITY];
    size_t parent_length = strlen(parent);
    WIN32_FIND_DATAA data;
    HANDLE search;
    int found = 0;
    if (parent_length + 5u > sizeof pattern) return 0;
    memcpy(pattern, parent, parent_length);
    if (parent_length && parent[parent_length - 1u] != '\\')
        pattern[parent_length++] = '\\';
    memcpy(pattern + parent_length, "*.*", 4u);
    search = FindFirstFileA(pattern, &data);
    if (search == INVALID_HANDLE_VALUE) return 0;
    do {
        const char *candidate = NULL;
        if (dos_name_equal(data.cFileName, dos_name)) candidate = data.cFileName;
        else if (data.cAlternateFileName[0] &&
                 dos_name_equal(data.cAlternateFileName, dos_name))
            candidate = data.cFileName;
        if (candidate) {
            size_t length = strlen(candidate);
            if (length < capacity) {
                memcpy(host_name, candidate, length + 1u);
                found = 1;
            }
            break;
        }
    } while (FindNextFileA(search, &data));
    FindClose(search);
    return found;
}

int16_t sim_drive_set_root(const char *path)
{
    DWORD length, attributes;
    char resolved[HOST_PATH_CAPACITY];
    if (!path || !*path) return 0;
    length = GetFullPathNameA(path, (DWORD)sizeof resolved, resolved, NULL);
    if (length == 0 || length >= sizeof resolved) return 0;
    attributes = GetFileAttributesA(resolved);
    if (attributes == INVALID_FILE_ATTRIBUTES ||
        !(attributes & FILE_ATTRIBUTE_DIRECTORY)) return 0;
    if (length > 3u && resolved[length - 1u] == '\\') resolved[length - 1u] = '\0';
    memcpy(host_root, resolved, strlen(resolved) + 1u);
    memset(drive_cwd, 0, sizeof drive_cwd);
    current_drive = DOS_DRIVE_C;
    root_ready = 1;
    return 1;
}

int16_t sim_drive_getdrive(void)
{
    return root_ready ? (int16_t)current_drive : 0;
}

int16_t sim_drive_setdrive(int16_t drive)
{
    if (!root_ready || drive != DOS_DRIVE_C) return -1;
    current_drive = DOS_DRIVE_C;
    return 0;
}

int16_t sim_drive_getcwd(int16_t drive, char *path, size_t capacity)
{
    char canonical[DOS_PATH_CHARS + 1u];
    unsigned selected;
    size_t length;
    if (!path || capacity == 0 || !root_ready || drive < 0 || drive > 26)
        return 0;
    selected = drive == 0 ? current_drive : (unsigned)drive;
    if (selected != DOS_DRIVE_C) return 0;
    canonical[0] = 'C';
    canonical[1] = ':';
    canonical[2] = '\\';
    memcpy(canonical + 3, drive_cwd[selected - 1u],
           strlen(drive_cwd[selected - 1u]) + 1u);
    length = strlen(canonical) + 1u;
    if (length > capacity) return 0;
    memcpy(path, canonical, length);
    return 1;
}

int16_t sim_drive_resolve_path(const char *path, char *host_path,
                               size_t capacity, int allow_wildcards,
                               uint16_t *dos_error)
{
    char canonical[DOS_PATH_CHARS + 1u];
    unsigned error, drive;
    size_t root_length, used;
    const char *relative, *cursor;

    if (dos_error) *dos_error = DOS_E_PATH_NOT_FOUND;
    if (!host_path || capacity == 0 || !root_ready) {
        if (dos_error) *dos_error = DOS_E_INVALID_DRIVE;
        return 0;
    }
    error = canonicalize(path, allow_wildcards, canonical, &drive);
    if (error) {
        if (dos_error) *dos_error = (uint16_t)error;
        return 0;
    }
    relative = canonical + 3;
    root_length = strlen(host_root);
    if (root_length + 1u > capacity || root_length + 1u > HOST_PATH_CAPACITY) {
        if (dos_error) *dos_error = DOS_E_FILENAME_RANGE;
        return 0;
    }
    memcpy(host_path, host_root, root_length);
    host_path[root_length] = '\0';
    used = root_length;
    cursor = relative;
    while (*cursor) {
        const char *end = strchr(cursor, '\\');
        size_t component_length = end ? (size_t)(end - cursor) : strlen(cursor);
        char component[13], matched[260];
        const char *chosen = cursor;
        size_t chosen_length = component_length;
        int wildcard = strchr(cursor, '*') != NULL || strchr(cursor, '?') != NULL;
        if (component_length >= sizeof component) {
            if (dos_error) *dos_error = DOS_E_FILENAME_RANGE;
            return 0;
        }
        memcpy(component, cursor, component_length);
        component[component_length] = '\0';
        if (!wildcard && find_host_name(host_path, component, matched,
                                         sizeof matched)) {
            chosen = matched;
            chosen_length = strlen(matched);
        }
        if (used && host_path[used - 1u] != '\\') {
            if (used + 1u >= capacity) goto too_long;
            host_path[used++] = '\\';
        }
        if (chosen_length >= capacity - used) goto too_long;
        memcpy(host_path + used, chosen, chosen_length);
        used += chosen_length;
        host_path[used] = '\0';
        if (!end) break;
        cursor = end + 1;
    }
    if (dos_error) *dos_error = 0;
    return 1;
too_long:
    if (dos_error) *dos_error = DOS_E_FILENAME_RANGE;
    return 0;
}

uint16_t sim_drive_chdir(const char *path)
{
    char canonical[DOS_PATH_CHARS + 1u];
    char host_path[HOST_PATH_CAPACITY];
    uint16_t error;
    unsigned drive;
    DWORD attributes;
    if (!path) return DOS_E_PATH_NOT_FOUND;
    error = (uint16_t)canonicalize(path, 0, canonical, &drive);
    if (error) return error;
    if (!sim_drive_resolve_path(path, host_path, sizeof host_path, 0, &error))
        return error;
    attributes = GetFileAttributesA(host_path);
    if (attributes == INVALID_FILE_ATTRIBUTES)
        return GetLastError() == ERROR_ACCESS_DENIED ? DOS_E_ACCESS_DENIED : DOS_E_PATH_NOT_FOUND;
    if (!(attributes & FILE_ATTRIBUTE_DIRECTORY)) return DOS_E_PATH_NOT_FOUND;
    memcpy(drive_cwd[drive - 1u], canonical + 3, strlen(canonical + 3) + 1u);
    return 0;
}

int16_t sim_drive_error_to_errno(uint16_t error)
{
    switch (error) {
    case 0: return 0;
    case DOS_E_FILE_NOT_FOUND:
    case DOS_E_PATH_NOT_FOUND: return 2;
    case DOS_E_ACCESS_DENIED: return 13;
    case DOS_E_INVALID_DRIVE: return 19;
    case DOS_E_FILENAME_RANGE: return 22;
    case DOS_E_OUT_OF_MEMORY: return 12;
    default: return 5;
    }
}

int16_t f_1F66_00AF(int16_t drive, char *path)
{
    return sim_drive_getcwd(drive, path, 67u);
}
