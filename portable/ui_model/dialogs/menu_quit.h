#ifndef SIMANT_PORTABLE_UI_MODEL_DIALOGS_MENU_QUIT_H
#define SIMANT_PORTABLE_UI_MODEL_DIALOGS_MENU_QUIT_H

#include <stddef.h>
#include <stdint.h>

typedef struct PortableMenuQuitRect {
    int16_t left, top, right, bottom;
} PortableMenuQuitRect;

typedef enum PortableMenuQuitChoice {
    PORTABLE_MENU_QUIT_DISCARD = 0,
    PORTABLE_MENU_QUIT_SAVE = 1,
    PORTABLE_MENU_QUIT_CANCEL = 2
} PortableMenuQuitChoice;

typedef enum PortableMenuQuitStatus {
    PORTABLE_MENU_QUIT_EXIT_REQUESTED = 0,
    PORTABLE_MENU_QUIT_CANCELLED,
    PORTABLE_MENU_QUIT_BAD_ARGUMENT,
    PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE,
    PORTABLE_MENU_QUIT_HOST_REJECTED,
    PORTABLE_MENU_QUIT_INPUT_PENDING
} PortableMenuQuitStatus;

typedef struct PortableMenuQuitHost {
    void *context;
    int (*open_window)(void *, int16_t window);
    int (*load_resource)(void *, int16_t object, int16_t kind, int16_t type,
                         uintptr_t *handle);
    int (*lock_resource)(void *, uintptr_t handle, const char **text,
                         size_t *length);
    int (*set_font)(void *, int16_t font);
    int (*get_object_rect)(void *, int16_t object, PortableMenuQuitRect *rect);
    int (*decorate_rect)(void *, int16_t a, int16_t b, int16_t c);
    int (*frame_rect)(void *, const PortableMenuQuitRect *rect, int16_t width);
    int (*set_color_from_object)(void *, int16_t object);
    int (*print_text)(void *, int16_t first, const char *text,
                      const PortableMenuQuitRect *rect);
    int (*key_ready)(void *, int *ready);
    int (*read_key)(void *, int16_t *key);
    int (*get_event)(void *, int *available, int16_t *code);
    int (*unlock_resource)(void *, uintptr_t handle);
    int (*release_resource)(void *, uintptr_t handle);
    int (*close_window)(void *, int16_t window);
    /* Real SaveGame I/O belongs to the host. Return its actual success flag. */
    int (*save_game)(void *, int16_t use_last, int *saved);
    /* Displays the source-authored terminal notice and performs process exit. */
    int (*exit_notice)(void *, const char *message, int16_t flag,
                       int16_t exit_code);
} PortableMenuQuitHost;

typedef struct PortableMenuQuitInput {
    int16_t dirty_word;
    int16_t screen_width_metric; /* g_3DB2; 0x140 selects font 2, else 4. */
    uint8_t frame_enabled;       /* g_5A97 & 1. */
    uint32_t max_input_polls;    /* Safety bound; live hosts block in poll calls. */
} PortableMenuQuitInput;

/* Returns a recognized source choice after executing the complete prompt
 * resource, font, draw, polling, and resource-cleanup sequence. */
PortableMenuQuitStatus portable_menu_quit_prompt(
    const PortableMenuQuitHost *host, int16_t which,
    const PortableMenuQuitInput *input, PortableMenuQuitChoice *choice);

/* Models S15 MenuQuit. A cancellation returns to the caller. All other paths
 * request the exact source thank-you notice and terminal exit. dirty_word is
 * borrowed source state and is never cleared by MenuQuit. */
PortableMenuQuitStatus portable_menu_quit_run(
    const PortableMenuQuitHost *host, const PortableMenuQuitInput *input);

#endif
