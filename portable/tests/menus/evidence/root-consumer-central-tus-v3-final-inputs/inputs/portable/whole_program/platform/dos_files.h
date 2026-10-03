/* Source-visible directory enumeration record. This is a wire-sized record,
 * not the host's _finddata_t. Provider iteration state belongs to the platform.
 * Layout grounded in MSC 6.00A include/dos.h, _dos_findfirst structure. */
#ifndef SIMANT_WHOLE_DOS_FILES_H
#define SIMANT_WHOLE_DOS_FILES_H
#include <stdint.h>
#include <stddef.h>
extern int16_t dos_errno;
#pragma pack(push, 1)
struct find_t {
    char reserved[21];
    char attrib;
    uint16_t wr_time;
    uint16_t wr_date;
    int32_t size;
    char name[13];
};
#pragma pack(pop)
_Static_assert(sizeof(struct find_t) == 43, "MSC find_t wire size");
_Static_assert(offsetof(struct find_t, name) == 30, "MSC filename offset");
uint16_t _dos_findfirst(const char *pattern, uint16_t attributes, struct find_t *result);
uint16_t _dos_findnext(struct find_t *result);
#endif
