#ifndef SIMANT_PORTABLE_GAME_RESOURCES_ADVICE_H
#define SIMANT_PORTABLE_GAME_RESOURCES_ADVICE_H

#include "database.h"

#include <stddef.h>
#include <stdint.h>

typedef enum PortableAdviceTableId {
    PORTABLE_ADVICE_SHARED_MESSAGES = 1010, /* DOS fd_50F6_034C */
    PORTABLE_ADVICE_TUTORIAL = 1020        /* DOS AdviceStrs */
} PortableAdviceTableId;

typedef enum PortableAdviceStatus {
    PORTABLE_ADVICE_OK = 0,
    PORTABLE_ADVICE_BAD_ARGUMENT,
    PORTABLE_ADVICE_DATABASE_ERROR,
    PORTABLE_ADVICE_INVALID_RESOURCE,
    PORTABLE_ADVICE_OUT_OF_MEMORY,
    PORTABLE_ADVICE_NOT_FOUND
} PortableAdviceStatus;

typedef struct PortableAdviceEntry {
    const char *text;        /* NUL-terminated, owned by the retained record. */
    size_t length;           /* Exact source length byte, including embedded NULs. */
    size_t source_offset;    /* Offset of the original length prefix in that record. */
} PortableAdviceEntry;

typedef struct PortableAdviceTable {
    PortableDbRecord record;
    PortableAdviceEntry *entries;
    const char **pointers;   /* Pascal-style (count+1) far-pointer table, host pointers. */
    void **source_pointers;  /* Separately typed backing for recovered void ** globals. */
    size_t count;
    int16_t resource_id;
} PortableAdviceTable;

typedef struct PortableAdviceResources {
    PortableAdviceTable shared_messages;
    PortableAdviceTable tutorial;
    uint8_t loaded;
} PortableAdviceResources;

typedef struct PortableAdvicePointerInfo {
    PortableAdviceTableId table_id;
    size_t index;
    size_t text_length;
    size_t source_offset;
} PortableAdvicePointerInfo;

void portable_advice_init(PortableAdviceResources *resources);
void portable_advice_free(PortableAdviceResources *resources);

/* Loads the exact kind-4 SHARED resources used by PrepareStrings and retains
 * their backing records for as long as any returned string pointer is used.
 * Destination must be initialized before first load. */
PortableAdviceStatus portable_advice_load(PortableAdviceResources *resources,
                                           PortableDatabase *shared_database);

const PortableAdviceTable *portable_advice_table(
    const PortableAdviceResources *resources, PortableAdviceTableId table_id);

/* Bounds-checked indexed view and source-compatible pointer-table access. */
int portable_advice_get(const PortableAdviceResources *resources,
                        PortableAdviceTableId table_id, size_t index,
                        PortableAdviceEntry *entry);
const char *const *portable_advice_pointers(
    const PortableAdviceResources *resources, PortableAdviceTableId table_id,
    size_t *count);

/* Source-signature-compatible pointer table for recovered void ** globals.
 * This storage is distinct from the typed const-char pointer table. */
void **portable_advice_source_pointers(
    PortableAdviceResources *resources, PortableAdviceTableId table_id,
    size_t *count);

/* Convert a live host pointer back to its source table/slot/length/record
 * offset. Only exact pointers issued by this owner are accepted. */
int portable_advice_normalize_pointer(
    const PortableAdviceResources *resources, const char *pointer,
    PortableAdvicePointerInfo *info);

const char *portable_advice_status_string(PortableAdviceStatus status);

#endif
