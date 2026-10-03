#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
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

#define SEG(p) ((uint32_t)(p) >> 16)
#define OFF(p) ((uint16_t)(p))

typedef struct {
    int16_t handle;                 /* +00 offset of the master pointer */
    int32_t size;                  /* +02 requested size in bytes */
    uint16_t paras;             /* +06 size in paragraphs incl. header */
    uint8_t type;         /* +08 */
    uint8_t lock;         /* +09 */
    int32_t age;                   /* +0A */
    uint16_t next;              /* +0E free list: next block segment */
    uint16_t prev;              /* +10 free list: previous block segment */
    uint8_t attr;         /* +12 */
    char name[13];              /* +13 */
} Block;

typedef char  *  *Handle;

#define BLK(s) ((Block  *)((uint32_t)(s) << 16))
#define HDR(h) BLK(SEG(*(h)) - 2)
#define NEXTBLK(p) BLK((p)->paras + SEG(p))

#define CHECKH(h) \
    if (SEG(h) == 0xF0F) { \
        int16_t i = OFF(h); \
        if (i >= 0 && i < g_2F42) \
            h = s_2F46 - i - 1; \
        else \
            Punt("RL5: Invalid handle index"); \
    }

#define INIT() if (!s_2F34) f_171C_07BE()

extern int8_t  fd_55B3_360C;
extern int16_t  fd_55B3_3612;
extern char  *  fd_55B3_360E;
extern uint16_t  fd_50F6_394C;
extern uint16_t  fd_50F6_394E;
extern uint16_t  fd_50F6_3950;
extern char  *  fd_50F6_3948;
extern uint16_t  g_91A0;
extern uint16_t  g_91A2;
extern Block  *  g_91A4;
extern Block  *  g_91A8;
extern Block  *  g_91AC;

extern void  Punt(char  *format, ...);
extern void  WinPrintf(char  *format, ...);
extern void  f_195A_001D(void);
extern void  f_195A_0035(void);
extern int16_t  f_195A_004B(int16_t pages);
extern void  f_195A_0062(int16_t handle, int16_t logical, int16_t physical);
extern void  f_195A_007D(int16_t handle);
extern void  f_195A_01CB(int16_t handle, char  *name);
extern int16_t  f_195A_0260(void);
extern void  f_194D_0006(void  *dst, void  *src, uint16_t paras);

extern int16_t g_2F44;
extern int16_t g_2F42;

static char b_8C62[14];
static uint16_t s_8C70;
static uint16_t s_8C72;

static int16_t s_2F2A = 0;
static int16_t s_2F2C = 0;
static int16_t s_2F2E = 0;
static int32_t s_2F30 = 0L;
static int16_t s_2F34 = 0;
static uint16_t s_2F36 = 0;
static uint16_t s_2F38 = 0;
static uint16_t s_2F3A = 0;
static uint16_t s_2F3C = 0;
static uint16_t s_2F3E = 0;
static uint16_t s_2F40 = 0;
int16_t g_2F42 = 0;
int16_t g_2F44 = 0;
static Handle s_2F46 = 0L;
static int16_t s_2F4A = 300;
static int16_t s_2F4C = 0;
static Block s_2F4E = { 0, 0L, 0, 5 };
static int16_t s_2F6E = 0;

void  f_171C_07BE(void);
Block  *  f_171C_0160(Block  *b, int16_t merge);
void  f_171C_068C(Block  *b, uint16_t paras, int16_t type);
Block  *  f_171C_0EEA(uint16_t paras, int16_t type, char  *name, int16_t noems);
Block  *  f_171C_0FBC(uint16_t paras, int16_t type);
void  f_171C_11F2(Block  *b);
void  f_171C_1246(Handle h);
Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);
void  f_171C_13E4(Handle h);
void  f_171C_15A2(Handle h, int16_t flags);
void  f_171C_1804(Handle h);
Handle  f_171C_18A6(Handle h, int32_t size, int16_t flags);
Handle  f_171C_1FC2(Handle h);
Handle  f_171C_2086(Handle h);
Handle  f_171C_2136(char  *p);
char  *  f_171C_21CC(uint16_t size);

void  f_171C_0002(char  *where)
{
    Punt("MemPunt @%s after %s", where, (char  *)b_8C62);
}

void  f_171C_001E(void)
{
}

void  f_171C_0020(void)
{
    if (s_2F6E)
        f_195A_007D(s_2F6E);
}

int16_t  f_171C_0034(void)
{
    if (s_2F6E)
        return 1;
    if (f_195A_0260()) {
        if (fd_55B3_360C >= 0x40) {
            f_195A_0035();
            if (fd_55B3_3612 >= 3) {
                f_195A_001D();
                fd_50F6_394C = FP_SEG(fd_55B3_360E) + 1;
                s_2F6E = f_195A_004B(3);
                fd_50F6_394E = 0xBF8;
                f_195A_01CB(s_2F6E, "RALLOCXX");
                f_195A_0062(s_2F6E, 0, 0);
                f_195A_0062(s_2F6E, 1, 1);
                f_195A_0062(s_2F6E, 2, 2);
                atexit(f_171C_0020);
                return 1;
            }
        }
    }
    return 0;
}

char  *  f_171C_00FA(int16_t type)
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

Block  *  f_171C_0160(Block  *b, int16_t merge)
{
    uint16_t paras;
    Block  *next;
    Block  *prev;

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
    if (g_91AC == 0L) {
        g_91AC = b;
        b->next = b->prev = 0;
    } else {
        f_171C_11F2(b);
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
        if (BLK((uint16_t)SEG(b) + (uint32_t)b->paras) == next) {
            b->next = next->next;
            b->paras += next->paras;
            next = BLK(next->next);
            if (next)
                next->prev = SEG(b);
        }
        if (b->prev == 0)
            g_91AC = b;
    }
    return b;
}

void  f_171C_02CA(int16_t fd, char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    char buffer[300];

    dos_vsprintf(buffer, format, _dos_va_args);
    dos_write(fd, buffer, _fstrlen(buffer));

    va_end(_dos_va_args);
}

void  f_171C_030C(char  *where)
{
    int16_t x;
    int16_t y;
    int16_t n;
    int16_t fd;
    Handle h;
    Block  *b;
    int32_t now;
    char name[30];

    if (s_2F2A)
        return;
    fd = dos_open("ralloc.dmp", 0x109, 0x180);
    time(&now);
    f_171C_02CA(fd, "\n\nRalloc dump at %s, %s", where, asctime(localtime(&now)));
    f_171C_02CA(fd, "\nFree Space:  %ld,  Used Space:  %ld, Total Space: %ld \n",
                (uint32_t)s_2F3E << 4, (uint32_t)s_2F3C << 4, (uint32_t)s_2F40 << 4);
    f_171C_02CA(fd, "Hard space:  %ld,  Firm space:  %ld, Soft Space : %ld\n",
                (uint32_t)s_2F36 << 4, (uint32_t)s_2F3A << 4, (uint32_t)s_2F38 << 4);
    f_171C_02CA(fd, "Handles allocated: %d,  handles used: %d max: %d", g_2F42, g_2F44, s_2F4C);
    h = s_2F46 - 1;
    n = g_2F44;
    f_171C_02CA(fd, "\nBy handles: \n");
    while (n) {
        if (*h) {
            _fstrncpy(name, HDR(h)->name, 29);
            name[29] = 0;
            b = HDR(h);
            f_171C_02CA(fd, "%p->%p: size=%ld, type=%c%s age=%5ld name=%s\n",
                        h, *h, (uint32_t)b->paras << 4, b->lock ? '*' : ' ',
                        f_171C_00FA(b->type), s_2F30 - b->age, (char  *)name);
            n--;
        }
        h--;
    }
    f_171C_02CA(fd, "\n\nBy location:\n");
    for (b = g_91A4; SEG(b) < SEG(g_91A8); b = BLK(SEG(b) + b->paras)) {
        _fstrncpy(name, b->name, 13);
        name[13] = 0;
        h = (Handle)((char  *)s_2F46 + b->handle);
        switch (b->type) {
        case 2:
        case 5:
        case 0x80:
            f_171C_02CA(fd, "----:----->%p:", (char  *)((int32_t)b + 0x20000L));
            break;
        default:
            f_171C_02CA(fd, "%p->%p:", h, *h);
            break;
        }
        f_171C_02CA(fd, "size=%x, %ld, type=%c%s", b->paras, (uint32_t)b->paras << 4,
                    HDR(h)->lock ? '*' : ' ', f_171C_00FA(b->type));
        f_171C_02CA(fd, " age=%5ld name=%s\n", s_2F30 - b->age, (char  *)name);
    }
    dos_close(fd);
}

void  f_171C_0674(void)
{
}

void  f_171C_0676(void)
{
}

void  f_171C_0678(void)
{
    _dos_freemem(g_91A2);
    s_2F34 = 0;
}

void  f_171C_068C(Block  *b, uint16_t paras, int16_t type)
{
    uint16_t seg;
    Block  *next;
    Block  *prev;
    Block  *nb;

    next = BLK(b->next);
    prev = BLK(b->prev);
    if (b->paras - 2 > paras) {
        seg = SEG(b) + paras;
        if (prev)
            prev->next = seg;
        else
            g_91AC = BLK(seg);
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
            g_91AC = next;
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

void  f_171C_07BE(void)
{
    Block  *b;

    if (s_2F34)
        return;
    s_2F34 = 1;
    if (_dos_allocmem(0xFF00, &g_91A0)) {
        g_91A0 -= 0x10;
        _dos_allocmem(g_91A0, &g_91A2);
        g_91A0 -= 0x10;
    } else
        exit(1);
    s_8C72 = (s_2F4A * 4 + 15) / 16;
    s_2F46 = (Handle)(((uint32_t)s_8C72 + g_91A2 - 0x1000) << 16);
    g_91A0 -= s_8C72 + 1;
    g_91A2 += s_8C72 + 1;
    g_91AC = g_91A4 = BLK(g_91A2);
    g_91AC->type = 0x80;
    g_91AC->next = 0;
    g_91AC->prev = 0;
    if (f_171C_0034()) {
        g_91AC->paras = s_2F40 = s_2F3E = fd_50F6_394E + fd_50F6_394C - g_91A2;
        g_91A8 = BLK(s_2F3E + SEG(BLK(g_91A2)));
        s_8C70 = SEG(g_91A8);
        fd_50F6_3950 = SEG(BLK(g_91A2)) + g_91A0 - 2;
        f_171C_068C(BLK(g_91A2), g_91A0 - 2, 0);
        f_171C_068C(BLK(g_91A2 + g_91A0 - 2), fd_50F6_394C - g_91A2 - g_91A0 + 2, 2);
        f_171C_0160(BLK(g_91A2), 0);
    } else {
        g_91AC->paras = s_2F40 = s_2F3E = g_91A0;
        g_91A8 = BLK(s_2F3E + g_91A2);
        fd_50F6_3950 = s_8C70 = SEG(g_91A8);
    }
    _fmemset(s_2F46 - s_2F4A, 0, s_2F4A * 4);
    fd_50F6_3948 = *f_171C_13CA(0x20L, 0, "DiscardEntry");
    _fmemcpy(fd_50F6_3948, &s_2F4E, 0x20);
    atexit(f_171C_0678);
}

/* SCAFFOLD BEGIN: draft; residue: register allocation (original keeps paras in DI, next block pointer in memory with two copies [bp-0Ah]/[bp-2]) */
int16_t  f_171C_09CC(Handle h, uint16_t paras, int16_t type)
{
    Block  *b;
    Block  *next;

    b = HDR(h);
    if (b->paras > paras) {
        if (b->paras < paras + 0x20)
            return 1;
    } else {
        next = BLK(SEG(b) + b->paras);
        if (SEG(next) >= SEG(g_91A8) || next->type != 0x80 || next->paras + b->paras < paras)
            return 0;
    }
    f_171C_068C(f_171C_0160(b, 0), paras, type);
    return 1;
}
/* SCAFFOLD END */

Handle  f_171C_0A5C(void)
{
    Handle h;
    int16_t i;

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
void  f_171C_0ADC(Block  *b)
{
    Block  *n;
    Block save;
    uint32_t seg;

    save = *b;
    seg = SEG(b);
    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);
    *(Handle)((char  *)s_2F46 + b->handle) = (char  *)((uint32_t)b + 0x20000L);
    b = BLK(b->paras + seg);
    *b = save;
    if (b->prev)
        BLK(b->prev)->next = SEG(b);
    else
        g_91AC = b;
    if (b->next) {
        n = BLK(b->next);
        if (b->next - b->paras == (uint16_t)SEG(b)) {
            b->next = n->next;
            b->paras += n->paras;
            n = BLK(b->next);
        }
        if (n)
            n->prev = SEG(b);
    }
}
/* SCAFFOLD END */

int16_t  f_171C_0BE2(int16_t emsOnly)
{
    Block  *b;
    uint32_t oldest;
    Handle h;
    int16_t n;
    Handle found;

    oldest = 0;
    found = 0L;
    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h) {
            b = HDR(h);
            if ((!emsOnly || (uint16_t)SEG(b) < fd_50F6_3950) && b->type == 3 && s_2F30 - b->age >= oldest && !b->lock) {
                oldest = s_2F30 - b->age;
                found = h;
            }
            n--;
        }
    }
    if (found) {
        WinPrintf("OLDESTH=%p", found);
        b = HDR(found);
        *found = (char  *)((int32_t)fd_50F6_3948 + 0x20000L);
        f_171C_0160(b, 1);
        return 1;
    }
    return 0;
}

/* SCAFFOLD BEGIN: draft; needs runtime __disable/__enable (29F4:2D76/2D78) registered; a 490-byte near-exact draft is in work/mem (unsigned seg loop, comma-hoisted type test) but it shifts the object layout and breaks 125C relocation order */
int16_t  f_171C_0CF4(int16_t emsOnly)
{
    int16_t t;
    uint16_t seg;
    int32_t size;
    uint16_t paras;
    Block  *n;
    uint16_t end;
    Block  *b;
    uint32_t moved;
    Block  *nb;

    moved = 0;
    b = g_91A4;
    end = emsOnly ? fd_50F6_3950 : s_8C70;
    for (; (seg = (uint16_t)SEG(b)) < end; b = BLK(b->paras + seg)) {
        if (b->type != 0x80)
            continue;
        n = BLK(b->paras + seg);
        if ((uint16_t)SEG(n) < end && (t = n->type, !n->lock) && (t == 1 || t == 3) && !(n->attr & 0x10)) {
            f_171C_0ADC(b);
            continue;
        }
        while ((uint16_t)SEG(n) < end) {
            if ((t = n->type, !n->lock) && (t == 1 || t == 3) && b->paras >= n->paras)
                goto found;
            n = BLK((uint16_t)SEG(n) + (uint32_t)n->paras);
        }
        continue;
found:
        paras = n->paras;
        size = n->size;
        f_171C_068C(b, paras, t);
        _fmemcpy(b->name, n->name, 13);
        nb = b;
        nb->size = size;
        f_194D_0006((char  *)((int32_t)nb + 0x20000L), (char  *)((int32_t)n + 0x20000L), paras - 2);
        nb->handle = n->handle;
        nb->age = n->age;
        nb->attr = n->attr;
        _disable();
        *(Handle)((char  *)s_2F46 + nb->handle) = (char  *)((int32_t)nb + 0x20000L);
        _enable();
        f_171C_0160(n, 1);
        moved = 1;
    }
    return (int16_t)moved;
}
/* SCAFFOLD END */

int16_t  f_171C_0EDE(void)
{
    return f_171C_0CF4(0);
}

Block  *  f_171C_0EEA(uint16_t paras, int16_t type, char  *name, int16_t noems)
{
    Block  *b;
    char buffer[100];

    for (;;) {
        for (b = g_91AC; b; b = BLK(b->next)) {
            if (noems && SEG(b) >= fd_50F6_3950)
                break;
            if (b->paras >= paras)
                return b;
        }
        if (s_2F3E > paras && f_171C_0CF4(noems))
            continue;
        if (!f_171C_0BE2(noems) || s_2F3E + s_2F38 <= paras)
            break;
        while (f_171C_0BE2(noems) && s_2F3E < paras)
            ;
    }
    dos_sprintf(buffer, "Cannot find a big enough space! (%ld bytes) @ %s", (uint32_t)paras << 4, name);
    Punt(buffer);
}

/* SCAFFOLD BEGIN: draft; residue: register allocation (original: SI for inner-loop block/size/result, DI for best/paras by region) and frame layout */
Block  *  f_171C_0FBC(uint16_t paras, int16_t type)
{
    int16_t first;
    Block  *b;
    Block  *best;
    int16_t compacted;
    Block  *n;
    char buffer[100];

    first = 1;
    compacted = 0;
    for (;;) {
        best = g_91AC;
        for (b = g_91AC; b; b = BLK(b->next))
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
                f_171C_068C(best, best->paras - paras, 0);
                n = BLK(SEG(best) + best->paras);
                f_171C_068C(n, paras, type);
                f_171C_0160(best, 1);
                return n;
            }
            WinPrintf("<WHOLE>");
            f_171C_068C(best, paras, type);
            return best;
        }
        if (!first) {
            dos_sprintf(buffer, "Cannot find a big enough space! (%ld bytes)", (uint32_t)paras << 4);
            Punt(buffer);
        }
again:
        if (!compacted) {
            WinPrintf("<CL>");
            if (s_2F3E > paras && f_171C_0CF4(0)) {
                first = compacted = 1;
                continue;
            }
        }
        WinPrintf("<FO>");
        compacted = 0;
        if (f_171C_0BE2(0) && s_2F3E + s_2F38 > paras) {
            WinPrintf("<FO2>");
            while (f_171C_0BE2(0) && s_2F3E < paras)
                ;
            first = 1;
        } else
            first = 0;
    }
}
/* SCAFFOLD END */

void  f_171C_11F2(Block  *b)
{
    Block  *cur;
    Block  *prev;

    cur = g_91AC;
    prev = 0L;
    while ((uint16_t)SEG(b) > SEG(cur)) {
        if (!cur)
            break;
        prev = cur;
        cur = BLK(cur->next);
    }
    b->prev = SEG(prev);
    b->next = SEG(cur);
}

void  f_171C_1246(Handle h)
{
    g_2F44--;
    *h = 0L;
}

Handle  f_171C_125C(int32_t size, int16_t flags, char  *name, int16_t unused)
{
    int16_t noems;
    uint16_t paras;
    Handle h;
    Block  *b;

    noems = flags & 8;
    flags &= ~8;
    if (size == 0)
        Punt("ALLOC 0 BYTES");
    INIT();
    _fstrncpy(b_8C62, name, 13);
    b_8C62[13] = 0;
    paras = ((uint16_t)size + 15) >> 4;
    b = f_171C_0EEA(paras + 2, flags & ~0x78, name, noems);
    if (noems)
        WinPrintf("\nNOEMS - memPtr=%p", b);
    h = f_171C_0A5C();
    if (!h)
        Punt("Could not allocate handle");
    *h = (char  *)((int32_t)b + 0x20000L);
    f_171C_068C(b, paras + 2, flags & ~0x78);
    b->handle = OFF(h);
    b->lock = 0;
    _fstrncpy(b->name, name, 12);
    b->name[12] = 0;
    HDR(h)->size = size;
    HDR(h)->age = s_2F30++;
    HDR(h)->attr = flags & 0x78;
    return h;
}

Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name)
{
    return f_171C_125C(size, flags, name);
}

void  f_171C_13E4(Handle h)
{
    Block  *b;
    char name[13];

    INIT();
    CHECKH(h);
    b = HDR(h);
    if (b->type != 5)
        f_171C_0160(b, 1);
    if (HDR(h)->lock) {
        _fmemcpy(name, b->name, 13);
        name[12] = 0;
        Punt("LOCKED FREED %s", (char  *)name);
    }
    HDR(h)->lock = 0;
    f_171C_1246(h);
}

int32_t  f_171C_14BE(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->age - s_2F30;
}

void  f_171C_152C(Handle h)
{
    INIT();
    CHECKH(h);
    HDR(h)->age = s_2F30++;
}

void  f_171C_15A2(Handle h, int16_t flags)
{
    int32_t paras;
    volatile int16_t type;

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

int16_t  f_171C_1686(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->type;
}

int32_t  f_171C_16EA(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->size;
}

int32_t  f_171C_1750(void)
{
    INIT();
    return (uint32_t)s_2F3E << 4;
}

int32_t  f_171C_1772(void)
{
    INIT();
    return (uint32_t)s_2F38 << 4;
}

int16_t  f_171C_1794(Handle h)
{
    INIT();
    CHECKH(h);
    if (HDR(h)->type == 5)
        return 1;
    return 0;
}

void  f_171C_1804(Handle h)
{
    Block  *b;

    INIT();
    CHECKH(h);
    if (h && HDR(h)->type != 5) {
        b = HDR(h);
        *h = (char  *)((int32_t)fd_50F6_3948 + 0x20000L);
        f_171C_0160(b, 1);
    }
}

Handle  f_171C_18A6(Handle h, int32_t size, int16_t flags)
{
    uint16_t paras;
    int16_t type;
    int16_t lock;
    uint16_t oldParas;
    Block  *nb;

    INIT();
    if (SEG(h) == 0xF0F)
        Punt("RL6: Handle must be locked before this operation");
    if (size == 0)
        Punt("REALLOC 0 BYTES");
    if (HDR(h)->lock)
        Punt("Realloc on locked block");
    paras = ((int16_t)size + 15) / 16 + 2;
    if (HDR(h)->paras != paras) {
        if (f_171C_09CC(h, paras, flags)) {
            HDR(h)->size = size;
            return h;
        }
        lock = HDR(h)->lock;
        type = HDR(h)->type;
        oldParas = HDR(h)->paras - 2;
        HDR(h)->type = 0;
        f_171C_068C(nb = f_171C_0EEA(paras, flags, HDR(h)->name, 0), paras, flags);
        nb->handle = OFF(h);
        nb->size = size;
        nb->lock = lock;
        HDR(h)->type = type;
        if (type != 5) {
            f_194D_0006((char  *)((int32_t)nb + 0x20000L), *h, paras - 2 < oldParas ? paras - 2 : oldParas);
            f_171C_0160(HDR(h), 1);
        }
        *h = (char  *)((int32_t)nb + 0x20000L);
    }
    HDR(h)->age = s_2F30++;
    return h;
}

Handle  f_171C_1A9E(int32_t size, int16_t flags, char  *name)
{
    Handle h;

    h = f_171C_125C(size, flags, name);
    return (Handle)((int32_t)(s_2F46 - h) + 0xF0EFFFFL);
}

int16_t  f_171C_1AD4(Handle h)
{
    CHECKH(h);
    return HDR(h)->lock;
}

Handle  f_171C_1B2C(Handle h, int32_t size, int16_t flags)
{
    CHECKH(h);
    return f_171C_18A6(h, size, flags);
}

char  *  f_171C_1B84(Handle h)
{
    Handle p;

    p = f_171C_1FC2(h);
    if (!p)
        return 0L;
    return *p;
}

Handle  f_171C_1BBA(Handle h)
{
    CHECKH(h);
    return f_171C_2086(h);
}

void  f_171C_1C0A(Handle h)
{
    f_171C_13E4(h);
}

int32_t  f_171C_1C1C(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->size;
}

void  f_171C_1C82(Handle h)
{
    CHECKH(h);
    f_171C_15A2(h, 3);
}

char  *  f_171C_1CD6(Handle h)
{
    CHECKH(h);
    if (HDR(h)->lock)
        return *h;
    return 0L;
}

char  *  f_171C_1D40(Handle h)
{
    char  *p;
    int16_t type;
    uint16_t paras;
    Block  *nb;
    Block  *b;

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
    if ((uint16_t)(s_8C70 - SEG(p)) - paras < 0x1800)
        return f_171C_1B84(h);
    BLK(SEG(p) - 2)->type = 1;
    nb = f_171C_0FBC(paras, type);
    b = HDR(h);
    f_194D_0006(nb, b, paras);
    nb->type = type;
    nb->paras = paras;
    *h = (char  *)((int32_t)nb + 0x20000L);
    f_171C_0160(b, 1);
    return f_171C_1B84(h);
}

void  f_171C_1E86(Handle h, int16_t flags)
{
    f_171C_15A2(h, flags);
}

int16_t  f_171C_1E9A(Handle h)
{
    CHECKH(h);
    if (SEG(*h) > fd_50F6_3950)
        return 1;
    return 0;
}

void  f_171C_1EFA(void)
{
    Handle h;
    int16_t n;

    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h) {
            if (HDR(h)->type == 3)
                f_171C_1804(h);
            n--;
        }
    }
}

Handle  f_171C_1F52(char  *name)
{
    Handle h;
    int16_t n;

    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h && !_fstrncmp((char  *)(int32_t)*name, HDR(h)->name, 13))
            return h;
    }
    return 0L;
}

Handle  f_171C_1FC2(Handle h)
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

Handle  f_171C_2086(Handle h)
{
    if (h > s_2F46 - 1 || h < s_2F46 - g_2F42)
        Punt("RU: Bad handle in unlock");
    HDR(h)->lock--;
    return (Handle)((int32_t)(s_2F46 - h) + 0xF0EFFFFL);
}

void  f_171C_20E2(Handle h)
{
    CHECKH(h);
    f_171C_15A2(h, 3);
}

Handle  f_171C_2136(char  *p)
{
    char  *q;
    Handle h;

    q = p;
    h = (Handle)((char  *)s_2F46 + BLK(SEG(q) - 2)->handle);
    if (*h != q)
        Punt("FindMemoryHandle: memPtr block has bad handle");
    return h;
}

char  *  f_171C_2190(uint16_t size, char  *name)
{
    char  *p;

    INIT();
    s_2F2A++;
    p = *f_171C_13CA((int32_t)size, 0, name);
    s_2F2A--;
    return p;
}

char  *  f_171C_21CC(uint16_t size)
{
    char  *p;

    INIT();
    s_2F2A++;
    p = *f_171C_13CA((int32_t)size, 0, "malloc");
    s_2F2A--;
    return p;
}

void  *  dos_malloc(uint16_t size)
{
    return f_171C_21CC(size);
}

void  dos_free(char  *p)
{
    Handle h;

    INIT();
    s_2F2A++;
    h = f_171C_2136(p);
    if (!h)
        Punt("_ffree: Could not find memory ptr");
    HDR(h)->lock = 0;
    f_171C_13E4(h);
    s_2F2A--;
}

void  dos_free(void  *p)
{
    dos_free(p);
}

char  *  dos_realloc(char  *p, uint16_t size)
{
    Handle h;

    INIT();
    s_2F2A++;
    if (!p)
        return f_171C_21CC(size);
    h = f_171C_2136(p);
    if (!h)
        Punt("_frealloc: Could not find memory ptr");
    h = f_171C_18A6(h, (int32_t)size, 0);
    s_2F2A--;
    return *h;
}

void  *  f_171C_2302(void  *p, uint16_t size)
{
    return dos_realloc(p, size);
}

/* WIDTH-1: the paragraph-address sum uses a word segment and an unsigned-long
 * paragraph count. Both contributions are unsigned words; the shifted BLK address
 * has the same value as NEXTBLK. The mixed-width expression reproduces DX. */

#pragma pack(pop)
