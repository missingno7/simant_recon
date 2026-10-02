#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_BALLOON_QUEUE_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_BALLOON_QUEUE_H

#include <stddef.h>
#include <stdint.h>

#include "../balloons/balloons.h"

enum { PORTABLE_BALLOON_QUEUE_CAPACITY = 6 };

typedef enum PortableBalloonTextTable {
    PORTABLE_BALLOON_TEXT_FIGHT = 0,
    PORTABLE_BALLOON_TEXT_FIGHT_ALT,
    PORTABLE_BALLOON_TEXT_EGG,
    PORTABLE_BALLOON_TEXT_QUEEN,
    PORTABLE_BALLOON_TEXT_REST,
    PORTABLE_BALLOON_TEXT_CALLER
} PortableBalloonTextTable;

typedef struct PortableBalloonMessageId {
    uint16_t table;
    uint16_t index;
    uint8_t is_null;
} PortableBalloonMessageId;

typedef struct PortableBalloonQueuedMessage {
    PortableBalloonMessageId id;
    const char *borrowed_text;
    int16_t x_pixels;
    int16_t y_pixels;
    int16_t plane;
    int16_t style;
} PortableBalloonQueuedMessage;

typedef struct PortableBalloonQueue {
    PortableBalloonViewport viewport;
    int16_t pixel_width;
    int16_t pixel_height;
    uint16_t count;
    PortableBalloonQueuedMessage entries[PORTABLE_BALLOON_QUEUE_CAPACITY];
} PortableBalloonQueue;

typedef enum PortableBalloonRandomFamily {
    PORTABLE_BALLOON_SRAND2 = 0,
    PORTABLE_BALLOON_SRAND4,
    PORTABLE_BALLOON_SRAND32,
    PORTABLE_BALLOON_SRAND64
} PortableBalloonRandomFamily;

/* A table resolver must return true for a valid (including NULL-terminated)
 * source table slot. The returned text is borrowed and remains owned by the
 * resource provider. Unknown tables/indices fail closed. */
typedef int (*PortableBalloonTextLookup)(void *context,
                                         const PortableBalloonMessageId *id,
                                         const char **borrowed_text);

/* Tick and random calls are explicit source-service boundaries. Each callback
 * invocation represents one source call; callers must provide results in
 * exact call order. */
typedef uint32_t (*PortableBalloonTick)(void *context);
typedef int16_t (*PortableBalloonRandom)(void *context,
                                         PortableBalloonRandomFamily family);

typedef struct PortableBalloonServices {
    void *context;
    PortableBalloonTick tick_count;
    PortableBalloonRandom random;
    PortableBalloonTextLookup lookup_text;
} PortableBalloonServices;

typedef struct PortableBalloonCueTimers {
    int32_t fight_first;
    int32_t fight_second;
    int32_t egg;
    int32_t queen;
    int32_t rest;
} PortableBalloonCueTimers;

typedef struct PortableBalloonCueMessages {
    int16_t fight_first_enabled;
    int16_t fight_second_enabled;
    int16_t egg_enabled;
    int16_t queen_enabled;
    int16_t rest_enabled;
    uint16_t fight_first_index;
    uint16_t fight_second_index;
    uint16_t egg_index;
    uint16_t queen_index;
    uint16_t rest_index;
} PortableBalloonCueMessages;

typedef struct PortableBalloonFrame {
    PortableBalloonCueState cue[PORTABLE_BALLOON_CUE_COUNT];
    PortableBalloonCueTimers timers;
    PortableBalloonCueMessages messages;
    PortableBalloonQueue queue;
    int16_t updates_enabled;
    int16_t sprite_state;
    int16_t cue_pause;
} PortableBalloonFrame;

typedef enum PortableBalloonQueueStatus {
    PORTABLE_BALLOON_QUEUE_OK = 0,
    PORTABLE_BALLOON_QUEUE_BAD_ARGUMENT,
    PORTABLE_BALLOON_QUEUE_MISSING_SERVICE,
    PORTABLE_BALLOON_QUEUE_MISSING_TEXT
} PortableBalloonQueueStatus;

void portable_balloon_queue_init(PortableBalloonQueue *queue,
                                 const PortableBalloonViewport *viewport,
                                 int16_t pixel_width, int16_t pixel_height);

/* Source AddMsgBalloon. The message reference is retained as a table/index
 * identity, while `borrowed_text` is a non-owning view for later presentation. */
PortableBalloonQueueStatus portable_balloon_queue_add(
    PortableBalloonQueue *queue, int16_t x, int16_t y, int16_t plane,
    int16_t style, PortableBalloonMessageId id, const char *borrowed_text);

/* Source DrawCurBalloons state/selection order, including its AddMsgBalloon
 * submissions. No label is fabricated: source table reads use lookup_text. */
PortableBalloonQueueStatus portable_balloon_draw_current(
    PortableBalloonFrame *frame, const PortableBalloonServices *services);

#endif
