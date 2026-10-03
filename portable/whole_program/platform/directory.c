#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "directory.h"

#include <limits.h>
#include <string.h>

#ifndef _WIN32
#error "The initial native directory provider requires Win32 FindFirstFile semantics"
#endif

#define DOS_A_RDONLY 0x01u
#define DOS_A_HIDDEN 0x02u
#define DOS_A_SYSTEM 0x04u
#define DOS_A_VOLID  0x08u
#define DOS_A_SUBDIR 0x10u
#define DOS_A_ARCH   0x20u

#define DOS_E_FILE_NOT_FOUND 2u
#define DOS_E_PATH_NOT_FOUND 3u
#define DOS_E_TOO_MANY_FILES 4u
#define DOS_E_ACCESS_DENIED  5u
#define DOS_E_INVALID_HANDLE 6u
#define DOS_E_NO_MORE_FILES 18u
#define DOS_E_FILENAME_RANGE 206u
#define DOS_E_FILE_TOO_LARGE 223u

#define MSC_EACCES 13
#define MSC_EBADF 9
#define MSC_EINVAL 22
#define MSC_EMFILE 24
#define MSC_ENOENT 2
#define MSC_EFBIG 27
#define MSC_EIO 5

#define SEARCH_SLOTS 32u
#define COOKIE_BYTES 12u

typedef struct SearchSlot {
    HANDLE handle;
    WIN32_FIND_DATAA current;
    DWORD generation;
    uint16_t attribute_mask;
    int wildcard_pattern;
    int active;
} SearchSlot;

static SearchSlot slots[SEARCH_SLOTS];
static DWORD next_generation = 1;

static uint16_t get_u16(const unsigned char *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t get_u32(const unsigned char *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static void put_u16(unsigned char *p, uint16_t value)
{
    p[0] = (unsigned char)value;
    p[1] = (unsigned char)(value >> 8);
}

static void put_u32(unsigned char *p, uint32_t value)
{
    p[0] = (unsigned char)value;
    p[1] = (unsigned char)(value >> 8);
    p[2] = (unsigned char)(value >> 16);
    p[3] = (unsigned char)(value >> 24);
}

static void clear_cookie(struct find_t *result)
{
    if (result != NULL) memset(result->reserved, 0, sizeof(result->reserved));
}

static int read_cookie(const struct find_t *result, unsigned *slot_index,
                       DWORD *generation)
{
    const unsigned char *p;
    unsigned index;
    DWORD gen;
    if (result == NULL) return 0;
    p = (const unsigned char *)result->reserved;
    if (p[0] != 'D' || p[1] != 'F' || p[2] != 'S' || p[3] != 1) return 0;
    index = get_u16(p + 4);
    gen = get_u32(p + 6);
    if (index >= SEARCH_SLOTS || gen == 0 || !slots[index].active ||
        slots[index].generation != gen)
        return 0;
    *slot_index = index;
    *generation = gen;
    return 1;
}

static void write_cookie(struct find_t *result, unsigned slot_index,
                         DWORD generation)
{
    unsigned char *p = (unsigned char *)result->reserved;
    memset(p, 0, sizeof(result->reserved));
    p[0] = 'D'; p[1] = 'F'; p[2] = 'S'; p[3] = 1;
    put_u16(p + 4, (uint16_t)slot_index);
    put_u32(p + 6, generation);
    put_u16(p + 10, (uint16_t)(slot_index ^ generation ^ 0xD05Au));
}

static int cookie_checksum_ok(const struct find_t *result)
{
    const unsigned char *p = (const unsigned char *)result->reserved;
    unsigned index = get_u16(p + 4);
    DWORD generation = get_u32(p + 6);
    return get_u16(p + 10) == (uint16_t)(index ^ generation ^ 0xD05Au);
}

static unsigned dos_error_from_win32(DWORD error)
{
    switch (error) {
    case ERROR_FILE_NOT_FOUND: return DOS_E_FILE_NOT_FOUND;
    case ERROR_PATH_NOT_FOUND: return DOS_E_PATH_NOT_FOUND;
    case ERROR_TOO_MANY_OPEN_FILES: return DOS_E_TOO_MANY_FILES;
    case ERROR_ACCESS_DENIED: return DOS_E_ACCESS_DENIED;
    case ERROR_INVALID_HANDLE: return DOS_E_INVALID_HANDLE;
    case ERROR_NO_MORE_FILES: return DOS_E_NO_MORE_FILES;
    case ERROR_FILENAME_EXCED_RANGE: return DOS_E_FILENAME_RANGE;
    case ERROR_FILE_TOO_LARGE: return DOS_E_FILE_TOO_LARGE;
    case ERROR_NOT_ENOUGH_MEMORY:
    case ERROR_OUTOFMEMORY: return 8u;
    default: return DOS_E_ACCESS_DENIED;
    }
}

static int msc_errno_from_dos(unsigned error)
{
    switch (error) {
    case 0: return 0;
    case DOS_E_FILE_NOT_FOUND:
    case DOS_E_PATH_NOT_FOUND:
    case DOS_E_NO_MORE_FILES: return MSC_ENOENT;
    case DOS_E_TOO_MANY_FILES: return MSC_EMFILE;
    case DOS_E_ACCESS_DENIED: return MSC_EACCES;
    case DOS_E_INVALID_HANDLE: return MSC_EBADF;
    case DOS_E_FILENAME_RANGE: return MSC_EINVAL;
    case DOS_E_FILE_TOO_LARGE: return MSC_EFBIG;
    case 87u: return MSC_EINVAL;
    default: return MSC_EIO;
    }
}

static unsigned set_error(unsigned error)
{
    dos_errno = (int16_t)msc_errno_from_dos(error);
    return (uint16_t)error;
}

static int valid_dos_83_name(const char *name)
{
    size_t base = 0, ext = 0;
    int seen_dot = 0;
    const unsigned char *p = (const unsigned char *)name;
    if (strcmp(name, ".") == 0 || strcmp(name, "..") == 0) return 1;
    if (*p == 0) return 0;
    for (; *p; ++p) {
        if (*p >= 0x80 || *p <= 0x20 || *p == '/' || *p == '\\' || *p == ':')
            return 0;
        if (*p == '.') {
            if (seen_dot || base == 0) return 0;
            seen_dot = 1;
            continue;
        }
        if (seen_dot) ++ext;
        else ++base;
    }
    return base <= 8 && (!seen_dot || (ext >= 1 && ext <= 3));
}

static int attributes_match(const WIN32_FIND_DATAA *data, uint16_t mask)
{
    DWORD attr = data->dwFileAttributes;
    if ((attr & FILE_ATTRIBUTE_HIDDEN) && !(mask & DOS_A_HIDDEN)) return 0;
    if ((attr & FILE_ATTRIBUTE_SYSTEM) && !(mask & DOS_A_SYSTEM)) return 0;
    if ((attr & FILE_ATTRIBUTE_DIRECTORY) && !(mask & DOS_A_SUBDIR)) return 0;
    return 1;
}

static int pack_timestamp(const FILETIME *utc, uint16_t *dos_date,
                          uint16_t *dos_time)
{
    FILETIME local;
    SYSTEMTIME st;
    unsigned year;
    if (!FileTimeToLocalFileTime(utc, &local) ||
        !FileTimeToSystemTime(&local, &st))
        return 0;
    year = st.wYear;
    if (year < 1980) {
        *dos_date = (uint16_t)((1u << 5) | 1u);
        *dos_time = 0;
        return 1;
    }
    if (year > 2107) {
        *dos_date = (uint16_t)((127u << 9) | (12u << 5) | 31u);
        *dos_time = (uint16_t)((23u << 11) | (59u << 5) | 29u);
        return 1;
    }
    *dos_date = (uint16_t)(((year - 1980u) << 9) | (st.wMonth << 5) | st.wDay);
    *dos_time = (uint16_t)((st.wHour << 11) | (st.wMinute << 5) |
                           (st.wSecond / 2u));
    return 1;
}

static int fill_result(const WIN32_FIND_DATAA *data, struct find_t *result)
{
    DWORD attr = data->dwFileAttributes;
    uint64_t size = ((uint64_t)data->nFileSizeHigh << 32) | data->nFileSizeLow;
    uint16_t date, time;
    unsigned char dos_attr = 0;
    if (!valid_dos_83_name(data->cFileName)) return 0;
    if (size > INT32_MAX) return -1;
    if (!pack_timestamp(&data->ftLastWriteTime, &date, &time)) return -2;
    if (attr & FILE_ATTRIBUTE_READONLY) dos_attr |= DOS_A_RDONLY;
    if (attr & FILE_ATTRIBUTE_HIDDEN) dos_attr |= DOS_A_HIDDEN;
    if (attr & FILE_ATTRIBUTE_SYSTEM) dos_attr |= DOS_A_SYSTEM;
    if (attr & FILE_ATTRIBUTE_DIRECTORY) dos_attr |= DOS_A_SUBDIR;
    if (attr & FILE_ATTRIBUTE_ARCHIVE) dos_attr |= DOS_A_ARCH;
    result->attrib = (char)dos_attr;
    result->wr_time = time;
    result->wr_date = date;
    result->size = (int32_t)size;
    memcpy(result->name, data->cFileName, strlen(data->cFileName) + 1);
    return 1;
}

static int find_next_acceptable(SearchSlot *slot, uint16_t mask,
                                struct find_t *result, int first)
{
    for (;;) {
        int converted;
        if (!first && !FindNextFileA(slot->handle, &slot->current)) return 0;
        first = 0;
        if (!attributes_match(&slot->current, mask)) continue;
        converted = fill_result(&slot->current, result);
        if (converted < 0) {
            SetLastError(converted == -1 ? ERROR_FILE_TOO_LARGE : ERROR_INVALID_DATA);
            return -1;
        }
        if (converted == 0) {
            if (slot->wildcard_pattern) continue;
            SetLastError(ERROR_FILENAME_EXCED_RANGE);
            return -1;
        }
        return 1;
    }
}

static void release_slot(unsigned index)
{
    if (slots[index].active) {
        FindClose(slots[index].handle);
        slots[index].handle = INVALID_HANDLE_VALUE;
        slots[index].active = 0;
    }
}

void dos_findclose(struct find_t *result)
{
    unsigned index;
    DWORD generation;
    if (read_cookie(result, &index, &generation) && cookie_checksum_ok(result))
        release_slot(index);
    clear_cookie(result);
    dos_errno = 0;
}

uint16_t _dos_findfirst(const char *pattern, uint16_t attributes,
                        struct find_t *result)
{
    WIN32_FIND_DATAA data;
    HANDLE handle;
    unsigned index;
    int found;
    if (result == NULL || pattern == NULL || *pattern == 0)
        return (uint16_t)set_error(87u);
    dos_findclose(result);
    clear_cookie(result);
    handle = FindFirstFileA(pattern, &data);
    if (handle == INVALID_HANDLE_VALUE)
        return (uint16_t)set_error(dos_error_from_win32(GetLastError()));
    for (index = 0; index < SEARCH_SLOTS; ++index)
        if (!slots[index].active) break;
    if (index == SEARCH_SLOTS) {
        FindClose(handle);
        return (uint16_t)set_error(DOS_E_TOO_MANY_FILES);
    }
    slots[index].handle = handle;
    slots[index].current = data;
    slots[index].attribute_mask = attributes;
    slots[index].wildcard_pattern = (strchr(pattern, '*') != NULL ||
                                     strchr(pattern, '?') != NULL);
    slots[index].active = 1;
    slots[index].generation = next_generation++;
    if (slots[index].generation == 0) slots[index].generation = next_generation++;
    found = find_next_acceptable(&slots[index], attributes, result, 1);
    if (found <= 0) {
        DWORD win_error = GetLastError();
        release_slot(index);
        clear_cookie(result);
        return (uint16_t)set_error(found == 0 ? DOS_E_FILE_NOT_FOUND :
                                    dos_error_from_win32(win_error));
    }
    write_cookie(result, index, slots[index].generation);
    dos_errno = 0;
    return 0;
}

uint16_t _dos_findnext(struct find_t *result)
{
    unsigned index;
    DWORD generation;
    int found;
    if (!read_cookie(result, &index, &generation) || !cookie_checksum_ok(result)) {
        clear_cookie(result);
        return (uint16_t)set_error(DOS_E_INVALID_HANDLE);
    }
    found = find_next_acceptable(&slots[index], slots[index].attribute_mask,
                                 result, 0);
    if (found > 0) {
        dos_errno = 0;
        return 0;
    }
    {
        DWORD error = GetLastError();
        release_slot(index);
        clear_cookie(result);
        return (uint16_t)set_error(found == 0 ? DOS_E_NO_MORE_FILES :
                                    dos_error_from_win32(error));
    }
}
