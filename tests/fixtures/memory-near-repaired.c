/*
 * Relocatable memory manager ("Ralloc") (root module, code frame 171C).
 * Blocks are paragraph aligned with a 32-byte header; a handle is a far pointer
 * to a far master pointer (the block data, header segment + 2).  Handles may also
 * be passed as indexes encoded as 0F0F:index.
 */

#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <io.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdarg.h>

#define SEG(p) ((unsigned long)(p) >> 16)
#define OFF(p) ((unsigned)(p))

typedef struct {
    int handle;                 /* +00 offset of the master pointer */
    long size;                  /* +02 requested size in bytes */
    unsigned paras;             /* +06 size in paragraphs incl. header */
    unsigned char type;         /* +08 */
    unsigned char lock;         /* +09 */
    long age;                   /* +0A */
    unsigned next;              /* +0E free list: next block segment */
    unsigned prev;              /* +10 free list: previous block segment */
    unsigned char attr;         /* +12 */
    char name[13];              /* +13 */
} Block;

typedef char far * far *Handle;

#define BLK(s) ((Block far *)((unsigned long)(s) << 16))
#define HDR(h) BLK(SEG(*(h)) - 2)
#define NEXTBLK(p) BLK((p)->paras + SEG(p))

#define CHECKH(h) \
    if (SEG(h) == 0xF0F) { \
        int i = OFF(h); \
        if (i >= 0 && i < g_2F42) \
            h = s_2F46 - i - 1; \
        else \
            Punt("RL5: Invalid handle index"); \
    }

#define INIT() if (!s_2F34) mem_init_movable_heap()

extern signed char far ems_version;
extern int far ems_free_page_count;
extern char far * far ems_page_frame_pointer;
extern unsigned far mem_ems_arena_start_segment;
extern unsigned far mem_ems_arena_paragraphs;
extern unsigned far mem_ems_boundary_segment;
extern char far * far mem_discard_entry_template;
extern unsigned near mem_conventional_paragraphs;
extern unsigned near mem_arena_start_segment;
extern Block far * near mem_arena_first_block;
extern Block far * near mem_arena_end_pointer;
extern Block far * near mem_free_list_cursor;

extern void far Punt(char far *format, ...);
extern void far WinPrintf(char far *format, ...);
extern void far ems_query_page_frame(void);
extern void far ems_query_page_counts(void);
extern int far ems_allocate_pages(int pages);
extern void far ems_map_page(int handle, int logical, int physical);
extern void far ems_free_handle(int handle);
extern void far ems_set_handle_name(int handle, char far *name);
extern int far ems_initialize(void);
extern void far mem_copy_paragraphs(void far *dst, void far *src, unsigned paras);

extern int g_2F44;
extern int g_2F42;

static char b_8C62[14];
static unsigned s_8C70;
static unsigned s_8C72;

static int s_2F2A = 0;
static int s_2F2C = 0;
static int s_2F2E = 0;
static long s_2F30 = 0L;
static int s_2F34 = 0;
static unsigned s_2F36 = 0;
static unsigned s_2F38 = 0;
static unsigned s_2F3A = 0;
static unsigned s_2F3C = 0;
static unsigned s_2F3E = 0;
static unsigned s_2F40 = 0;
int g_2F42 = 0;
int g_2F44 = 0;
static Handle s_2F46 = 0L;
static int s_2F4A = 300;
static int s_2F4C = 0;
static Block s_2F4E = { 0, 0L, 0, 5 };
static int s_2F6E = 0;

void far mem_init_movable_heap(void);
Block far * far mem_free_and_coalesce(Block far *b, int merge);
void far mem_carve_free_block(Block far *b, unsigned paras, int type);
Block far * far mem_find_free_block(unsigned paras, int type, char far *name, int noems);
Block far * far mem_allocate_high_block(unsigned paras, int type);
void far mem_find_free_list_neighbors(Block far *b);
void far mem_release_handle_slot(Handle h);
Handle far Ralloc(long size, int flags, char far *name);
void far RallocFree(Handle h);
void far RallocSetType(Handle h, int flags);
void far mem_discard_handle(Handle h);
Handle far RallocRealloc(Handle h, long size, int flags);
Handle far mem_lock_handle(Handle h);
Handle far mem_unlock_encoded_handle(Handle h);
Handle far mem_handle_from_pointer(char far *p);
char far * far mem_malloc_bridge(unsigned size);

void far mem_abort_with_alloc_context(char far *where)
{
    Punt("MemPunt @%s after %s", where, (char far *)b_8C62);
}

void far f_171C_001E(void)
{
}

void far mem_free_ems_heap(void)
{
    if (s_2F6E)
        ems_free_handle(s_2F6E);
}

int far mem_init_ems_heap(void)
{
    if (s_2F6E)
        return 1;
    if (ems_initialize()) {
        if (ems_version >= 0x40) {
            ems_query_page_counts();
            if (ems_free_page_count >= 3) {
                ems_query_page_frame();
                mem_ems_arena_start_segment = FP_SEG(ems_page_frame_pointer) + 1;
                s_2F6E = ems_allocate_pages(3);
                mem_ems_arena_paragraphs = 0xBF8;
                ems_set_handle_name(s_2F6E, "RALLOCXX");
                ems_map_page(s_2F6E, 0, 0);
                ems_map_page(s_2F6E, 1, 1);
                ems_map_page(s_2F6E, 2, 2);
                atexit(mem_free_ems_heap);
                return 1;
            }
        }
    }
    return 0;
}

char far * far mem_type_name(int type)
{
    switch (type) {
    case 3:
        return "SOFT";
    case 1:
        return "FIRM";
    case 0:
        return "HARD";
    case 5:
        return "DISCARDED";
    case 0x80:
        return "FREE";
    case 2:
        return "SYSTEM";
    }
    return "BAD";
}

Block far * far mem_free_and_coalesce(Block far *b, int merge)
{
    unsigned paras;
    Block far *next;
    Block far *prev;

    paras = b->paras;
    switch (b->type) {
    case 0:
        s_2F36 -= paras;
        break;
    case 1:
        s_2F3A -= paras;
        break;
    case 3:
        s_2F38 -= paras;
        break;
    case 5:
        break;
    default:
        Punt("Free illegal type");
        break;
    }
    s_2F3E += paras;
    s_2F3C -= paras;
    if (mem_free_list_cursor == 0L) {
        mem_free_list_cursor = b;
        b->next = b->prev = 0;
    } else {
        mem_find_free_list_neighbors(b);
        next = BLK(b->next);
        prev = BLK(b->prev);
        b->type = 0x80;
        if (prev)
            prev->next = SEG(b);
        if (merge && prev && NEXTBLK(prev) == b) {
            prev->paras += b->paras;
            prev->next = b->next;
            b = prev;
        }
        if (next)
            next->prev = SEG(b);
        if (BLK((unsigned)SEG(b) + (unsigned long)b->paras) == next) {
            b->next = next->next;
            b->paras += next->paras;
            next = BLK(next->next);
            if (next)
                next->prev = SEG(b);
        }
        if (b->prev == 0)
            mem_free_list_cursor = b;
    }
    return b;
}

void far mem_dump_printf(int fd, char far *format, ...)
{
    char buffer[300];

    vsprintf(buffer, format, (char far *)(&format + 1));
    write(fd, buffer, _fstrlen(buffer));
}

void far mem_dump_heap(char far *where)
{
    int x;
    int y;
    int n;
    int fd;
    Handle h;
    Block far *b;
    long now;
    char name[30];

    if (s_2F2A)
        return;
    fd = open("ralloc.dmp", 0x109, 0x180);
    time(&now);
    mem_dump_printf(fd, "\n\nRalloc dump at %s, %s", where, asctime(localtime(&now)));
    mem_dump_printf(fd, "\nFree Space:  %ld,  Used Space:  %ld, Total Space: %ld \n",
                (unsigned long)s_2F3E << 4, (unsigned long)s_2F3C << 4, (unsigned long)s_2F40 << 4);
    mem_dump_printf(fd, "Hard space:  %ld,  Firm space:  %ld, Soft Space : %ld\n",
                (unsigned long)s_2F36 << 4, (unsigned long)s_2F3A << 4, (unsigned long)s_2F38 << 4);
    mem_dump_printf(fd, "Handles allocated: %d,  handles used: %d max: %d", g_2F42, g_2F44, s_2F4C);
    h = s_2F46 - 1;
    n = g_2F44;
    mem_dump_printf(fd, "\nBy handles: \n");
    while (n) {
        if (*h) {
            _fstrncpy(name, HDR(h)->name, 29);
            name[29] = 0;
            b = HDR(h);
            mem_dump_printf(fd, "%p->%p: size=%ld, type=%c%s age=%5ld name=%s\n",
                        h, *h, (unsigned long)b->paras << 4, b->lock ? '*' : ' ',
                        mem_type_name(b->type), s_2F30 - b->age, (char far *)name);
            n--;
        }
        h--;
    }
    mem_dump_printf(fd, "\n\nBy location:\n");
    for (b = mem_arena_first_block; SEG(b) < SEG(mem_arena_end_pointer); b = BLK(SEG(b) + b->paras)) {
        _fstrncpy(name, b->name, 13);
        name[13] = 0;
        h = (Handle)((char far *)s_2F46 + b->handle);
        switch (b->type) {
        case 2:
        case 5:
        case 0x80:
            mem_dump_printf(fd, "----:----->%p:", (char far *)((long)b + 0x20000L));
            break;
        default:
            mem_dump_printf(fd, "%p->%p:", h, *h);
            break;
        }
        mem_dump_printf(fd, "size=%x, %ld, type=%c%s", b->paras, (unsigned long)b->paras << 4,
                    HDR(h)->lock ? '*' : ' ', mem_type_name(b->type));
        mem_dump_printf(fd, " age=%5ld name=%s\n", s_2F30 - b->age, (char far *)name);
    }
    close(fd);
}

void far f_171C_0674(void)
{
}

void far f_171C_0676(void)
{
}

void far mem_release_dos_heap(void)
{
    _dos_freemem(mem_arena_start_segment);
    s_2F34 = 0;
}

void far mem_carve_free_block(Block far *b, unsigned paras, int type)
{
    unsigned seg;
    Block far *next;
    Block far *prev;
    Block far *nb;

    next = BLK(b->next);
    prev = BLK(b->prev);
    if (b->paras - 2 > paras) {
        seg = SEG(b) + paras;
        if (prev)
            prev->next = seg;
        else
            mem_free_list_cursor = BLK(seg);
        if (next)
            next->prev = seg;
        nb = BLK(seg);
        *nb = *b;
        nb->type = 0x80;
        nb->paras = b->paras - paras;
    } else {
        if (prev)
            prev->next = SEG(next);
        else
            mem_free_list_cursor = next;
        if (next)
            next->prev = SEG(prev);
        paras = b->paras;
    }
    b->type = type;
    b->paras = paras;
    b->age = 0;
    s_2F3E -= paras;
    s_2F3C += paras;
    switch (type) {
    case 0:
        s_2F36 += paras;
        break;
    case 1:
        s_2F3A += paras;
        break;
    case 3:
        s_2F38 += paras;
        break;
    case 2:
        break;
    default:
        Punt("RallocSetSpace to illegal type");
        break;
    }
}

void far mem_init_movable_heap(void)
{
    Block far *b;

    if (s_2F34)
        return;
    s_2F34 = 1;
    if (_dos_allocmem(0xFF00, &mem_conventional_paragraphs)) {
        mem_conventional_paragraphs -= 0x10;
        _dos_allocmem(mem_conventional_paragraphs, &mem_arena_start_segment);
        mem_conventional_paragraphs -= 0x10;
    } else
        exit(1);
    s_8C72 = (s_2F4A * 4 + 15) / 16;
    s_2F46 = (Handle)(((unsigned long)s_8C72 + mem_arena_start_segment - 0x1000) << 16);
    mem_conventional_paragraphs -= s_8C72 + 1;
    mem_arena_start_segment += s_8C72 + 1;
    mem_free_list_cursor = mem_arena_first_block = BLK(mem_arena_start_segment);
    mem_free_list_cursor->type = 0x80;
    mem_free_list_cursor->next = 0;
    mem_free_list_cursor->prev = 0;
    if (mem_init_ems_heap()) {
        mem_free_list_cursor->paras = s_2F40 = s_2F3E = mem_ems_arena_paragraphs + mem_ems_arena_start_segment - mem_arena_start_segment;
        mem_arena_end_pointer = BLK(s_2F3E + SEG(BLK(mem_arena_start_segment)));
        s_8C70 = SEG(mem_arena_end_pointer);
        mem_ems_boundary_segment = SEG(BLK(mem_arena_start_segment)) + mem_conventional_paragraphs - 2;
        mem_carve_free_block(BLK(mem_arena_start_segment), mem_conventional_paragraphs - 2, 0);
        mem_carve_free_block(BLK(mem_arena_start_segment + mem_conventional_paragraphs - 2), mem_ems_arena_start_segment - mem_arena_start_segment - mem_conventional_paragraphs + 2, 2);
        mem_free_and_coalesce(BLK(mem_arena_start_segment), 0);
    } else {
        mem_free_list_cursor->paras = s_2F40 = s_2F3E = mem_conventional_paragraphs;
        mem_arena_end_pointer = BLK(s_2F3E + mem_arena_start_segment);
        mem_ems_boundary_segment = s_8C70 = SEG(mem_arena_end_pointer);
    }
    _fmemset(s_2F46 - s_2F4A, 0, s_2F4A * 4);
    mem_discard_entry_template = *Ralloc(0x20L, 0, "DiscardEntry");
    _fmemcpy(mem_discard_entry_template, &s_2F4E, 0x20);
    atexit(mem_release_dos_heap);
}

/* SCAFFOLD BEGIN: draft; residue: register allocation (original keeps paras in DI, next block pointer in memory with two copies [bp-0Ah]/[bp-2]) */
int far mem_resize_in_place(Handle h, unsigned paras, int type)
{
    Block far *b;
    Block far *next;

    b = HDR(h);
    if (b->paras > paras) {
        if (b->paras < paras + 0x20)
            return 1;
    } else {
        next = BLK(SEG(b) + b->paras);
        if (SEG(next) >= SEG(mem_arena_end_pointer) || next->type != 0x80 || next->paras + b->paras < paras)
            return 0;
    }
    mem_carve_free_block(mem_free_and_coalesce(b, 0), paras, type);
    return 1;
}
/* SCAFFOLD END */

Handle far mem_claim_handle_slot(void)
{
    Handle h;
    int i;

    if (s_2F4A - 1 <= g_2F42)
        Punt("ALL MEMORY HANDLES USED");
    if (g_2F42 < g_2F44)
        Punt("HANDLES USED > HANDLES ALLOCATED");
    h = s_2F46 - 1;
    for (i = 0; i < g_2F42 + 1; i++, h--) {
        if (!*h) {
            if (++g_2F44 > g_2F42)
                g_2F42 = g_2F44;
            return h;
        }
    }
    Punt("Handle free - but none found");
}

/* SCAFFOLD BEGIN: draft; residue: original keeps the long local seg in memory ([bp-28h]); MSC here enregisters it in SI:DI */
void far mem_slide_next_block_down(Block far *b)
{
    Block far *n;
    Block save;
    unsigned long seg;

    save = *b;
    seg = SEG(b);
    mem_copy_paragraphs(b, NEXTBLK(b), NEXTBLK(b)->paras);
    *(Handle)((char far *)s_2F46 + b->handle) = (char far *)((unsigned long)b + 0x20000L);
    b = BLK(b->paras + seg);
    *b = save;
    if (b->prev)
        BLK(b->prev)->next = SEG(b);
    else
        mem_free_list_cursor = b;
    if (b->next) {
        n = BLK(b->next);
        if (b->next - b->paras == (unsigned)SEG(b)) {
            b->next = n->next;
            b->paras += n->paras;
            n = BLK(b->next);
        }
        if (n)
            n->prev = SEG(b);
    }
}
/* SCAFFOLD END */

int far mem_discard_oldest_soft_block(int emsOnly)
{
    Block far *b;
    unsigned long oldest;
    Handle h;
    int n;
    Handle found;

    oldest = 0;
    found = 0L;
    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h) {
            b = HDR(h);
            if ((!emsOnly || (unsigned)SEG(b) < mem_ems_boundary_segment) && b->type == 3 && s_2F30 - b->age >= oldest && !b->lock) {
                oldest = s_2F30 - b->age;
                found = h;
            }
            n--;
        }
    }
    if (found) {
        WinPrintf("OLDESTH=%p", found);
        b = HDR(found);
        *found = (char far *)((long)mem_discard_entry_template + 0x20000L);
        mem_free_and_coalesce(b, 1);
        return 1;
    }
    return 0;
}

int far mem_compact_region(int emsOnly)
{
    int t;
    unsigned seg;
    long size;
    unsigned paras;
    Block far *n;
    unsigned end;
    Block far *b;
    unsigned long moved;
    Block far *nb;

    moved = 0;
    b = mem_arena_first_block;
    end = emsOnly ? mem_ems_boundary_segment : s_8C70;
    for (; (seg = (unsigned)SEG(b)) < end; b = BLK(b->paras + seg)) {
        if (b->type != 0x80)
            continue;
        n = BLK(b->paras + seg);
        if ((unsigned)SEG(n) < end && (t = n->type, !n->lock) && (t == 1 || t == 3) && !(n->attr & 0x10)) {
            mem_slide_next_block_down(b);
            continue;
        }
        while ((unsigned)SEG(n) < end) {
            if ((t = n->type, !n->lock) && (t == 1 || t == 3) && b->paras >= n->paras)
                goto found;
            n = BLK((unsigned)SEG(n) + (unsigned long)n->paras);
        }
        continue;
found:
        paras = n->paras;
        size = n->size;
        mem_carve_free_block(b, paras, t);
        _fmemcpy(b->name, n->name, 13);
        nb = b;
        nb->size = size;
        mem_copy_paragraphs((char far *)((long)nb + 0x20000L), (char far *)((long)n + 0x20000L), paras - 2);
        nb->handle = n->handle;
        nb->age = n->age;
        nb->attr = n->attr;
        _disable();
        *(Handle)((char far *)s_2F46 + nb->handle) = (char far *)((long)nb + 0x20000L);
        _enable();
        mem_free_and_coalesce(n, 1);
        moved = 1;
    }
    return *(int near *)&moved;
}

int far mem_compact_any_region(void)
{
    return mem_compact_region(0);
}

Block far * far mem_find_free_block(unsigned paras, int type, char far *name, int noems)
{
    Block far *b;
    char buffer[100];

    for (;;) {
        for (b = mem_free_list_cursor; b; b = BLK(b->next)) {
            if (noems && SEG(b) >= mem_ems_boundary_segment)
                break;
            if (b->paras >= paras)
                return b;
        }
        if (s_2F3E > paras && mem_compact_region(noems))
            continue;
        if (!mem_discard_oldest_soft_block(noems) || s_2F3E + s_2F38 <= paras)
            break;
        while (mem_discard_oldest_soft_block(noems) && s_2F3E < paras)
            ;
    }
    sprintf(buffer, "Cannot find a big enough space! (%ld bytes) @ %s", (unsigned long)paras << 4, name);
    Punt(buffer);
}

/* SCAFFOLD BEGIN: draft; residue: register allocation (original: SI for inner-loop block/size/result, DI for best/paras by region) and frame layout */
Block far * far mem_allocate_high_block(unsigned paras, int type)
{
    int first;
    Block far *b;
    Block far *best;
    int compacted;
    Block far *n;
    char buffer[100];

    first = 1;
    compacted = 0;
    for (;;) {
        best = mem_free_list_cursor;
        for (b = mem_free_list_cursor; b; b = BLK(b->next))
            if (b->paras >= paras)
                best = b;
        if (best && best->paras >= paras) {
            if (first) {
                for (n = BLK(SEG(best) + best->paras); SEG(n) < s_8C70; n = BLK(SEG(n) + n->paras))
                    if (!n->lock && (n->type == 1 || n->type == 3 || n->type == 0x80))
                        goto again;
            }
            if (best->paras > paras + 4) {
                WinPrintf("<SPLIT>");
                mem_carve_free_block(best, best->paras - paras, 0);
                n = BLK(SEG(best) + best->paras);
                mem_carve_free_block(n, paras, type);
                mem_free_and_coalesce(best, 1);
                return n;
            }
            WinPrintf("<WHOLE>");
            mem_carve_free_block(best, paras, type);
            return best;
        }
        if (!first) {
            sprintf(buffer, "Cannot find a big enough space! (%ld bytes)", (unsigned long)paras << 4);
            Punt(buffer);
        }
again:
        if (!compacted) {
            WinPrintf("<CL>");
            if (s_2F3E > paras && mem_compact_region(0)) {
                first = compacted = 1;
                continue;
            }
        }
        WinPrintf("<FO>");
        compacted = 0;
        if (mem_discard_oldest_soft_block(0) && s_2F3E + s_2F38 > paras) {
            WinPrintf("<FO2>");
            while (mem_discard_oldest_soft_block(0) && s_2F3E < paras)
                ;
            first = 1;
        } else
            first = 0;
    }
}
/* SCAFFOLD END */

void far mem_find_free_list_neighbors(Block far *b)
{
    Block far *cur;
    Block far *prev;

    cur = mem_free_list_cursor;
    prev = 0L;
    while ((unsigned)SEG(b) > SEG(cur)) {
        if (!cur)
            break;
        prev = cur;
        cur = BLK(cur->next);
    }
    b->prev = SEG(prev);
    b->next = SEG(cur);
}

void far mem_release_handle_slot(Handle h)
{
    g_2F44--;
    *h = 0L;
}

Handle far mem_alloc_handle_block(long size, int flags, char far *name, int unused)
{
    int noems;
    unsigned paras;
    Handle h;
    Block far *b;

    noems = flags & 8;
    flags &= ~8;
    if (size == 0)
        Punt("ALLOC 0 BYTES");
    INIT();
    _fstrncpy(b_8C62, name, 13);
    b_8C62[13] = 0;
    paras = ((unsigned)size + 15) >> 4;
    b = mem_find_free_block(paras + 2, flags & ~0x78, name, noems);
    if (noems)
        WinPrintf("\nNOEMS - memPtr=%p", b);
    h = mem_claim_handle_slot();
    if (!h)
        Punt("Could not allocate handle");
    *h = (char far *)((long)b + 0x20000L);
    mem_carve_free_block(b, paras + 2, flags & ~0x78);
    b->handle = OFF(h);
    b->lock = 0;
    _fstrncpy(b->name, name, 12);
    b->name[12] = 0;
    HDR(h)->size = size;
    HDR(h)->age = s_2F30++;
    HDR(h)->attr = flags & 0x78;
    return h;
}

Handle far Ralloc(long size, int flags, char far *name)
{
    return mem_alloc_handle_block(size, flags, name);
}

void far RallocFree(Handle h)
{
    Block far *b;
    char name[13];

    INIT();
    CHECKH(h);
    b = HDR(h);
    if (b->type != 5)
        mem_free_and_coalesce(b, 1);
    if (HDR(h)->lock) {
        _fmemcpy(name, b->name, 13);
        name[12] = 0;
        Punt("LOCKED FREED %s", (char far *)name);
    }
    HDR(h)->lock = 0;
    mem_release_handle_slot(h);
}

long far mem_handle_age_delta(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->age - s_2F30;
}

void far RallocFreshen(Handle h)
{
    INIT();
    CHECKH(h);
    HDR(h)->age = s_2F30++;
}

void far RallocSetType(Handle h, int flags)
{
    long paras;
    volatile int type;

    INIT();
    if (SEG(h) == 0xF0F)
        Punt("RL6: Handle must be locked before this operation");
    paras = HDR(h)->paras;
    type = HDR(h)->type;
    HDR(h)->attr = flags & 0x78;
    flags &= ~0x78;
    switch (type) {
    case 0:
        s_2F36 -= paras;
        break;
    case 1:
        s_2F3A -= paras;
        break;
    case 5:
        Punt("Cannot set type on discarded block");
    case 3:
        s_2F38 -= paras;
        break;
    }
    switch (flags) {
    case 0:
        s_2F36 += paras;
        break;
    case 1:
        s_2F3A += paras;
        break;
    case 3:
        s_2F38 += paras;
        break;
    case 2:
        break;
    default:
        Punt("RallocSetType to illegal type");
        break;
    }
    HDR(h)->type = flags;
}

int far RallocType(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->type;
}

long far RallocSize(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->size;
}

long far RallocMemoryFree(void)
{
    INIT();
    return (unsigned long)s_2F3E << 4;
}

long far RallocMemorySoft(void)
{
    INIT();
    return (unsigned long)s_2F38 << 4;
}

int far RallocFreed(Handle h)
{
    INIT();
    CHECKH(h);
    if (HDR(h)->type == 5)
        return 1;
    return 0;
}

void far mem_discard_handle(Handle h)
{
    Block far *b;

    INIT();
    CHECKH(h);
    if (h && HDR(h)->type != 5) {
        b = HDR(h);
        *h = (char far *)((long)mem_discard_entry_template + 0x20000L);
        mem_free_and_coalesce(b, 1);
    }
}

Handle far RallocRealloc(Handle h, long size, int flags)
{
    unsigned paras;
    int type;
    int lock;
    unsigned oldParas;
    Block far *nb;

    INIT();
    if (SEG(h) == 0xF0F)
        Punt("RL6: Handle must be locked before this operation");
    if (size == 0)
        Punt("REALLOC 0 BYTES");
    if (HDR(h)->lock)
        Punt("Realloc on locked block");
    paras = ((int)size + 15) / 16 + 2;
    if (HDR(h)->paras != paras) {
        if (mem_resize_in_place(h, paras, flags)) {
            HDR(h)->size = size;
            return h;
        }
        lock = HDR(h)->lock;
        type = HDR(h)->type;
        oldParas = HDR(h)->paras - 2;
        HDR(h)->type = 0;
        mem_carve_free_block(nb = mem_find_free_block(paras, flags, HDR(h)->name, 0), paras, flags);
        nb->handle = OFF(h);
        nb->size = size;
        nb->lock = lock;
        HDR(h)->type = type;
        if (type != 5) {
            mem_copy_paragraphs((char far *)((long)nb + 0x20000L), *h, paras - 2 < oldParas ? paras - 2 : oldParas);
            mem_free_and_coalesce(HDR(h), 1);
        }
        *h = (char far *)((long)nb + 0x20000L);
    }
    HDR(h)->age = s_2F30++;
    return h;
}

Handle far mem_Alloc(long size, int flags, char far *name)
{
    Handle h;

    h = mem_alloc_handle_block(size, flags, name);
    return (Handle)((long)(s_2F46 - h) + 0xF0EFFFFL);
}

int far mem_LockLevel(Handle h)
{
    CHECKH(h);
    return HDR(h)->lock;
}

Handle far mem_Realloc(Handle h, long size, int flags)
{
    CHECKH(h);
    return RallocRealloc(h, size, flags);
}

char far * far mem_Lock(Handle h)
{
    Handle p;

    p = mem_lock_handle(h);
    if (!p)
        return 0L;
    return *p;
}

Handle far mem_Unlock(Handle h)
{
    CHECKH(h);
    return mem_unlock_encoded_handle(h);
}

void far mem_Free(Handle h)
{
    RallocFree(h);
}

long far mem_Size(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->size;
}

void far mem_mark_discardable_1c82(Handle h)
{
    CHECKH(h);
    RallocSetType(h, 3);
}

char far * far mem_pointer_if_locked(Handle h)
{
    CHECKH(h);
    if (HDR(h)->lock)
        return *h;
    return 0L;
}

char far * far mem_move_high_and_lock(Handle h)
{
    char far *p;
    int type;
    unsigned paras;
    Block far *nb;
    Block far *b;

    CHECKH(h);
    p = *h;
    type = BLK(SEG(p) - 2)->type;
    paras = BLK(SEG(p) - 2)->paras;
    if (type == 5) {
        WinPrintf("{DIS}");
        return 0L;
    }
    if (HDR(h)->lock)
        Punt("Attempt to move block high which is locked");
    if ((unsigned)(s_8C70 - SEG(p)) - paras < 0x1800)
        return mem_Lock(h);
    BLK(SEG(p) - 2)->type = 1;
    nb = mem_allocate_high_block(paras, type);
    b = HDR(h);
    mem_copy_paragraphs(nb, b, paras);
    nb->type = type;
    nb->paras = paras;
    *h = (char far *)((long)nb + 0x20000L);
    mem_free_and_coalesce(b, 1);
    return mem_Lock(h);
}

void far mem_set_alloc_type(Handle h, int flags)
{
    RallocSetType(h, flags);
}

int far mem_handle_above_ems_boundary(Handle h)
{
    CHECKH(h);
    if (SEG(*h) > mem_ems_boundary_segment)
        return 1;
    return 0;
}

void far mem_discard_soft_blocks(void)
{
    Handle h;
    int n;

    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h) {
            if (HDR(h)->type == 3)
                mem_discard_handle(h);
            n--;
        }
    }
}

Handle far f_171C_1F52(char far *name)
{
    Handle h;
    int n;

    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h && !_fstrncmp((char far *)(long)*name, HDR(h)->name, 13))
            return h;
    }
    return 0L;
}

Handle far mem_lock_handle(Handle h)
{
    CHECKH(h);
    if (HDR(h)->lock > 100)
        Punt("Lock depth exceeded 100");
    if (HDR(h)->type == 5)
        Punt("Locked discarded!!");
    HDR(h)->age = s_2F30++;
    HDR(h)->lock++;
    return h;
}

Handle far mem_unlock_encoded_handle(Handle h)
{
    if (h > s_2F46 - 1 || h < s_2F46 - g_2F42)
        Punt("RU: Bad handle in unlock");
    HDR(h)->lock--;
    return (Handle)((long)(s_2F46 - h) + 0xF0EFFFFL);
}

void far mem_mark_discardable_20e2(Handle h)
{
    CHECKH(h);
    RallocSetType(h, 3);
}

Handle far mem_handle_from_pointer(char far *p)
{
    char far *q;
    Handle h;

    q = p;
    h = (Handle)((char far *)s_2F46 + BLK(SEG(q) - 2)->handle);
    if (*h != q)
        Punt("FindMemoryHandle: memPtr block has bad handle");
    return h;
}

char far * far mem_malloc(unsigned size, char far *name)
{
    char far *p;

    INIT();
    s_2F2A++;
    p = *Ralloc((long)size, 0, name);
    s_2F2A--;
    return p;
}

char far * far mem_malloc_bridge(unsigned size)
{
    char far *p;

    INIT();
    s_2F2A++;
    p = *Ralloc((long)size, 0, "malloc");
    s_2F2A--;
    return p;
}

void far * far malloc(unsigned size)
{
    return mem_malloc_bridge(size);
}

void far _ffree(char far *p)
{
    Handle h;

    INIT();
    s_2F2A++;
    h = mem_handle_from_pointer(p);
    if (!h)
        Punt("_ffree: Could not find memory ptr");
    HDR(h)->lock = 0;
    RallocFree(h);
    s_2F2A--;
}

void far free(void far *p)
{
    _ffree(p);
}

char far * far _frealloc(char far *p, unsigned size)
{
    Handle h;

    INIT();
    s_2F2A++;
    if (!p)
        return mem_malloc_bridge(size);
    h = mem_handle_from_pointer(p);
    if (!h)
        Punt("_frealloc: Could not find memory ptr");
    h = RallocRealloc(h, (long)size, 0);
    s_2F2A--;
    return *h;
}

void far * far mem_realloc_pointer_bridge(void far *p, unsigned size)
{
    return _frealloc(p, size);
}

/* WIDTH-1: the paragraph-address sum uses a word segment and an unsigned-long
 * paragraph count. Both contributions are unsigned words; the shifted BLK address
 * has the same value as NEXTBLK. The mixed-width expression reproduces DX. */
