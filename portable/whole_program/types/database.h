/* Three historical TUs share one database table. Only index/header payloads
 * are file records; the outer table owns a real native index pointer.
 * Wire offsets and sizes follow m1986/m19A9/m1A28 reads, not host sizeof(ptr).
 */
#ifndef SIMANT_WHOLE_DATABASE_H
#define SIMANT_WHOLE_DATABASE_H
#include <stdint.h>
#include <stddef.h>
#if !defined(__BYTE_ORDER__) || __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Direct source record I/O requires a little-endian host; use field codecs elsewhere"
#endif
#pragma pack(push, 2)
typedef struct {
    int32_t offset;
    int16_t id;
    uint8_t kind;
    uint8_t flags;
} IndexEntry;
typedef struct {
    int16_t count;
    int16_t spare;
    int32_t stat1;
    int32_t stat2;
    int32_t stat3;
    int16_t field8;
    int16_t field9;
} IndexHeader;
typedef struct {
    int32_t magic;
    int16_t count;
    int32_t freeBytes;
    int32_t wastedBytes;
} DBHeader;
typedef struct {
    int16_t id;
    int16_t type;
    int16_t flags;
    int16_t size;
    int16_t extra;
} DBRecordHeader;
#pragma pack(pop)
typedef struct {
    char name[0x50];
    IndexEntry *index;
    IndexHeader indexHeader;
    union {
        DBHeader header;
        char dbHeader[14];
    };
    int16_t indexFile;
    int16_t file;
    int16_t dirty;
} OpenDBRec;
_Static_assert(sizeof(IndexEntry) == 8, "source count*8 index rows");
_Static_assert(offsetof(IndexEntry, id) == 4, "index id");
_Static_assert(offsetof(IndexEntry, kind) == 6, "index kind");
_Static_assert(offsetof(IndexEntry, flags) == 7, "index flags");
_Static_assert(sizeof(IndexHeader) == 20, "source index header read");
_Static_assert(sizeof(DBHeader) == 14, "source database header read");
_Static_assert(offsetof(DBHeader, freeBytes) == 6, "database free count");
_Static_assert(sizeof(DBRecordHeader) == 10, "source record header read");
/* GetFreeHandle initializes and searches exactly four source slots. */
extern OpenDBRec fd_50F6_3958[4];
extern IndexEntry *fd_50F6_3952;
extern int16_t fd_50F6_3956;
#endif
