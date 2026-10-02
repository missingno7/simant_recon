extern int idscan_pad0;
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

#define INIT() if (!s_2F34) f_171C_07BE()

extern signed char far fd_55B3_360C;
extern int far fd_55B3_3612;
extern char far * far fd_55B3_360E;
extern unsigned far fd_50F6_394C;
extern unsigned far fd_50F6_394E;
extern unsigned far fd_50F6_3950;
extern char far * far fd_50F6_3948;
extern unsigned near g_91A0;
extern unsigned near g_91A2;
extern Block far * near g_91A4;
extern Block far * near g_91A8;
extern Block far * near g_91AC;

extern void far Punt(char far *format, ...);
extern void far WinPrintf(char far *format, ...);
extern void far f_195A_001D(void);
extern void far f_195A_0035(void);
extern int far f_195A_004B(int pages);
extern void far f_195A_0062(int handle, int logical, int physical);
extern void far f_195A_007D(int handle);
extern void far f_195A_01CB(int handle, char far *name);
extern int far f_195A_0260(void);
extern void far f_194D_0006(void far *dst, void far *src, unsigned paras);

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

void far f_171C_07BE(void);
Block far * far f_171C_0160(Block far *b, int merge);
void far f_171C_068C(Block far *b, unsigned paras, int type);
Block far * far f_171C_0EEA(unsigned paras, int type, char far *name, int noems);
Block far * far f_171C_0FBC(unsigned paras, int type);
void far f_171C_11F2(Block far *b);
void far f_171C_1246(Handle h);
Handle far f_171C_13CA(long size, int flags, char far *name);
void far f_171C_13E4(Handle h);
void far f_171C_15A2(Handle h, int flags);
void far f_171C_1804(Handle h);
Handle far f_171C_18A6(Handle h, long size, int flags);
Handle far f_171C_1FC2(Handle h);
Handle far f_171C_2086(Handle h);
Handle far f_171C_2136(char far *p);
char far * far f_171C_21CC(unsigned size);

void far f_171C_0002(char far *where)
{
    Punt("MemPunt @%s after %s", where, (char far *)b_8C62);
}

void far f_171C_001E(void)
{
}

void far f_171C_0020(void)
{
    if (s_2F6E)
        f_195A_007D(s_2F6E);
}

int far f_171C_0034(void)
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

char far * far f_171C_00FA(int type)
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

Block far * far f_171C_0160(Block far *b, int merge)
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
        if (BLK((unsigned)SEG(b) + (unsigned long)b->paras) == next) {
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

void far f_171C_02CA(int fd, char far *format, ...)
{
    char buffer[300];

    vsprintf(buffer, format, (char far *)(&format + 1));
    write(fd, buffer, _fstrlen(buffer));
}

void far f_171C_030C(char far *where)
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
    f_171C_02CA(fd, "\n\nRalloc dump at %s, %s", where, asctime(localtime(&now)));
    f_171C_02CA(fd, "\nFree Space:  %ld,  Used Space:  %ld, Total Space: %ld \n",
                (unsigned long)s_2F3E << 4, (unsigned long)s_2F3C << 4, (unsigned long)s_2F40 << 4);
    f_171C_02CA(fd, "Hard space:  %ld,  Firm space:  %ld, Soft Space : %ld\n",
                (unsigned long)s_2F36 << 4, (unsigned long)s_2F3A << 4, (unsigned long)s_2F38 << 4);
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
                        h, *h, (unsigned long)b->paras << 4, b->lock ? '*' : ' ',
                        f_171C_00FA(b->type), s_2F30 - b->age, (char far *)name);
            n--;
        }
        h--;
    }
    f_171C_02CA(fd, "\n\nBy location:\n");
    for (b = g_91A4; SEG(b) < SEG(g_91A8); b = BLK(SEG(b) + b->paras)) {
        _fstrncpy(name, b->name, 13);
        name[13] = 0;
        h = (Handle)((char far *)s_2F46 + b->handle);
        switch (b->type) {
        case 2:
        case 5:
        case 0x80:
            f_171C_02CA(fd, "----:----->%p:", (char far *)((long)b + 0x20000L));
            break;
        default:
            f_171C_02CA(fd, "%p->%p:", h, *h);
            break;
        }
        f_171C_02CA(fd, "size=%x, %ld, type=%c%s", b->paras, (unsigned long)b->paras << 4,
                    HDR(h)->lock ? '*' : ' ', f_171C_00FA(b->type));
        f_171C_02CA(fd, " age=%5ld name=%s\n", s_2F30 - b->age, (char far *)name);
    }
    close(fd);
}

void far f_171C_0674(void)
{
}

void far f_171C_0676(void)
{
}

void far f_171C_0678(void)
{
    _dos_freemem(g_91A2);
    s_2F34 = 0;
}

void far f_171C_068C(Block far *b, unsigned paras, int type)
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

void far f_171C_07BE(void)
{
    Block far *b;

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
    s_2F46 = (Handle)(((unsigned long)s_8C72 + g_91A2 - 0x1000) << 16);
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
int far f_171C_09CC(Handle h, unsigned paras, int type)
{
    Block far *b;
    Block far *next;

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

Handle far f_171C_0A5C(void)
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
void far f_171C_0ADC(Block far *b)
{
    Block far *n;
    Block save;
    unsigned long seg;

    save = *b;
    seg = SEG(b);
    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);
    *(Handle)((char far *)s_2F46 + b->handle) = (char far *)((unsigned long)b + 0x20000L);
    b = BLK(b->paras + seg);
    *b = save;
    if (b->prev)
        BLK(b->prev)->next = SEG(b);
    else
        g_91AC = b;
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

int far f_171C_0BE2(int emsOnly)
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
            if ((!emsOnly || (unsigned)SEG(b) < fd_50F6_3950) && b->type == 3 && s_2F30 - b->age >= oldest && !b->lock) {
                oldest = s_2F30 - b->age;
                found = h;
            }
            n--;
        }
    }
    if (found) {
        WinPrintf("OLDESTH=%p", found);
        b = HDR(found);
        *found = (char far *)((long)fd_50F6_3948 + 0x20000L);
        f_171C_0160(b, 1);
        return 1;
    }
    return 0;
}

int far f_171C_0CF4(int emsOnly)
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
    b = g_91A4;
    end = emsOnly ? fd_50F6_3950 : s_8C70;
    for (; (seg = (unsigned)SEG(b)) < end; b = BLK(b->paras + seg)) {
        if (b->type != 0x80)
            continue;
        n = BLK(b->paras + seg);
        if ((unsigned)SEG(n) < end && (t = n->type, !n->lock) && (t == 1 || t == 3) && !(n->attr & 0x10)) {
            f_171C_0ADC(b);
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
        f_171C_068C(b, paras, t);
        _fmemcpy(b->name, n->name, 13);
        nb = b;
        nb->size = size;
        f_194D_0006((char far *)((long)nb + 0x20000L), (char far *)((long)n + 0x20000L), paras - 2);
        nb->handle = n->handle;
        nb->age = n->age;
        nb->attr = n->attr;
        _disable();
        *(Handle)((char far *)s_2F46 + nb->handle) = (char far *)((long)nb + 0x20000L);
        _enable();
        f_171C_0160(n, 1);
        moved = 1;
    }
    return *(int near *)&moved;
}

int far f_171C_0EDE(void)
{
    return f_171C_0CF4(0);
}

Block far * far f_171C_0EEA(unsigned paras, int type, char far *name, int noems)
{
    Block far *b;
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
    sprintf(buffer, "Cannot find a big enough space! (%ld bytes) @ %s", (unsigned long)paras << 4, name);
    Punt(buffer);
}

/* SCAFFOLD BEGIN: draft; residue: register allocation (original: SI for inner-loop block/size/result, DI for best/paras by region) and frame layout */
Block far * far f_171C_0FBC(unsigned paras, int type)
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
            sprintf(buffer, "Cannot find a big enough space! (%ld bytes)", (unsigned long)paras << 4);
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

void far f_171C_11F2(Block far *b)
{
    Block far *cur;
    Block far *prev;

    cur = g_91AC;
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

void far f_171C_1246(Handle h)
{
    g_2F44--;
    *h = 0L;
}

Handle far f_171C_125C(long size, int flags, char far *name, int unused)
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
    b = f_171C_0EEA(paras + 2, flags & ~0x78, name, noems);
    if (noems)
        WinPrintf("\nNOEMS - memPtr=%p", b);
    h = f_171C_0A5C();
    if (!h)
        Punt("Could not allocate handle");
    *h = (char far *)((long)b + 0x20000L);
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

Handle far f_171C_13CA(long size, int flags, char far *name)
{
    return f_171C_125C(size, flags, name);
}

void far f_171C_13E4(Handle h)
{
    Block far *b;
    char name[13];

    INIT();
    CHECKH(h);
    b = HDR(h);
    if (b->type != 5)
        f_171C_0160(b, 1);
    if (HDR(h)->lock) {
        _fmemcpy(name, b->name, 13);
        name[12] = 0;
        Punt("LOCKED FREED %s", (char far *)name);
    }
    HDR(h)->lock = 0;
    f_171C_1246(h);
}

long far f_171C_14BE(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->age - s_2F30;
}

void far f_171C_152C(Handle h)
{
    INIT();
    CHECKH(h);
    HDR(h)->age = s_2F30++;
}

void far f_171C_15A2(Handle h, int flags)
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

int far f_171C_1686(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->type;
}

long far f_171C_16EA(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->size;
}

long far f_171C_1750(void)
{
    INIT();
    return (unsigned long)s_2F3E << 4;
}

long far f_171C_1772(void)
{
    INIT();
    return (unsigned long)s_2F38 << 4;
}

int far f_171C_1794(Handle h)
{
    INIT();
    CHECKH(h);
    if (HDR(h)->type == 5)
        return 1;
    return 0;
}

void far f_171C_1804(Handle h)
{
    Block far *b;

    INIT();
    CHECKH(h);
    if (h && HDR(h)->type != 5) {
        b = HDR(h);
        *h = (char far *)((long)fd_50F6_3948 + 0x20000L);
        f_171C_0160(b, 1);
    }
}

Handle far f_171C_18A6(Handle h, long size, int flags)
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
            f_194D_0006((char far *)((long)nb + 0x20000L), *h, paras - 2 < oldParas ? paras - 2 : oldParas);
            f_171C_0160(HDR(h), 1);
        }
        *h = (char far *)((long)nb + 0x20000L);
    }
    HDR(h)->age = s_2F30++;
    return h;
}

Handle far f_171C_1A9E(long size, int flags, char far *name)
{
    Handle h;

    h = f_171C_125C(size, flags, name);
    return (Handle)((long)(s_2F46 - h) + 0xF0EFFFFL);
}

int far f_171C_1AD4(Handle h)
{
    CHECKH(h);
    return HDR(h)->lock;
}

Handle far f_171C_1B2C(Handle h, long size, int flags)
{
    CHECKH(h);
    return f_171C_18A6(h, size, flags);
}

char far * far f_171C_1B84(Handle h)
{
    Handle p;

    p = f_171C_1FC2(h);
    if (!p)
        return 0L;
    return *p;
}

Handle far f_171C_1BBA(Handle h)
{
    CHECKH(h);
    return f_171C_2086(h);
}

void far f_171C_1C0A(Handle h)
{
    f_171C_13E4(h);
}

long far f_171C_1C1C(Handle h)
{
    INIT();
    CHECKH(h);
    return HDR(h)->size;
}

void far f_171C_1C82(Handle h)
{
    CHECKH(h);
    f_171C_15A2(h, 3);
}

char far * far f_171C_1CD6(Handle h)
{
    CHECKH(h);
    if (HDR(h)->lock)
        return *h;
    return 0L;
}

char far * far f_171C_1D40(Handle h)
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
        return f_171C_1B84(h);
    BLK(SEG(p) - 2)->type = 1;
    nb = f_171C_0FBC(paras, type);
    b = HDR(h);
    f_194D_0006(nb, b, paras);
    nb->type = type;
    nb->paras = paras;
    *h = (char far *)((long)nb + 0x20000L);
    f_171C_0160(b, 1);
    return f_171C_1B84(h);
}

void far f_171C_1E86(Handle h, int flags)
{
    f_171C_15A2(h, flags);
}

int far f_171C_1E9A(Handle h)
{
    CHECKH(h);
    if (SEG(*h) > fd_50F6_3950)
        return 1;
    return 0;
}

void far f_171C_1EFA(void)
{
    Handle h;
    int n;

    h = s_2F46 - 1;
    for (n = g_2F44; n; h--) {
        if (*h) {
            if (HDR(h)->type == 3)
                f_171C_1804(h);
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

Handle far f_171C_1FC2(Handle h)
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

Handle far f_171C_2086(Handle h)
{
    if (h > s_2F46 - 1 || h < s_2F46 - g_2F42)
        Punt("RU: Bad handle in unlock");
    HDR(h)->lock--;
    return (Handle)((long)(s_2F46 - h) + 0xF0EFFFFL);
}

void far f_171C_20E2(Handle h)
{
    CHECKH(h);
    f_171C_15A2(h, 3);
}

Handle far f_171C_2136(char far *p)
{
    char far *q;
    Handle h;

    q = p;
    h = (Handle)((char far *)s_2F46 + BLK(SEG(q) - 2)->handle);
    if (*h != q)
        Punt("FindMemoryHandle: memPtr block has bad handle");
    return h;
}

char far * far f_171C_2190(unsigned size, char far *name)
{
    char far *p;

    INIT();
    s_2F2A++;
    p = *f_171C_13CA((long)size, 0, name);
    s_2F2A--;
    return p;
}

char far * far f_171C_21CC(unsigned size)
{
    char far *p;

    INIT();
    s_2F2A++;
    p = *f_171C_13CA((long)size, 0, "malloc");
    s_2F2A--;
    return p;
}

void far * far malloc(unsigned size)
{
    return f_171C_21CC(size);
}

void far _ffree(char far *p)
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
        return f_171C_21CC(size);
    h = f_171C_2136(p);
    if (!h)
        Punt("_frealloc: Could not find memory ptr");
    h = f_171C_18A6(h, (long)size, 0);
    s_2F2A--;
    return *h;
}

void far * far f_171C_2302(void far *p, unsigned size)
{
    return _frealloc(p, size);
}

/* WIDTH-1: the paragraph-address sum uses a word segment and an unsigned-long
 * paragraph count. Both contributions are unsigned words; the shifted BLK address
 * has the same value as NEXTBLK. The mixed-width expression reproduces DX. */
