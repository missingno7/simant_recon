/*
 * Database file reader with an EMS page cache (root module, code frame 19DC).
 * No direct Win16 counterpart (DOS-only EMS layer).
 */

typedef struct {
    unsigned int age;
    int file;
    int page;
} EmsSlot;

extern signed char far fd_55B3_360C;
extern int far fd_55B3_3612;
extern char far * far fd_55B3_360E;
extern char far * far fd_50F6_3B48;
extern EmsSlot far * far * far fd_50F6_3B4C;

extern void far Punt(char far *format, ...);
extern void far DosPunt(char far *message);
extern int far atexit(void (far *func)(void));
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned int n);
extern long far lseek(int fd, long offset, int origin);
extern int far read(int fd, void far *buffer, unsigned int count);
extern void far f_195A_001D(void);
extern void far f_195A_0035(void);
extern int far f_195A_004B(int pages);
extern void far f_195A_0062(int handle, int logical, int physical);
extern void far f_195A_007D(int handle);
extern void far f_195A_01CB(int handle, char far *name);
extern int far f_195A_0260(void);
extern EmsSlot far * far * far f_2CFB_0002(long size, int flags, char far *name);

void far f_19DC_04B9(void);

static int s_8C74;
int g_389C = 0;
int g_389E = 0;
int g_38A0 = 0;

void far f_19DC_0008(void)
{
    if (g_389C)
        f_195A_007D(g_389C);
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_19DC_001A (EMS cache setup) draft: calls the RTLink thunk 2CFB:0002 (jmp 171C:13CA)
 * and the runtime long-shift helper 29F4:2F7A (__aFlshr), neither registered (see
 * REPORT.md), so it cannot bind yet. */
int far f_19DC_001A(long size)
{
    int i;
    EmsSlot far *slot;
    int pages;
    int avail;

    if (g_389C)
        return 1;
    if (!f_195A_0260())
        return 0;
    if (fd_55B3_360C < 0x40)
        return 0;
    f_195A_0035();
    pages = (int)((size + 0x3FFF) >> 14);
    avail = fd_55B3_3612 - g_38A0;
    g_389E = avail > pages ? pages : avail;
    if (g_389E < 8) {
        g_389E = 0;
        return 0;
    }
    f_195A_001D();
    g_389C = f_195A_004B(g_389E);
    f_195A_01CB(g_389C, "DBEMSXXX");
    fd_50F6_3B48 = fd_55B3_360E - 0x4000;
    fd_50F6_3B4C = f_2CFB_0002((long)g_389E * 6, 0, "DBEMSLIST");
    slot = *fd_50F6_3B4C;
    for (i = 0; i < g_389E; i++) {
        slot->age = 0;
        slot->file = slot->page = -1;
    }
    f_195A_0062(g_389C, 0, 3);
    atexit(f_19DC_0008);
    return 1;
}
/* SCAFFOLD END */

int g_38B6 = -1;
int g_38B8 = -1;
int g_38BA = -1;

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_19DC_0148 (EMS page lookup) draft: uses the runtime long-shift helper 29F4:2F6E
 * (__aFlshl), not registered, so it cannot bind yet. */
char far * far f_19DC_0148(int file, int page)
{
    EmsSlot far *slot;
    int i;
    int freeSlot;
    int found;
    unsigned int oldest;
    int oldestSlot;

    freeSlot = -1;
    found = 0;
    oldest = 0;
    if (file == g_38B8 && page == g_38BA)
        return fd_50F6_3B48;
    slot = *fd_50F6_3B4C;
    for (i = 0; i < g_389E; i++, slot++) {
        if (slot->file == -1) {
            freeSlot = i;
            continue;
        }
        if (slot->file == file && slot->page == page) {
            f_195A_0062(g_389C, i, 3);
            g_38B6 = i;
            slot->age = 0;
            found = 1;
        }
        if (slot->age < 0xFFFF)
            slot->age++;
        if (slot->age > oldest) {
            oldest = slot->age;
            oldestSlot = i;
        }
    }
    if (!found) {
        i = freeSlot;
        if (i == -1)
            i = oldestSlot;
        slot = &(*fd_50F6_3B4C)[i];
        slot->file = file;
        slot->page = page;
        f_195A_0062(g_389C, i, 3);
        g_38B6 = i;
        slot->age = 0;
        while (lseek(file, (long)page << 14, 0) == -1L)
            f_19DC_04B9();
        for (;;) {
            if (read(file, fd_50F6_3B48, 0x4000) != -1)
                break;
            f_19DC_04B9();
        }
    }
    g_38B8 = file;
    g_38BA = page;
    return fd_50F6_3B48;
}
/* SCAFFOLD END */


static long s_8C76;

int far f_19DC_02FB(int file, long offset, char far *buffer, long count);

void far f_19DC_02D9(int file, char far *buffer, long count)
{
    f_19DC_02FB(file, s_8C76, buffer, count);
}

int g_390C = 0;

#define CHECK_FILE() if (s_8C74 != file) Punt("Handle mismatch")

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_19DC_02FB (positioned read through the EMS cache) draft: uses the runtime
 * long-shift helper 29F4:2F7A (__aFlshr), not registered, so it cannot bind yet. */
int far f_19DC_02FB(int file, long offset, char far *buffer, long count)
{
    int page;
    unsigned int off;
    unsigned int chunk;
    unsigned int done;
    unsigned int left;
    char far *src;

    s_8C76 = offset + count;
    s_8C74 = file;
    if (count == 0L)
        return 0;
    if (g_390C || !f_19DC_001A(500000L))
        goto plain;
    page = (int)(offset >> 14);
    off = (unsigned int)offset & 0x3FFF;
    chunk = 0x4000 - off;
    if (chunk > count)
        chunk = (unsigned int)count;
    CHECK_FILE();
    _fmemcpy(buffer, f_19DC_0148(file, page) + off, chunk);
    page++;
    done = chunk;
    left = (unsigned int)count - chunk;
    while (left >= 0x4000) {
        CHECK_FILE();
        src = f_19DC_0148(file, page);
        CHECK_FILE();
        _fmemcpy(buffer + done, src, 0x4000);
        done += 0x4000;
        page++;
        left -= 0x4000;
    }
    if (left) {
        CHECK_FILE();
        src = f_19DC_0148(file, page);
        CHECK_FILE();
        _fmemcpy(buffer + done, src, left);
    }
    return;
plain:
    g_390C = 1;
    lseek(file, offset, 0);
    return read(file, buffer, (unsigned int)count);
}
/* SCAFFOLD END */

void far f_19DC_04B9(void)
{
    DosPunt("Database error");
}
