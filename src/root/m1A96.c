/*
 * Object cache table (root module, code frame 1A96).
 * Win16 counterpart: unit simtwo_8F46 (ch_* functions).
 * A cache table is a DOS memory handle (far pointer to a far master pointer).
 */

typedef union {
    struct {
        int id;
        int type;
    } k;
    char far *h;
} CacheEntry;

typedef struct {
    int count;
    int used;
    CacheEntry e[1];
} CacheTable;

typedef CacheTable far * far *CacheHandle;

extern void far * far f_171C_13CA(long size, int flags, char far *name);
extern void far f_171C_13E4(void far *handle);
extern unsigned long far f_171C_14BE(char far *handle);
extern void far f_171C_152C(char far *handle);
extern int far f_171C_1686(char far *handle);
extern int far f_171C_1794(char far *handle);
extern int far f_171C_1AD4(char far *handle);
extern void far * far f_171C_2208(int size);
extern void far f_171C_2276(void far *p);
extern void far * far _fmemset(void far *dst, int c, unsigned int n);
extern void far Punt(char far *format, ...);

char far * (far *g_3B7E)(int object, int type) = 0L;
char far * (far *g_3B82)(int object, int type) = 0L;
static int s_3B86 = 0;
static long s_3B88 = 0L;
static long s_3B8C = 0L;
static long s_3B90 = 0L;
static long s_3B94 = 0L;
static int s_8C7A;

int far ch_GetPrime(int n);
int far ch_CleanupTable(CacheHandle table);
int far ch_DumpOldest(CacheHandle table);
char far * far ch_LookUpId(int object, int type, CacheHandle table);

CacheHandle far ch_CreateTable(int size)
{
    CacheHandle table;

    if (size == 0)
        size = 503;
    else
        size = ch_GetPrime(size);
    _fmemset(*(table = f_171C_13CA((long)(size * 8 + 4), 0, "cachetable")), -1, (size + 1) * 4);
    (*table)->count = size;
    (*table)->used = 0;
    return table;
}

int far ch_RemoveEntry(int object, int type, CacheHandle table)
{
    if (ch_LookUpId(object, type, table)) {
        (*table)->e[s_3B86].k.id = -1;
        (*table)->e[(*table)->count + s_3B86].h = 0L;
        (*table)->used--;
        return 1;
    }
    return 0;
}

void far ch_PurgeCache(CacheHandle table)
{
    int count;
    int i;
    CacheEntry far *p;

    count = (*table)->count;
    p = (*table)->e;
    for (i = 0; i < count; p++, i++) {
        if (p->k.id != -1)
            f_171C_13E4((*table)->e[i + count].h);
    }
    f_171C_13E4(table);
}

int far ch_LookUpHandle(char far *handle, CacheHandle table, int far *object, int far *type)
{
    int i;
    int count;
    CacheEntry far *key;
    CacheEntry far *hp;

    count = (*table)->count;
    key = (*table)->e;
    hp = &(*table)->e[count];
    for (i = 0; i < count; i++, key++, hp++) {
        if (key->k.id != -1 && hp->h == handle) {
            *object = key->k.id;
            *type = key->k.type;
            return 1;
        }
    }
    return 0;
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * ch_LookUpId (ch_LookUpId) best draft (/Oeg): 359 vs 354 bytes, same control flow.  Residue:
 * the original keeps the hook result low word in SI (ours DI), computes base before the
 * hash and caches count in SI as the idiv divisor, and keeps the second-loop pointer in
 * ES:BX without storing its segment; 120 declaration orders give identical code. */
char far * far ch_LookUpId(int object, int type, CacheHandle table)
{
    char far *handle;
    int probes;
    int count;
    int start;
    int i;
    CacheEntry far *base;
    CacheEntry far *p;

    probes = 0;
    if (g_3B7E) {
        handle = (*g_3B7E)(object, type);
        if (handle)
            return handle;
    }
    count = (*table)->count;
    base = (*table)->e;
    start = i = (object + (object >> 8) + type * 7) % count;
    p = &base[i];
    for (; i >= 0; i--, p--, probes++) {
        if (p->k.id == object && p->k.type == type)
            goto found;
        if (p->k.id == -1)
            goto missing;
    }
    for (i = count - 1, p = &base[i]; i >= start; i--, p--) {
        if (p->k.id == object && p->k.type == type)
            goto found;
        if (p->k.id == -1)
            goto missing;
        probes++;
    }
    goto missing;
found:
    s_3B90 += probes;
    s_3B88++;
    s_3B86 = i;
    handle = (*table)->e[count + i].h;
    if (f_171C_1794(handle)) {
        ch_CleanupTable(table);
        goto missing;
    }
    f_171C_152C(handle);
    return handle;
missing:
    s_3B86 = i;
    s_3B94 += probes;
    s_3B8C++;
    return 0L;
}
/* SCAFFOLD END */

int far ch_AddEntry(int object, int type, CacheHandle table, char far *handle)
{
    register int used;
    int count;

    count = (*table)->count;
    used = (*table)->used;
    s_8C7A++;
    if (used == count || s_8C7A > 30) {
        s_8C7A = 0;
        if (ch_CleanupTable(table) == count && ch_DumpOldest(table) == count)
            return 0;
    }
    if (ch_LookUpId(object, type, table))
        Punt("Attemp to add ID already present in lookup table");
    (*table)->e[s_3B86].k.id = object;
    (*table)->e[s_3B86].k.type = type;
    (*table)->e[count + s_3B86].h = handle;
    (*table)->used++;
    return 1;
}

int far ch_DeleteEntry(int object, int type, CacheHandle table)
{
    if (ch_LookUpId(object, type, table)) {
        (*table)->e[s_3B86].k.id = -1;
        (*table)->e[(*table)->count + s_3B86].h = 0L;
        (*table)->used--;
        return 1;
    }
    return 0;
}

int far ch_CleanupTable(CacheHandle table)
{
    int count;
    CacheEntry far *hp;
    CacheEntry far *kp;

    count = (*table)->count;
    hp = &(*table)->e[count];
    kp = (*table)->e;
    while (count--) {
        if (kp->k.id != -1 && hp->h && f_171C_1794(hp->h) && !f_171C_1AD4(hp->h)) {
            f_171C_13E4(hp->h);
            kp->k.id = -1;
            (*table)->used--;
        }
        kp++;
        hp++;
    }
    return (*table)->used;
}

int far ch_DumpOldest(CacheHandle table)
{
    unsigned long oldest;
    unsigned long age;
    int count;
    CacheEntry far *hp;
    CacheEntry far *kp;
    CacheEntry far *oldH;
    CacheEntry far *oldK;
    CacheTable far *tp;

    oldest = 0L;
    count = (*table)->count;
    hp = &(*table)->e[count];
    tp = *table;
    kp = tp->e;
    if (tp->used) {
        while (count--) {
            if (kp->k.id != -1) {
                age = f_171C_14BE(hp->h);
                if (age > oldest && f_171C_1686(hp->h) == 3 && !f_171C_1AD4(hp->h)) {
                    oldest = age;
                    oldH = hp;
                    oldK = kp;
                }
            }
            hp++;
            kp++;
        }
        if (oldest == 0L)
            Punt("no memory over 0 in age!");
        f_171C_13E4(oldH->h);
        oldK->k.id = -1;
        oldH->h = 0L;
        (*table)->used--;
    }
    return (*table)->used;
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * ch_GetPrime best draft (/Oeg): equal length, 5 instructions differ.  Residue: the
 * original stores prime = cand before forming the primes[nprimes] address (index BX,
 * base SI); this draft forms the address first (index SI, base BX).  Tried: 12 spellings
 * of the store, register j/nprimes, all 120 declaration orders, while/for/flag forms. */
int far ch_GetPrime(int n)
{
    int prime;
    int cand;
    int far *primes;
    int j;
    int nprimes;

    prime = 1;
    cand = 2;
    nprimes = 0;
    primes = f_171C_2208(800);
    for (; prime < n; cand++) {
        if (nprimes >= 400)
            break;
        for (j = 0; j < nprimes; j++)
            if (cand % primes[j] == 0)
                goto next;
        primes[nprimes++] = prime = cand;
next:   ;
    }
    f_171C_2276(primes);
    return prime;
}
/* SCAFFOLD END */

void far ch_SetCacheHooks(char far * (far *cache)(int object, int type),
                     char far * (far *release)(int object, int type))
{
    g_3B7E = cache;
    g_3B82 = release;
}
