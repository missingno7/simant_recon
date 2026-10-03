#include "portable/whole_program/types/database.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
#ifdef EXPECT_UNGUARDED_CRASH
static LONG WINAPI detect_one_past_fault(PEXCEPTION_POINTERS info)
{
    if (info && info->ExceptionRecord &&
        info->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION)
        ExitProcess(86);
    return EXCEPTION_CONTINUE_SEARCH;
}
#endif
#endif

extern IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind);

static void empty_table(void)
{
    fd_50F6_3958[0].index = NULL;
    fd_50F6_3958[0].indexHeader.count = 0;
    fd_50F6_3956 = 0x1234;
    fd_50F6_3952 = (IndexEntry *)(uintptr_t)0x5678;
    assert(FindIndex(0, 0, 0) == NULL);
    assert(fd_50F6_3956 == 0);
    /* Source returns before assigning the cursor pointer on the empty path. */
    assert(fd_50F6_3952 == (IndexEntry *)(uintptr_t)0x5678);
}

static void singleton_and_invalid_queries(void)
{
    IndexEntry row[] = {{ 0x1234, INT16_MAX, 7, 0 }};
    fd_50F6_3958[0].index = row;
    fd_50F6_3958[0].indexHeader.count = 1;
    assert(FindIndex(0, INT16_MAX, 7) == &row[0]);
    assert(fd_50F6_3956 == 0);
    assert(FindIndex(0, INT16_MIN, 7) == NULL);
    assert(fd_50F6_3956 == 0);
    assert(FindIndex(0, INT16_MAX, 8) == NULL);
    assert(fd_50F6_3956 == 1);
    assert(fd_50F6_3952 == &row[1]); /* legal one-past pointer, never dereferenced */
    assert(FindIndex(0, INT16_MAX, 256) == NULL);
    assert(fd_50F6_3956 == 1);
}

static void multiple_rows_and_last_hit(void)
{
    IndexEntry rows[] = {
        { 0, -3, 2, 0 }, { 8, 4, 2, 0 }, { 16, 300, 2, 0 },
        { 24, -2, 9, 0 }
    };
    fd_50F6_3958[0].index = rows;
    fd_50F6_3958[0].indexHeader.count = 4;
    assert(FindIndex(0, 300, 2) == &rows[2]);
    assert(fd_50F6_3956 == 2);
    assert(FindIndex(0, 300, 10) == NULL);
    assert(fd_50F6_3956 == 4);
    assert(fd_50F6_3952 == &rows[4]);
}

#ifdef _WIN32
static void protected_one_past(void)
{
    SYSTEM_INFO info;
    DWORD old_protect;
    uint8_t *memory;
    size_t page;
    IndexEntry *row;
    GetSystemInfo(&info);
    page = (size_t)info.dwPageSize;
    memory = (uint8_t *)VirtualAlloc(NULL, page * 2,
        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    assert(memory);
    assert(VirtualProtect(memory + page, page, PAGE_NOACCESS, &old_protect));
    row = (IndexEntry *)(memory + page - sizeof(*row));
    row[0].offset = 1; row[0].id = 32760; row[0].kind = 6; row[0].flags = 0;
    fd_50F6_3958[0].index = row;
    fd_50F6_3958[0].indexHeader.count = 1;
    assert(FindIndex(0, 32761, 6) == NULL);
    assert(fd_50F6_3956 == 1);
    assert(fd_50F6_3952 == row + 1);
    VirtualFree(memory, 0, MEM_RELEASE);
}
#endif

int main(void)
{
#if defined(_WIN32) && defined(EXPECT_UNGUARDED_CRASH)
    if (!AddVectoredExceptionHandler(1, detect_one_past_fault)) return 87;
#endif
    empty_table();
    singleton_and_invalid_queries();
    multiple_rows_and_last_hit();
#ifdef _WIN32
    protected_one_past();
#endif
    puts("guarded FindIndex native boundary tests passed");
    return 0;
}
