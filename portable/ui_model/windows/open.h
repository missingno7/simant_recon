#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_OPEN_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_OPEN_H

#include "registry.h"

enum {
    PORTABLE_WINDOW_OPEN_NONE = 0x8000,
    PORTABLE_WINDOW_OPEN_MAX_EVENTS = 8
};

typedef enum PortableWindowOpenStatus {
    PORTABLE_WINDOW_OPEN_OK = 0,
    PORTABLE_WINDOW_OPEN_BAD_ARGUMENT,
    PORTABLE_WINDOW_OPEN_INVALID_STATE,
    PORTABLE_WINDOW_OPEN_NOT_LOADED,
    PORTABLE_WINDOW_OPEN_REGISTRY_ERROR,
    PORTABLE_WINDOW_OPEN_UNSUPPORTED_GEOMETRY,
    PORTABLE_WINDOW_OPEN_STACK_FULL,
    PORTABLE_WINDOW_OPEN_OUT_OF_MEMORY
} PortableWindowOpenStatus;

typedef enum PortableWindowOpenEventKind {
    PORTABLE_WINDOW_OPEN_RECALCULATE = 1,
    PORTABLE_WINDOW_OPEN_SAVE_ORIGIN,
    PORTABLE_WINDOW_OPEN_MOVE_ORIGIN,
    PORTABLE_WINDOW_OPEN_RECALCULATE_AFTER_MOVE,
    PORTABLE_WINDOW_OPEN_FRONT_CHANGED,
    PORTABLE_WINDOW_OPEN_FLAG_SET,
    PORTABLE_WINDOW_OPEN_DRAW_REQUESTED,
    PORTABLE_WINDOW_OPEN_FLUSH_EVENTS,
    PORTABLE_WINDOW_OPEN_FLAG_CLEARED,
    PORTABLE_WINDOW_OPEN_RESTORE_ORIGIN,
    PORTABLE_WINDOW_OPEN_FRONT_RESTORED,
    PORTABLE_WINDOW_OPEN_ERASE_REQUESTED
} PortableWindowOpenEventKind;

typedef struct PortableWindowOpenEvent {
    PortableWindowOpenEventKind kind;
    int16_t window_id;
} PortableWindowOpenEvent;

typedef struct PortableWindowOpenScene {
    PortableWindowState windows[PORTABLE_WINDOW_REGISTRY_SLOTS];
    int16_t order[PORTABLE_WINDOW_REGISTRY_SLOTS]; /* front to back */
    uint16_t open_count;
    int16_t front_window_id;
    uint8_t initialized;
} PortableWindowOpenScene;

typedef struct PortableWindowOpenResult {
    PortableWindowRect frame_before_move;
    PortableWindowRect frame_after;
    int16_t move_dx;
    int16_t move_dy;
    int16_t registry_status;
    uint8_t already_front;
    uint8_t moved;
    uint8_t opened;
    size_t event_count;
    PortableWindowOpenEvent events[PORTABLE_WINDOW_OPEN_MAX_EVENTS];
} PortableWindowOpenResult;

/* Initialize from the caller's actual front-to-back list. This only copies
 * loaded registry state; it never guesses or lazily loads an absent window. */
PortableWindowOpenStatus portable_window_open_scene_init(
    const PortableWindowRegistry *registry,
    const int16_t *open_order, size_t open_count,
    PortableWindowOpenScene *scene);

/* Source win_Open: requires four explicit arguments because the original
 * routine reads all four vararg slots before recalculation. */
PortableWindowOpenStatus portable_window_open_apply(
    PortableWindowRegistry *registry,
    PortableWindowOpenScene *scene,
    int16_t window_id,
    const int16_t window_args[4],
    int16_t screen_width, int16_t screen_height,
    const PortableWindowRect *menu_rect,
    PortableWindowOpenResult *result);

/* Source win_Close: clear open state and restore a movable window's saved
 * object-zero origin. Closing does not recalculate the object rectangles. */
PortableWindowOpenStatus portable_window_close_apply(
    PortableWindowRegistry *registry,
    PortableWindowOpenScene *scene,
    int16_t window_id,
    PortableWindowOpenResult *result);

const char *portable_window_open_status_string(PortableWindowOpenStatus status);

#endif
