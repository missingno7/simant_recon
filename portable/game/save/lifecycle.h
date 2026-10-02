#ifndef SIMANT_PORTABLE_SAVE_LIFECYCLE_H
#define SIMANT_PORTABLE_SAVE_LIFECYCLE_H

#include "legacy_codec.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PORTABLE_SAVEGAME_FILENAME_CAP 100u

typedef enum PortableSaveOpenMode {
    PORTABLE_SAVE_OPEN_READ_ONLY = 0,
    PORTABLE_SAVE_OPEN_READ_WRITE_EXISTING = 1,
    PORTABLE_SAVE_OPEN_CREATE_TRUNCATE = 2
} PortableSaveOpenMode;

typedef enum PortableSaveMessage {
    PORTABLE_SAVE_MESSAGE_OPEN_ERROR = 0,
    PORTABLE_SAVE_MESSAGE_READ_ERROR = 1,
    PORTABLE_SAVE_MESSAGE_WRITE_ERROR = 2,
    PORTABLE_SAVE_MESSAGE_SAVED = 3
} PortableSaveMessage;

typedef struct PortableSaveLifecycleState {
    char last_filename[PORTABLE_SAVEGAME_FILENAME_CAP];
    int16_t dirty;
    int16_t load_mode;
    /* Serialized SaveRec backing: fd_3D57_07A8[7], including [1] == fd_3D57_07AA. */
    int16_t fd_3D57_07A8[7];
} PortableSaveLifecycleState;

/*
 * All side effects are explicit typed host boundaries. `context` must refer to
 * the same owner that contains `state`; callbacks which observe/mutate fields
 * outside the SaveRec rows must do so through that owner, not a stale copy.
 * Reads and writes are per SaveRec row, matching the original call granularity. A read callback may
 * modify a prefix of buffer even when it reports a short/error result; those
 * bytes remain mutated, matching the DOS destination semantics.
 */
typedef struct PortableSaveLifecycleHost {
    void *context;
    int16_t (*select_path)(void *context, const char *title, const char *verb,
                           int16_t save, char *out_path, size_t capacity);
    int16_t (*dirty_prompt)(void *context);
    int16_t (*confirm_overwrite)(void *context, const char *prompt_text);
    int32_t (*open_file)(void *context, const char *path, PortableSaveOpenMode mode);
    int32_t (*read_record)(void *context, int32_t fd, uint8_t *buffer, uint16_t count);
    int32_t (*write_record)(void *context, int32_t fd, const uint8_t *buffer, uint16_t count);
    int32_t (*close_file)(void *context, int32_t fd);
    int32_t (*remove_file)(void *context, const char *path);
    void (*show_message)(void *context, PortableSaveMessage message, const char *text);
    void (*before_load)(void *context, PortableSaveLifecycleState *state);
    void (*load_stream_complete)(void *context, int32_t start, int32_t end, int16_t mode);
    void (*refresh_after_load)(void *context);
    void (*update_after_load)(void *context, int16_t mode);
    void (*rebuild_after_load)(void *context);
    int16_t (*should_stop_song)(void *context, const PortableSaveLifecycleState *state);
    void (*stop_song)(void *context);
} PortableSaveLifecycleHost;

typedef enum PortableSaveLifecycleStatus {
    /* Valid calls return the original DOS convention: success=1, failure=0. */
    PORTABLE_SAVE_LIFECYCLE_OK = 1,
    PORTABLE_SAVE_LIFECYCLE_CANCELLED = 0,
    PORTABLE_SAVE_LIFECYCLE_INVALID_ARGUMENT = -1,
    PORTABLE_SAVE_LIFECYCLE_BAD_PATH = -2,
    PORTABLE_SAVE_LIFECYCLE_BAD_SPEC = -3
} PortableSaveLifecycleStatus;

int16_t portable_savegame_save(PortableSaveLifecycleState *state,
                               const PortableLegacySaveRecordSpec *specs,
                               size_t spec_count,
                               const PortableLegacySaveBinding *bindings,
                               size_t binding_count,
                               const PortableSaveLifecycleHost *host,
                               int16_t use_last);

int16_t portable_savegame_load(PortableSaveLifecycleState *state,
                               const PortableLegacySaveRecordSpec *specs,
                               size_t spec_count,
                               PortableLegacySaveBinding *bindings,
                               size_t binding_count,
                               const PortableSaveLifecycleHost *host);

#ifdef __cplusplus
}
#endif

#endif
