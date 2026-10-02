#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_TITLES_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_TITLES_H

#include "../../game/resources/database.h"

#include <stddef.h>
#include <stdint.h>

enum {
    PORTABLE_TITLE_MAP_TABLE_ID = 1000,
    PORTABLE_TITLE_SCENARIO_TABLE_ID = 1001,
    PORTABLE_TITLE_EDIT_SUFFIX_TABLE_ID = 1800,
    PORTABLE_TITLE_STRING_KIND = 4,
    PORTABLE_TITLE_MAX_BYTES = 100,
    PORTABLE_TITLE_EDIT_SUFFIX_INDEX = 15,
    PORTABLE_TITLE_EDIT_WINDOW_ID = 0,
    PORTABLE_TITLE_MAP_WINDOW_ID = 0x0100,
    PORTABLE_TITLE_YARD_WINDOW_ID = 0x1900,
    PORTABLE_TITLE_EDIT_OBJECT_ID = 0x0001,
    PORTABLE_TITLE_MAP_OBJECT_ID = 0x0101,
    PORTABLE_TITLE_YARD_OBJECT_ID = 0x1901
};

typedef enum PortableWindowTitlesStatus {
    PORTABLE_WINDOW_TITLES_OK = 0,
    PORTABLE_WINDOW_TITLES_BAD_ARGUMENT,
    PORTABLE_WINDOW_TITLES_DATABASE_ERROR,
    PORTABLE_WINDOW_TITLES_INVALID_RESOURCE,
    PORTABLE_WINDOW_TITLES_OUT_OF_MEMORY,
    PORTABLE_WINDOW_TITLES_INVALID_SCENE,
    PORTABLE_WINDOW_TITLES_TEXT_TOO_LONG,
    PORTABLE_WINDOW_TITLES_NOT_READY
} PortableWindowTitlesStatus;

typedef struct PortableTitleStringTable {
    size_t count;
    char **items;
    char *storage;
} PortableTitleStringTable;

typedef struct PortableWindowTitlesStringSet {
    PortableTitleStringTable map_modes;       /* kind 4 / object 1000 */
    PortableTitleStringTable scenarios;       /* kind 4 / object 1001 */
    PortableTitleStringTable edit_suffixes;   /* kind 4 / object 1800 */
    uint8_t loaded;
} PortableWindowTitlesStringSet;

typedef struct PortableWindowTitleScene {
    int16_t scenario;   /* fd_50F6_0EAC */
    int16_t map_mode;   /* fd_3D57_07C8 */
    int16_t yard_mode;  /* YardMode */
    uint8_t edit_window_open;
    uint8_t map_window_open;
    uint8_t yard_window_open;
} PortableWindowTitleScene;

typedef struct PortableWindowTitleValue {
    uint16_t object_id;
    uint16_t redraw_window_id;
    uint8_t redraw;
    size_t text_size;
    uint8_t text[PORTABLE_TITLE_MAX_BYTES];
} PortableWindowTitleValue;

typedef struct PortableWindowTitleProjection {
    PortableWindowTitleValue edit;
    PortableWindowTitleValue map;
    PortableWindowTitleValue yard;
    uint8_t valid;
} PortableWindowTitleProjection;

/* `strings` must be zero-initialized before its first load. Loads the three
 * actual SHARED kind-4 resources consumed by PrepareStrings.
 * The record's first byte is skipped, followed by the count and length-prefixed
 * strings used by LoadStringAnt. */
PortableWindowTitlesStatus portable_window_titles_load(
    PortableWindowTitlesStringSet *strings,
    PortableDatabase *shared_database);
void portable_window_titles_free(PortableWindowTitlesStringSet *strings);

/* Compute SetEditWinTitle and SetMapTitle outputs from current source state.
 * The output records preserve exact target object IDs and redraw routing. */
PortableWindowTitlesStatus portable_window_titles_update(
    const PortableWindowTitlesStringSet *strings,
    const PortableWindowTitleScene *scene,
    PortableWindowTitleProjection *projection);

/* Signature-compatible with PortableWindowRenderer.resolve_text. It resolves
 * only title objects in the latest projection; every other formatted object
 * remains the renderer's explicit unsupported path. */
int portable_window_titles_resolve_text(
    void *context, int16_t window_id, uint16_t object_index,
    const uint8_t *format, size_t format_size,
    const uint8_t **text, size_t *text_size);

const char *portable_window_titles_status_string(
    PortableWindowTitlesStatus status);

#endif
