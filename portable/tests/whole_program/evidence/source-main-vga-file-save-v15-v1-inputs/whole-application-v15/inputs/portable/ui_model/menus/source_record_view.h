#ifndef SIMANT_PORTABLE_MENU_SOURCE_RECORD_VIEW_H
#define SIMANT_PORTABLE_MENU_SOURCE_RECORD_VIEW_H

#include "../../game/resources/database.h"

/* Native pointer sidecar over one already-loaded kind-6 record. The record
 * owns and retains the decompressed payload; this view allocates only native
 * pointer vectors and never copies or relocates resource bytes. */
typedef struct PortableMenuSourceRecordView {
    char ***tables;
    char **titles;
    char **items[16];
    size_t table_count;
    const PortableDbRecord *record_owner;
    const void *payload_owner;
    const uint8_t *payload_data;
    size_t payload_size;
    char **handle_owner;
} PortableMenuSourceRecordView;

typedef enum PortableMenuSourceRecordStatus {
    PORTABLE_MENU_SOURCE_RECORD_OK = 0,
    PORTABLE_MENU_SOURCE_RECORD_BAD_ARGUMENT,
    PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE,
    PORTABLE_MENU_SOURCE_RECORD_OUT_OF_MEMORY
} PortableMenuSourceRecordStatus;

void portable_menu_source_record_view_init(PortableMenuSourceRecordView *view);
void portable_menu_source_record_view_release(PortableMenuSourceRecordView *view);
PortableMenuSourceRecordStatus portable_menu_source_record_view_bind(
    PortableMenuSourceRecordView *view, const PortableDbRecord *record);
/* Bind directly to one source-visible SimHandle (`char **`) and its current
 * payload byte length. Does not lock, copy, release or register the handle. */
PortableMenuSourceRecordStatus portable_menu_source_record_view_bind_handle(
    PortableMenuSourceRecordView *view, char **handle, int32_t payload_size);
char ***portable_menu_source_record_tables(
    const PortableMenuSourceRecordView *view);

#endif
