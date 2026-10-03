#include "portable/whole_program/state/yard_cache_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
#include <stddef.h>
/*
 * Object cache table (root module, code frame 1A96).
 * Win16 counterpart: unit simtwo_8F46 (ch_* functions).
 * A cache table is a DOS memory handle (far pointer to a far master pointer).
 */

#include <string.h>

typedef union {
    struct {
        int16_t id;
        int16_t type;
    } k;
        SimYardCacheHandle h;
} CacheEntry;

typedef struct {
    int16_t count;
    int16_t used;
    CacheEntry e[1];
} CacheTable;

typedef CacheTable  *  *CacheHandle;

extern void  *  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern void  f_171C_13E4(void  *handle);
extern uint32_t f_171C_14BE(SimYardCacheHandle handle);
extern void f_171C_152C(SimYardCacheHandle handle);
extern int16_t f_171C_1686(SimYardCacheHandle handle);
extern int16_t f_171C_1794(SimYardCacheHandle handle);
extern int16_t f_171C_1AD4(SimYardCacheHandle handle);
extern void  *  dos_malloc(int16_t size);
extern void  dos_free(void  *p);
extern void  Punt(char  *format, ...);

SimYardCacheHandle (*g_3B7E)(int16_t object, int16_t type) = 0;
SimYardCacheHandle (*g_3B82)(int16_t object, int16_t type) = 0;
static int16_t s_3B86 = 0;
static int32_t s_3B88 = 0L;
static int32_t s_3B8C = 0L;
static int32_t s_3B90 = 0L;
static int32_t s_3B94 = 0L;
static int16_t s_8C7A;

int16_t  ch_GetPrime(int16_t n);
int16_t  ch_CleanupTable(CacheHandle table);
int16_t  ch_DumpOldest(CacheHandle table);
SimYardCacheHandle ch_LookUpId(int16_t object, int16_t type, CacheHandle table);

CacheHandle  ch_CreateTable(int16_t size)
{
    CacheHandle table;

    if (size == 0)
        size = 503;
    else
        size = ch_GetPrime(size);
    _fmemset(*(table = f_171C_13CA((int32_t)(offsetof(CacheTable, e) + (int32_t)size * 2 * sizeof(CacheEntry)), 0, "cachetable")), -1, offsetof(CacheTable, e) + (int32_t)size * sizeof(CacheEntry));
    (*table)->count = size;
    (*table)->used = 0;
    return table;
}

int16_t  ch_RemoveEntry(int16_t object, int16_t type, CacheHandle table)
{
    if (ch_LookUpId(object, type, table)) {
        (*table)->e[s_3B86].k.id = -1;
        (*table)->e[(*table)->count + s_3B86].h = 0L;
        (*table)->used--;
        return 1;
    }
    return 0;
}

void  ch_PurgeCache(CacheHandle table)
{
    int16_t count;
    int16_t i;
    CacheEntry  *p;

    count = (*table)->count;
    p = (*table)->e;
    for (i = 0; i < count; p++, i++) {
        if (p->k.id != -1)
            f_171C_13E4((*table)->e[i + count].h);
    }
    f_171C_13E4(table);
}

int16_t ch_LookUpHandle(SimYardCacheHandle handle, CacheHandle table, int16_t *object, int16_t *type)
{
    int16_t i;
    int16_t count;
    CacheEntry  *key;
    CacheEntry  *hp;

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

SimYardCacheHandle ch_LookUpId(int16_t object, int16_t type, CacheHandle table)
{
    SimYardCacheHandle handle;
    int16_t probes;
    int16_t count;
    int16_t start;
    int16_t i;
    CacheEntry  *base;
    CacheEntry  *p;

    probes = 0;
    if (g_3B7E) {
        handle = (*g_3B7E)(object, type);
        if (handle)
            return handle;
    }
    count = (*table)->count;
    base = (*table)->e;
    i = start = (object + (object >> 8) + type * 7) % count;
    p = base + i;
    for (; i >= 0; i--, p--, probes++) {
        if (p->k.id == object && p->k.type == type)
            goto found;
        if (p->k.id == -1)
            goto missing;
    }
    for (i = count - 1, p = base + i; i >= start; i--, p--) {
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

int16_t ch_AddEntry(int16_t object, int16_t type, CacheHandle table, SimYardCacheHandle handle)
{
     int16_t used;
    int16_t count;

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

int16_t  ch_DeleteEntry(int16_t object, int16_t type, CacheHandle table)
{
    if (ch_LookUpId(object, type, table)) {
        (*table)->e[s_3B86].k.id = -1;
        (*table)->e[(*table)->count + s_3B86].h = 0L;
        (*table)->used--;
        return 1;
    }
    return 0;
}

int16_t  ch_CleanupTable(CacheHandle table)
{
    int16_t count;
    CacheEntry  *hp;
    CacheEntry  *kp;

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

int16_t  ch_DumpOldest(CacheHandle table)
{
    uint32_t oldest;
    uint32_t age;
    int16_t count;
    CacheEntry  *hp;
    CacheEntry  *kp;
    CacheEntry  *oldH;
    CacheEntry  *oldK;
    CacheTable  *tp;

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

int16_t  ch_GetPrime(int16_t n)
{
    int16_t prime;
    int16_t cand;
    int16_t  *primes;
    int16_t j;
    int16_t nprimes;

    prime = 1;
    cand = 2;
    nprimes = 0;
    primes = dos_malloc(800);
    for (; prime < n; cand++) {
        if (nprimes >= 400)
            break;
        for (j = 0; j < nprimes; j++)
            if (cand % primes[j] == 0)
                goto next;
        primes[nprimes++] = prime = cand;
next:   ;
    }
    dos_free(primes);
    return prime;
}

void ch_SetCacheHooks(SimYardCacheHandle (*cache)(int16_t object, int16_t type),
                     SimYardCacheHandle (*release)(int16_t object, int16_t type))
{
    g_3B7E = cache;
    g_3B82 = release;
}

#pragma pack(pop)
