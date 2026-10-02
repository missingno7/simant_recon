#ifndef SIMANT_PORTABLE_UI_MODEL_DIALOGS_END_GAME_VIEW_H
#define SIMANT_PORTABLE_UI_MODEL_DIALOGS_END_GAME_VIEW_H

#include "end_game_flow.h"
#include "../windows/open.h"
#include "../windows/render.h"
#include "../../game/resources/fonts.h"

#include <stddef.h>

typedef enum PortableEndGameViewStatus {
    PORTABLE_END_GAME_VIEW_OK = 0,
    PORTABLE_END_GAME_VIEW_BAD_ARGUMENT,
    PORTABLE_END_GAME_VIEW_DATABASE_ERROR,
    PORTABLE_END_GAME_VIEW_INVALID_RESOURCE,
    PORTABLE_END_GAME_VIEW_INVALID_STATE,
    PORTABLE_END_GAME_VIEW_UNSUPPORTED_WINDOW,
    PORTABLE_END_GAME_VIEW_UNSUPPORTED_FONT,
    PORTABLE_END_GAME_VIEW_RENDER_ERROR
} PortableEndGameViewStatus;

typedef struct PortableEndGameString {
    const uint8_t *bytes; /* Borrowed from a retained SHARED kind-4 record. */
    size_t length;
} PortableEndGameString;

/* Owns the two SHARED string records and the transient formatted score text.
 * Registry/window-open state, renderer, fonts, and databases are borrowed. */
typedef struct PortableEndGameView {
    SimGameOverResult summary;
    PortableDbRecord scenario_record;
    PortableDbRecord level_record;
    PortableEndGameString *scenario_strings;
    size_t scenario_string_count;
    PortableEndGameString *level_strings;
    size_t level_string_count;
    PortableEndGameString scenario_text;
    PortableEndGameString level_text;
    char score_text[32];
    size_t score_text_length;
    uint16_t screen_width;
    int16_t active_font_id;
    int16_t text_font_id;
    uint8_t initialized;
    uint8_t window_open_seen;
    uint8_t scenario_text_ready;
    uint8_t score_text_ready;
    uint8_t level_text_ready;
} PortableEndGameView;

void portable_end_game_view_init(PortableEndGameView *view);
void portable_end_game_view_release(PortableEndGameView *view);

/* Loads and retains actual SHARED kind-4 resources 1001 and 1900. This does
 * not open, move, recalculate, or close HCEGANT window 0x0400. */
PortableEndGameViewStatus portable_end_game_view_prepare(
    PortableEndGameView *view, PortableDatabase *shared_database,
    const SimGameOverResult *summary, uint16_t screen_width);

/* These have the corresponding SimEndGameFlowHost callback signatures.
 * Window 0x0400 lifecycle remains the caller's explicit window-manager job. */
int portable_end_game_view_note_open(void *context, int16_t window_id);
int portable_end_game_view_set_font(void *context, int16_t font_id);
int portable_end_game_view_set_resource_text(void *context, int16_t object_id,
                                             int16_t resource_id, int16_t index);
int portable_end_game_view_set_score_text(void *context, int16_t object_id,
                                          int32_t score);

/* Renders only after the source open manager has loaded/recalculated and
 * opened 0x0400. It preserves the manager's current object coordinates. */
PortableEndGameViewStatus portable_end_game_view_render(
    const PortableEndGameView *view, const PortableWindowRegistry *registry,
    const PortableWindowOpenScene *scene, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer);

const char *portable_end_game_view_status_string(
    PortableEndGameViewStatus status);

#endif
