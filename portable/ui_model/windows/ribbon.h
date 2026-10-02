#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_RIBBON_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_RIBBON_H

#include "registry.h"
#include "render.h"
#include "../../game/resources/advice.h"

#include <stdint.h>

enum { PORTABLE_RIBBON_COLOR_INDEX = 3, PORTABLE_RIBBON_FONT_320 = 0,
       PORTABLE_RIBBON_FONT_OTHER = 2 };

typedef int32_t (*PortableRibbonTickProvider)(void *context);

typedef enum PortableRibbonTarget {
    PORTABLE_RIBBON_EDIT_SURFACE = 0, /* win_GetObjRect(4), source 0x0004 */
    PORTABLE_RIBBON_MAP = 1,          /* win_GetObjRect(0x0102) */
    PORTABLE_RIBBON_YARD = 2          /* win_GetObjRect(0x1902), then left++ */
} PortableRibbonTarget;

typedef enum PortableRibbonStatus {
    PORTABLE_RIBBON_OK = 0,
    PORTABLE_RIBBON_BAD_ARGUMENT,
    PORTABLE_RIBBON_UNKNOWN_MESSAGE,
    PORTABLE_RIBBON_REGISTRY_ERROR,
    PORTABLE_RIBBON_UNSUPPORTED_FONT,
    PORTABLE_RIBBON_INVALID_GEOMETRY,
    PORTABLE_RIBBON_RENDER_ERROR
} PortableRibbonStatus;

typedef struct PortableRibbonMessage {
    const char *pointer; /* Borrowed from PortableAdviceResources. */
    PortableAdvicePointerInfo source;
} PortableRibbonMessage;

typedef struct PortableRibbonChannelState {
    PortableRibbonMessage message;
    int32_t deadline;
    uint8_t dirty;
} PortableRibbonChannelState;

typedef struct PortableRibbonState {
    PortableRibbonChannelState edit_surface; /* fd_55B3_19C6/19CA/19CE */
    PortableRibbonChannelState map_yard;      /* fd_55B3_299A/299E/29A2 */
} PortableRibbonState;

typedef struct PortableRibbonEditResult {
    uint8_t applied;
    uint8_t tick_reads;
    uint8_t edit_pointer_changed;
    uint8_t map_pointer_changed;
} PortableRibbonEditResult;

typedef struct PortableRibbonRenderResult {
    uint8_t message_live;
    uint8_t expired;
    uint8_t drawn;
    uint8_t has_clip_exclusion;
    uint8_t font_id;
    uint8_t color_index;
    PortableWindowRect target_rect;
    PortableWindowRect text_rect;
    PortableAdvicePointerInfo source;
} PortableRibbonRenderResult;

void portable_ribbon_init(PortableRibbonState *state);

/* EditMessage source behavior. `message` must be NULL or an exact pointer from
 * the retained advice table owner. Nonnegative duration uses two independent
 * tick reads in source order; negative duration stores the 0x7fffffff sentinel. */
PortableRibbonStatus portable_ribbon_edit_message(
    PortableRibbonState *state, const PortableAdviceResources *advice,
    const void *message, int32_t duration, int16_t mode, int advice_enabled,
    PortableRibbonTickProvider tick, void *tick_context,
    PortableRibbonEditResult *result);

/* Resolve the live target rectangle from the registry, expire its shared
 * message with one source TickCount read, and draw the native text. A false
 * target_visible still performs expiry (yard has this source behavior). The
 * returned clip_exclusion is the exact rect passed to clip_SubExclude. */
PortableRibbonStatus portable_ribbon_render_current(
    PortableRibbonState *state, const PortableAdviceResources *advice,
    PortableRibbonTarget target, PortableWindowRegistry *registry,
    const PortableWindowRenderer *renderer, int target_visible,
    PortableRibbonTickProvider tick, void *tick_context,
    PortableRibbonRenderResult *result);

void portable_ribbon_clear_dirty(PortableRibbonState *state,
                                 PortableRibbonTarget target);
const char *portable_ribbon_status_string(PortableRibbonStatus status);

#endif
