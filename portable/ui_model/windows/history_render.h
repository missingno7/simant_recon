#ifndef SIMANT_PORTABLE_UI_WINDOWS_HISTORY_RENDER_H
#define SIMANT_PORTABLE_UI_WINDOWS_HISTORY_RENDER_H

#include <stddef.h>
#include <stdint.h>
#include "../../render/primitives.h"
#include "../../render/font.h"
#include "../../game/resources/database.h"
#include "registry.h"
#include "render.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    PORTABLE_HISTORY_SERIES_COUNT = 10,
    PORTABLE_HISTORY_SAMPLES = 64,
    PORTABLE_HISTORY_VISIBLE_GRAPHS = 4,
    PORTABLE_HISTORY_WINDOW_ID = 0x1500,
    PORTABLE_HISTORY_OBJECT_ID = 0x150e,
    PORTABLE_HISTORY_LABELS_ID = 1050,
    PORTABLE_HISTORY_STRING_KIND = 4,
    PORTABLE_HISTORY_MAX_TEXT = 256,
    PORTABLE_HISTORY_MAX_COMMANDS = 4 + 63 + 6
};

typedef struct PortableHistoryRect {
    int16_t left, top, right, bottom;
} PortableHistoryRect;

typedef enum PortableHistoryCommandKind {
    PORTABLE_HISTORY_SET_COLOR,
    PORTABLE_HISTORY_SET_FONT,
    PORTABLE_HISTORY_LINE,
    PORTABLE_HISTORY_TEXT,
    PORTABLE_HISTORY_OUTLINE,
    PORTABLE_HISTORY_FILL_OBJECT,
    PORTABLE_HISTORY_DRAW_GRAPH
} PortableHistoryCommandKind;

typedef struct PortableHistoryCommand {
    PortableHistoryCommandKind kind;
    int16_t a, b, c, d, e;
    uint16_t text_size;
    char text[PORTABLE_HISTORY_MAX_TEXT];
} PortableHistoryCommand;

typedef enum PortableHistoryStatus {
    PORTABLE_HISTORY_OK = 0,
    PORTABLE_HISTORY_BAD_ARGUMENT,
    PORTABLE_HISTORY_BAD_DOMAIN,
    PORTABLE_HISTORY_PROVIDER_FAILED,
    PORTABLE_HISTORY_OUTPUT_FULL,
    PORTABLE_HISTORY_TEXT_TOO_LONG,
    PORTABLE_HISTORY_RASTER_UNSUPPORTED,
    PORTABLE_HISTORY_RASTER_FAILED
} PortableHistoryStatus;

typedef int (*PortableHistoryGetRect)(void *context, int16_t window_id,
    int16_t object_id, PortableHistoryRect *rect);
typedef int (*PortableHistoryGetFontHeight)(void *context, int16_t *height);
typedef int (*PortableHistoryGetTextWidth)(void *context, const char *text,
    size_t text_size, int16_t *width);
typedef int (*PortableHistoryGetFillColor)(void *context, int16_t object_id,
    int16_t *color);

typedef struct PortableHistoryProviders {
    void *context;
    PortableHistoryGetRect get_object_rect;
    PortableHistoryGetFontHeight get_font_height;
    PortableHistoryGetTextWidth get_text_width;
    PortableHistoryGetFillColor get_fill_color;
} PortableHistoryProviders;

typedef int (*PortableHistoryResolveColor)(void *context, int16_t source_color,
    uint8_t *framebuffer_color);
typedef int (*PortableHistoryFillObject)(void *context, int16_t object_id,
    int16_t source_color, uint8_t framebuffer_color);

typedef struct PortableHistoryRasterProviders {
    void *context;
    PortableFramebuffer *framebuffer;
    const PortableFont *font3; /* Resource-selected source font ID 3 (FONT2). */
    PortableHistoryResolveColor resolve_color;
    PortableHistoryFillObject fill_object;
} PortableHistoryRasterProviders;

typedef struct PortableHistoryInput {
    /* Current SimSetupState.history_series[10][64], in S24 source order. */
    int16_t series[PORTABLE_HISTORY_SERIES_COUNT][PORTABLE_HISTORY_SAMPLES];
    int16_t history_color[PORTABLE_HISTORY_SERIES_COUNT];
    int16_t graph_colors[4];
    const char *labels[PORTABLE_HISTORY_SERIES_COUNT];
    size_t label_sizes[PORTABLE_HISTORY_SERIES_COUNT];
    int16_t start;
    int16_t count;
    int16_t graph;
    int16_t hilite;
    int16_t slot;
} PortableHistoryInput;

typedef struct PortableHistoryLabels {
    size_t count;
    char **items;
    size_t *sizes;
    char *storage;
} PortableHistoryLabels;

typedef struct PortableHistoryUiSnapshot {
    int16_t graph_colors[4];
    int16_t history_color[PORTABLE_HISTORY_SERIES_COUNT];
    int16_t shown_graphs[PORTABLE_HISTORY_VISIBLE_GRAPHS];
} PortableHistoryUiSnapshot;

typedef struct PortableHistoryActiveResources {
    PortableHistoryLabels labels;
    PortableWindowRegistry *registry; /* Borrowed, loaded HCEGANT windows. */
    const PortableWindowRenderer *renderer; /* Borrowed active colors/fonts. */
    PortableFramebuffer *framebuffer; /* Borrowed while raster providers are active. */
    PortableHistoryRect current_window_rect;
    uint8_t ready;
} PortableHistoryActiveResources;

typedef struct PortableHistoryWindowInput {
    PortableHistoryInput render;
    int16_t flags;
    int16_t shown_graphs[PORTABLE_HISTORY_VISIBLE_GRAPHS];
} PortableHistoryWindowInput;

/* Emits the ordered logical service requests made by drawHistGraph. The
 * supported oracle-comparison domain is start 0..63, count 0..64, graph 0..9,
 * slot 0..3, resource labels shorter than 256 bytes, and positive geometry
 * that keeps 16-bit source calculations defined. All arithmetic that can
 * wrap in the DOS 16-bit int model is evaluated through explicit int16 wraps. */
PortableHistoryStatus portable_history_render_graph(
    const PortableHistoryInput *input, const PortableHistoryProviders *providers,
    PortableHistoryCommand *commands, size_t capacity, size_t *command_count);

/* Models win_DrawHistoryWindow's flags & 2 gate and source slot order. Emits a
 * fill request followed by each selected graph's expanded command trace. */
PortableHistoryStatus portable_history_render_window(
    const PortableHistoryWindowInput *input,
    const PortableHistoryProviders *providers,
    PortableHistoryCommand *commands, size_t capacity, size_t *command_count);

/* Rasterizes the normalized logical trace with the supplied source-resource
 * font, palette resolver, and window-fill hook. Line segments use the host
 * framebuffer line routine here; this path has native output only and carries
 * no DOS-pixel equivalence claim. */
PortableHistoryStatus portable_history_rasterize(
    const PortableHistoryCommand *commands, size_t command_count,
    const PortableHistoryRasterProviders *providers);

const char *portable_history_status_string(PortableHistoryStatus status);

/* LoadStringAnt(1050), used by PrepareStrings for fd_50F6_02BA. The first
 * ten counted strings are borrowed by a bound render input until labels_free. */
PortableHistoryStatus portable_history_labels_load(
    PortableHistoryLabels *labels, PortableDatabase *shared_database);
void portable_history_labels_free(PortableHistoryLabels *labels);

/* Source lookup table order recovered from fd_3D57_082A/0852. Both source
 * far pointers are resolved through the same ten session arrays, so graph 6's
 * paired pointers naturally alias series 6. Label pointers borrow `labels`. */
PortableHistoryStatus portable_history_bind_session(
    PortableHistoryInput *input,
    const int16_t history_series[PORTABLE_HISTORY_SERIES_COUNT][PORTABLE_HISTORY_SAMPLES],
    int16_t history_start, int16_t history_count, int16_t graph,
    int16_t hilite, int16_t slot, const PortableHistoryUiSnapshot *ui,
    const PortableHistoryLabels *labels);

PortableHistoryStatus portable_history_bind_window(
    PortableHistoryWindowInput *input,
    const int16_t history_series[PORTABLE_HISTORY_SERIES_COUNT][PORTABLE_HISTORY_SAMPLES],
    int16_t history_start, int16_t history_count, int16_t flags,
    const PortableHistoryUiSnapshot *ui, const PortableHistoryLabels *labels);

/* Bind actual SHARED:1050 labels, HCEGANT:0x150e geometry, HCEGANT color
 * entries, and the active source font ID 3 (FONT2). Registry, renderer and
 * both databases/resources remain caller-owned. The rect can be refreshed
 * from the live window manager after move/recalculation. */
PortableHistoryStatus portable_history_active_resources_load(
    PortableHistoryActiveResources *resources,
    PortableDatabase *shared_database, PortableWindowRegistry *registry,
    const PortableWindowRenderer *renderer);
void portable_history_active_resources_free(
    PortableHistoryActiveResources *resources);
PortableHistoryStatus portable_history_active_resources_set_rect(
    PortableHistoryActiveResources *resources,
    const PortableHistoryRect *current_rect);
void portable_history_active_providers(
    PortableHistoryActiveResources *resources,
    PortableHistoryProviders *providers);
void portable_history_active_raster_providers(
    PortableHistoryActiveResources *resources,
    PortableFramebuffer *framebuffer,
    PortableHistoryRasterProviders *providers);

#ifdef __cplusplus
}
#endif
#endif

