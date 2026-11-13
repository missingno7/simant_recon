/*
 * Reads database files through an EMS page cache. It tracks cached pages and validates handles
 * before returning record data.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 19DC; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oeg /Gs /Zi.
 */

typedef struct {
    unsigned int age;
    int file;
    int page;
} EmsSlot;

extern signed char far ems_version;
extern int far ems_free_page_count;
extern char far * far ems_page_frame_pointer;
extern char far * far db_ems_page_buffer;
extern EmsSlot far * far * far db_ems_slot_list_handle;

extern void far Punt(char far *format, ...);
extern void far DosPunt(char far *message);
extern int far atexit(void (far *func)(void));
extern void far * far _fmemcpy(void far *dst, void far *src, int n);
extern long far lseek(int fd, long offset, int origin);
extern int far read(int fd, void far *buffer, unsigned int count);
extern void far ems_query_page_frame(void);
extern void far ems_query_page_counts(void);
extern int far ems_allocate_pages(int pages);
extern void far ems_map_page(int handle, int logical, int physical);
extern void far ems_free_handle(int handle);
extern void far ems_set_handle_name(int handle, char far *name);
extern int far ems_initialize(void);
extern EmsSlot far * far * far f_2CFB_0002(long size, int flags, char far *name);

void far db_report_read_error(void);

static int s_8C74;
int g_389C = 0;
int g_389E = 0;
int g_38A0 = 0;

void far db_free_ems_cache(void)
{
    if (g_389C)
        ems_free_handle(g_389C);
}

int far db_init_ems_cache(long size)
{
    int i;
    EmsSlot far *slot;
    int pages;
    int avail;

    if (g_389C)
        return 1;
    if (!ems_initialize() || ems_version < 0x40)
        return 0;
    ems_query_page_counts();
    pages = (int)((size + 0x3FFF) >> 14);
    avail = ems_free_page_count - g_38A0;
    g_389E = avail > pages ? pages : avail;
    if (g_389E < 8) {
        g_389E = 0;
        return 0;
    }
    ems_query_page_frame();
    g_389C = ems_allocate_pages(g_389E);
    ems_set_handle_name(g_389C, "DBEMSXXX");
    db_ems_page_buffer = ems_page_frame_pointer - 0x4000;
    db_ems_slot_list_handle = f_2CFB_0002((long)g_389E * 6, 0, "DBEMSLIST");
    slot = *db_ems_slot_list_handle;
    for (i = 0; i < g_389E; i++) {
        slot->age = 0;
        slot->file = slot->page = -1;
    }
    ems_map_page(g_389C, 0, 3);
    atexit(db_free_ems_cache);
    return 1;
}

int g_38B6 = -1;
int g_38B8 = -1;
int g_38BA = -1;

char far * far db_get_ems_page(int file, int page)
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
        return db_ems_page_buffer;
    slot = *db_ems_slot_list_handle;
    for (i = 0; i < g_389E; i++, slot++) {
        if (slot->file == -1) {
            freeSlot = i;
            continue;
        }
        if (slot->file == file && slot->page == page) {
            ems_map_page(g_389C, i, 3);
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
        slot = &(*db_ems_slot_list_handle)[i];
        slot->file = file;
        slot->page = page;
        ems_map_page(g_389C, i, 3);
        g_38B6 = i;
        slot->age = 0;
        while ((int)lseek(file, (long)page << 14, 0) == -1)
            db_report_read_error();
        for (;;) {
            if (read(file, db_ems_page_buffer, 0x4000) != -1)
                break;
            db_report_read_error();
        }
    }
    g_38B8 = file;
    g_38BA = page;
    return db_ems_page_buffer;
}


static long s_8C76;

int far db_read_cached_range(int file, long offset, char far *buffer, long count);

void far db_read_at_cursor(int file, char far *buffer, long count)
{
    db_read_cached_range(file, s_8C76, buffer, count);
}

int g_390C = 0;

#define CHECK_FILE() if (s_8C74 != file) Punt("Handle mismatch")

int far db_read_cached_range(int file, long offset, char far *buffer, long count)
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
    if (g_390C || !db_init_ems_cache(500000L))
        goto plain;
    page = (int)(offset >> 14);
    off = (unsigned int)offset & 0x3FFF;
    chunk = 0x4000 - off;
    if (chunk > count)
        chunk = (unsigned int)count;
    CHECK_FILE();
    _fmemcpy(buffer, db_get_ems_page(file, page) + off, chunk);
    page++;
    done = chunk;
    left = (unsigned int)count - chunk;
    while (left >= 0x4000) {
        CHECK_FILE();
        src = db_get_ems_page(file, page);
        CHECK_FILE();
        _fmemcpy(buffer + done, src, 0x4000);
        done += 0x4000;
        page++;
        left -= 0x4000;
    }
    if (left) {
        CHECK_FILE();
        src = db_get_ems_page(file, page);
        CHECK_FILE();
        _fmemcpy(buffer + done, src, left);
    }
    return;
plain:
    g_390C = 1;
    lseek(file, offset, 0);
    return read(file, buffer, (unsigned int)count);
}

void far db_report_read_error(void)
{
    DosPunt("Database error");
}
