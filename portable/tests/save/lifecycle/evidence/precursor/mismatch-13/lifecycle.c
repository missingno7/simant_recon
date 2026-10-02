#include "lifecycle.h"

#include <stdio.h>
#include <string.h>

static int valid_table(const PortableLegacySaveRecordSpec *specs,
                       size_t spec_count,
                       const PortableLegacySaveBinding *bindings,
                       size_t binding_count)
{
    size_t i;
    if (specs == NULL || bindings == NULL || spec_count == 0 || spec_count != binding_count)
        return 0;
    for (i = 0; i < spec_count; ++i) {
        uint32_t size = (uint32_t)specs[i].element_size * specs[i].element_count;
        if (size == 0 || size > UINT16_MAX || bindings[i].bytes == NULL || bindings[i].extent < size)
            return 0;
    }
    return 1;
}

static int valid_host(const PortableSaveLifecycleHost *host)
{
    return host != NULL && host->select_path != NULL && host->dirty_prompt != NULL &&
        host->confirm_overwrite != NULL && host->open_file != NULL &&
        host->read_record != NULL && host->write_record != NULL &&
        host->close_file != NULL && host->remove_file != NULL &&
        host->show_message != NULL && host->before_load != NULL &&
        host->load_stream_complete != NULL && host->refresh_after_load != NULL &&
        host->update_after_load != NULL && host->rebuild_after_load != NULL && host->stop_song != NULL;
}

static int copy_path(char *dst, size_t cap, const char *src)
{
    size_t n;
    if (src == NULL) return 0;
    n = strlen(src);
    if (n == 0 || n >= cap) return 0;
    memcpy(dst, src, n + 1);
    return 1;
}

static int select_path(const PortableSaveLifecycleHost *host,
                       const char *title, const char *verb, int16_t save,
                       char path[PORTABLE_SAVEGAME_FILENAME_CAP])
{
    memset(path, 0, PORTABLE_SAVEGAME_FILENAME_CAP);
    if (!host->select_path(host->context, title, verb, save, path,
                           PORTABLE_SAVEGAME_FILENAME_CAP))
        return 0;
    path[PORTABLE_SAVEGAME_FILENAME_CAP - 1] = '\0';
    return path[0] != '\0';
}

int16_t portable_savegame_save(PortableSaveLifecycleState *state,
                               const PortableLegacySaveRecordSpec *specs,
                               size_t spec_count,
                               const PortableLegacySaveBinding *bindings,
                               size_t binding_count,
                               const PortableSaveLifecycleHost *host,
                               int16_t use_last)
{
    char path[PORTABLE_SAVEGAME_FILENAME_CAP];
    char prompt[PORTABLE_SAVEGAME_FILENAME_CAP + 16];
    size_t i;
    int32_t fd;
    char saved_text[PORTABLE_SAVEGAME_FILENAME_CAP + 24];

    if (state == NULL || !valid_table(specs, spec_count, bindings, binding_count) || !valid_host(host))
        return PORTABLE_SAVE_LIFECYCLE_INVALID_ARGUMENT;

    if (use_last != 0 && state->last_filename[0] != '\0') {
        if (!copy_path(path, sizeof(path), state->last_filename)) return PORTABLE_SAVE_LIFECYCLE_BAD_PATH;
    } else {
select_again:
        if (!select_path(host, "Save Game", "SAVE", 1, path))
            return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
        if (!copy_path(state->last_filename, sizeof(state->last_filename), path))
            return PORTABLE_SAVE_LIFECYCLE_BAD_PATH;
    }

    fd = host->open_file(host->context, path, PORTABLE_SAVE_OPEN_READ_WRITE_EXISTING);
    if (fd > 0) {
        if (host->confirm_overwrite == NULL) return PORTABLE_SAVE_LIFECYCLE_INVALID_ARGUMENT;
        (void)snprintf(prompt, sizeof(prompt), "OVERWRITE\n%s", path);
        if (host->confirm_overwrite(host->context, prompt) != 0) {
            (void)host->close_file(host->context, fd);
            goto select_again;
        }
    } else {
        fd = host->open_file(host->context, path, PORTABLE_SAVE_OPEN_CREATE_TRUNCATE);
        if (fd <= 0) {
            host->show_message(host->context, PORTABLE_SAVE_MESSAGE_OPEN_ERROR, NULL);
            state->last_filename[0] = '\0';
            return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
        }
    }

    for (i = 0; i < spec_count; ++i) {
        uint16_t count = (uint16_t)((uint32_t)specs[i].element_size * specs[i].element_count);
        if (host->write_record(host->context, fd, bindings[i].bytes, count) == -1) {
            state->last_filename[0] = '\0';
            host->show_message(host->context, PORTABLE_SAVE_MESSAGE_WRITE_ERROR, NULL);
            (void)host->close_file(host->context, fd);
            (void)host->remove_file(host->context, path);
            return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
        }
    }

    state->dirty = 0;
    (void)snprintf(saved_text, sizeof(saved_text), "%s\nSaved correctly", path);
    host->show_message(host->context, PORTABLE_SAVE_MESSAGE_SAVED, saved_text);
    (void)copy_path(state->last_filename, sizeof(state->last_filename), path);
    (void)host->close_file(host->context, fd);
    return PORTABLE_SAVE_LIFECYCLE_OK;
}

int16_t portable_savegame_load(PortableSaveLifecycleState *state,
                               const PortableLegacySaveRecordSpec *specs,
                               size_t spec_count,
                               PortableLegacySaveBinding *bindings,
                               size_t binding_count,
                               const PortableSaveLifecycleHost *host,
                               int16_t stop_song_when_game_inactive)
{
    char path[PORTABLE_SAVEGAME_FILENAME_CAP];
    size_t i;
    int32_t fd;
    int16_t prompt_result;

    if (state == NULL || !valid_table(specs, spec_count, bindings, binding_count) || !valid_host(host))
        return PORTABLE_SAVE_LIFECYCLE_INVALID_ARGUMENT;
    if (state->dirty != 0) {
        do {
            prompt_result = host->dirty_prompt(host->context);
            if (prompt_result == 2) return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
        } while (prompt_result == 1 &&
                 portable_savegame_save(state, specs, spec_count, bindings, binding_count,
                                        host, 0) == 0);
    }

    if (!select_path(host, "Load Game", "LOAD", 0, path))
        return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
    if (!copy_path(state->last_filename, sizeof(state->last_filename), path))
        return PORTABLE_SAVE_LIFECYCLE_BAD_PATH;
    state->dirty = 0;

    fd = host->open_file(host->context, path, PORTABLE_SAVE_OPEN_READ_ONLY);
    if (fd <= 0) {
        host->show_message(host->context, PORTABLE_SAVE_MESSAGE_OPEN_ERROR, NULL);
        return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
    }
    host->before_load(host->context, state);
    for (i = 0; i < spec_count; ++i) {
        uint16_t count = (uint16_t)((uint32_t)specs[i].element_size * specs[i].element_count);
        if (host->read_record(host->context, fd, bindings[i].bytes, count) != count) {
            host->show_message(host->context, PORTABLE_SAVE_MESSAGE_READ_ERROR,
                               "  Read error  \ngame not loaded");
            state->load_mode = -1;
            (void)host->close_file(host->context, fd);
            return PORTABLE_SAVE_LIFECYCLE_CANCELLED;
        }
    }

    host->load_stream_complete(host->context, 0, -2, 1);
    (void)host->close_file(host->context, fd);
    host->refresh_after_load(host->context);
    host->update_after_load(host->context, 1);
    host->rebuild_after_load(host->context);
    if (stop_song_when_game_inactive) host->stop_song(host->context);
    return PORTABLE_SAVE_LIFECYCLE_OK;
}
