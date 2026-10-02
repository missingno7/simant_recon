#include "menu_modal.h"

#include "../host.h"
#include "../../ui_model/input/input.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

enum { MENU_POLL_WAIT_MS = 8, MENU_PLAN_COMMANDS = 64,
       MENU_TEXT_STORAGE = 4001 };

typedef struct SavedPopup {
    PortableRect rect;
    uint8_t *pixels;
    size_t width, height;
} SavedPopup;

static PortableRect intersect(PortableRect a, PortableRect b)
{
    PortableRect r = {a.left > b.left ? a.left : b.left,
                      a.top > b.top ? a.top : b.top,
                      a.right < b.right ? a.right : b.right,
                      a.bottom < b.bottom ? a.bottom : b.bottom};
    if (r.right < r.left) r.right = r.left;
    if (r.bottom < r.top) r.bottom = r.top;
    return r;
}

static int framebuffer_valid(const PortableFramebuffer *fb, size_t *bytes)
{
    if (fb == NULL || bytes == NULL || fb->pixels == NULL || fb->width <= 0 ||
        fb->height <= 0 || fb->stride < (size_t)fb->width ||
        (size_t)fb->height > SIZE_MAX / fb->stride)
        return 0;
    *bytes = fb->stride * (size_t)fb->height;
    return 1;
}

static int save_popup(PortableFramebuffer *fb,
                      const PortableMenuDropdownRect *popup,
                      SavedPopup *saved)
{
    PortableRect screen = {0, 0, fb->width, fb->height};
    PortableRect requested = {popup->left, popup->top,
                              popup->right, popup->bottom};
    size_t row, width, height;
    saved->rect = intersect(intersect(requested, fb->clip), screen);
    width = (size_t)(saved->rect.right - saved->rect.left);
    height = (size_t)(saved->rect.bottom - saved->rect.top);
    if (width != 0 && height > SIZE_MAX / width) return 0;
    saved->pixels = malloc(width * height);
    if (saved->pixels == NULL && width * height != 0) return 0;
    saved->width = width;
    saved->height = height;
    for (row = 0; row < height; ++row)
        memcpy(saved->pixels + row * width,
               fb->pixels + ((size_t)saved->rect.top + row) * fb->stride +
                   (size_t)saved->rect.left,
               width);
    return 1;
}

static void restore_popup(PortableFramebuffer *fb, const SavedPopup *saved)
{
    size_t row;
    for (row = 0; row < saved->height; ++row)
        memcpy(fb->pixels + ((size_t)saved->rect.top + row) * fb->stride +
                   (size_t)saved->rect.left,
               saved->pixels + row * saved->width, saved->width);
}

static PortableMenuModalStatus draw_plan(
    const PortableMenuModalRequest *request,
    const PortableMenuInteraction *interaction, int old_item, int new_item,
    int initial)
{
    PortableMenuDropdownDrawCommand commands[MENU_PLAN_COMMANDS];
    uint8_t text[MENU_TEXT_STORAGE];
    int16_t colors[4];
    size_t count = 0, used = 0;
    PortableMenuDropdownRenderStatus status;
    portable_menu_dropdown_source_pen_colors(request->source_g5fea,
        request->source_g5fec, request->source_g5fee, colors);
    if (initial) {
        status = portable_menu_dropdown_build_open_plan(interaction, -1,
            request->source_g5fea, request->source_g5fec, request->source_g5fee,
            colors, commands, MENU_PLAN_COMMANDS, text, sizeof(text),
            &count, &used);
    } else {
        status = portable_menu_dropdown_build_highlight_plan(interaction,
            old_item, new_item, request->source_g5fea, request->source_g5fec,
            request->source_g5fee, colors, commands, MENU_PLAN_COMMANDS,
            text, sizeof(text), &count, &used);
    }
    (void)used;
    if (status != PORTABLE_DROPDOWN_RENDER_OK)
        return PORTABLE_MENU_MODAL_RENDER_ERROR;
    if (count != 0 && portable_menu_dropdown_rasterize(request->framebuffer,
            request->font, interaction->saved_rect, commands, count) !=
            PORTABLE_DROPDOWN_RENDER_OK)
        return PORTABLE_MENU_MODAL_RENDER_ERROR;
    return PORTABLE_MENU_MODAL_COMMAND;
}

static int apply_step(PortableMenuInteraction *interaction,
                      const PortableMenuInput *input,
                      const PortableMenuModalRequest *request,
                      Host *host,
                      int *old_item, int *completed)
{
    PortableMenuInteractionStatus status =
        portable_menu_interaction_step(interaction, input);
    if (status == PORTABLE_MENU_INTERACTION_BAD_ARGUMENT) return 0;
    if (interaction->current_item != *old_item) {
        int before = *old_item;
        *old_item = interaction->current_item;
        if (draw_plan(request, interaction, before, *old_item, 0) !=
            PORTABLE_MENU_MODAL_COMMAND)
            return 0;
    }
    if (interaction->warped_pointer) {
        if (!host_warp_pointer(host, interaction->warp_x,
                               interaction->warp_y))
            return 0;
        interaction->warped_pointer = 0;
    }
    *completed = status == PORTABLE_MENU_INTERACTION_COMPLETE ||
                 interaction->completed;
    return 1;
}

static void export_result(const PortableMenuInteraction *interaction,
                          PortableMenuModalResult *result)
{
    size_t i;
    result->command_id = interaction->command_id;
    result->selection = interaction->selection;
    result->selection_written = interaction->selection_written;
    result->returned = interaction->returned;
    result->flushed_key = interaction->flushed_key;
    result->forwarded_event = interaction->forwarded_event;
    for (i = 0; i < 5; ++i)
        result->forwarded_event_words[i] = interaction->forwarded_event_words[i];
}

PortableMenuModalStatus portable_menu_modal_run(
    Host *host, const PortableMenuModalRequest *request,
    PortableMenuModalResult *result)
{
    PortableMenuInteraction interaction;
    PortableMenuInteractionStatus interaction_status;
    PortableMenuModalStatus final_status = PORTABLE_MENU_MODAL_BAD_ARGUMENT;
    PortableMenuInput input;
    PortableFramebuffer *fb;
    SavedPopup saved = {{0, 0, 0, 0}, NULL, 0, 0};
    size_t framebuffer_bytes;
    int button_down, pointer_x, pointer_y, old_item = -1, completed = 0;
    int opened = 0, restore_ok = 1, input_state_ok = 1, poll_status;
    if (host == NULL || request == NULL || result == NULL ||
        request->menu == NULL || request->layout == NULL ||
        request->framebuffer == NULL || request->font == NULL ||
        request->host_palette == NULL || request->screen_width <= 0 ||
        request->screen_height <= 0 || request->line_height <= 0 ||
        request->char_width <= 0 || request->menu_index >= 16 ||
        !framebuffer_valid(request->framebuffer, &framebuffer_bytes) ||
        request->screen_width > request->framebuffer->width ||
        request->screen_height > request->framebuffer->height ||
        request->font->glyph_width != 8 ||
        (request->font->glyph_height != 8 && request->font->glyph_height != 14) ||
        request->font->glyph_rows == NULL ||
        request->font->glyph_rows_size < (size_t)256 * request->font->glyph_height)
        return PORTABLE_MENU_MODAL_BAD_ARGUMENT;
    (void)framebuffer_bytes;
    memset(result, 0, sizeof(*result));
    memset(&interaction, 0, sizeof(interaction));
    interaction_status = portable_menu_interaction_init_from_bar(&interaction,
        request->menu, request->layout, request->menu_index,
        request->screen_width, request->screen_height, request->line_height,
        request->char_width, request->initial_selection);
    if (interaction_status == PORTABLE_MENU_INTERACTION_NO_ITEMS) {
        export_result(&interaction, result);
        return PORTABLE_MENU_MODAL_RETURNED;
    }
    if (interaction_status != PORTABLE_MENU_INTERACTION_RUNNING) {
        return PORTABLE_MENU_MODAL_INTERACTION_ERROR;
    }
    fb = request->framebuffer;
    if (!save_popup(fb, &interaction.saved_rect, &saved))
        return PORTABLE_MENU_MODAL_RENDER_ERROR;
    opened = 1;
    final_status = draw_plan(request, &interaction, -1, -1, 1);
    if (final_status != PORTABLE_MENU_MODAL_COMMAND) goto cleanup;
    if (!host_present(host, fb->pixels, fb->stride, request->host_palette)) {
        final_status = PORTABLE_MENU_MODAL_HOST_ERROR;
        goto cleanup;
    }
    button_down = request->initial_left_button_down != 0;
    pointer_x = request->initial_x;
    pointer_y = request->initial_y;
    if (button_down) {
        memset(&input, 0, sizeof(input));
        input.kind = PORTABLE_MENU_INPUT_POINTER_POLL;
        input.x = pointer_x;
        input.y = pointer_y;
        input.button_down = 1;
        if (!apply_step(&interaction, &input, request, host, &old_item,
                        &completed)) {
            final_status = PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT;
            goto cleanup;
        }
        if (!host_present(host, fb->pixels, fb->stride, request->host_palette)) {
            final_status = PORTABLE_MENU_MODAL_HOST_ERROR;
            goto cleanup;
        }
    }
    while (!completed) {
        HostEvent event;
        if (request->poll_source_event != NULL) {
            memset(&input, 0, sizeof(input));
            poll_status = request->poll_source_event(
                request->source_event_context, &input);
            if (poll_status < 0) {
                final_status = PORTABLE_MENU_MODAL_HOST_ERROR;
                goto cleanup;
            }
            if (poll_status > 0) {
                if (input.kind != PORTABLE_MENU_INPUT_WINDOW_EVENT) {
                    final_status = PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT;
                    goto cleanup;
                }
                if (!apply_step(&interaction, &input, request, host, &old_item,
                                &completed)) {
                    final_status = PORTABLE_MENU_MODAL_INTERACTION_ERROR;
                    goto cleanup;
                }
                if (interaction.forwarded_event) {
                    final_status = PORTABLE_MENU_MODAL_FORWARDED_SOURCE_EVENT;
                    goto cleanup;
                }
                continue;
            }
        }
        poll_status = host_poll_event(host, &event);
        if (poll_status < 0) {
            final_status = PORTABLE_MENU_MODAL_HOST_ERROR;
            goto cleanup;
        }
        if (poll_status == 0) {
            memset(&input, 0, sizeof(input));
            input.kind = PORTABLE_MENU_INPUT_POINTER_POLL;
            input.x = pointer_x;
            input.y = pointer_y;
            input.button_down = button_down;
            if (!apply_step(&interaction, &input, request, host, &old_item,
                            &completed)) {
                final_status = PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT;
                goto cleanup;
            }
            if (!host_present(host, fb->pixels, fb->stride,
                              request->host_palette)) {
                final_status = PORTABLE_MENU_MODAL_HOST_ERROR;
                goto cleanup;
            }
            if (!completed) host_wait_ms(MENU_POLL_WAIT_MS);
            continue;
        }
        if (event.kind == HOST_EVENT_QUIT) {
            if (request->quit_flag != NULL) *request->quit_flag = 1;
            final_status = PORTABLE_MENU_MODAL_QUIT;
            goto cleanup;
        }
        if (event.kind == HOST_EVENT_KEY_DOWN) {
            int16_t logical_key;
            PortableInputStatus key_status =
                portable_input_decode_bios_key(event.key, &logical_key);
            if (key_status == PORTABLE_INPUT_NO_KEY ||
                key_status == PORTABLE_INPUT_MODIFIER_ONLY)
                continue;
            if (key_status != PORTABLE_INPUT_OK) {
                final_status = PORTABLE_MENU_MODAL_INTERACTION_ERROR;
                goto cleanup;
            }
            memset(&input, 0, sizeof(input));
            input.kind = PORTABLE_MENU_INPUT_KEY;
            input.key = (uint16_t)logical_key;
            if (!apply_step(&interaction, &input, request, host, &old_item,
                            &completed)) {
                final_status = PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT;
                goto cleanup;
            }
        } else if (event.kind == HOST_EVENT_MOUSE_MOVE) {
            pointer_x = event.x;
            pointer_y = event.y;
        } else if (event.kind == HOST_EVENT_MOUSE_DOWN ||
                   event.kind == HOST_EVENT_MOUSE_UP) {
            int title;
            if (event.button != 1) {
                final_status = PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT;
                goto cleanup;
            }
            pointer_x = event.x;
            pointer_y = event.y;
            if (event.kind == HOST_EVENT_MOUSE_DOWN) {
                title = portable_menu_title_hit(request->menu, request->layout,
                                                pointer_x, pointer_y);
                if (title >= 0 && (size_t)title != request->menu_index) {
                    result->physical_title_index_valid = 1;
                    result->physical_title_index = (uint8_t)title;
                    result->physical_title_x = event.x;
                    result->physical_title_y = event.y;
                    final_status = PORTABLE_MENU_MODAL_PHYSICAL_TITLE_EVENT;
                    goto cleanup;
                }
                button_down = 1;
            } else {
                button_down = 0;
            }
        } else {
            continue;
        }
        memset(&input, 0, sizeof(input));
        input.kind = PORTABLE_MENU_INPUT_POINTER_POLL;
        input.x = pointer_x;
        input.y = pointer_y;
        input.button_down = button_down;
        if (!apply_step(&interaction, &input, request, host, &old_item,
                        &completed)) {
            final_status = interaction.warped_pointer
                ? PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT
                : PORTABLE_MENU_MODAL_INTERACTION_ERROR;
            goto cleanup;
        }
        if (!host_present(host, fb->pixels, fb->stride, request->host_palette)) {
            final_status = PORTABLE_MENU_MODAL_HOST_ERROR;
            goto cleanup;
        }
    }
    export_result(&interaction, result);
    final_status = interaction.forwarded_event
        ? PORTABLE_MENU_MODAL_FORWARDED_SOURCE_EVENT
        : (interaction.command_dispatched ? PORTABLE_MENU_MODAL_COMMAND
                                          : PORTABLE_MENU_MODAL_RETURNED);

cleanup:
    if (opened) {
        restore_popup(fb, &saved);
        free(saved.pixels);
        if (!host_present(host, fb->pixels, fb->stride, request->host_palette))
            restore_ok = 0;
    }
    if (final_status == PORTABLE_MENU_MODAL_COMMAND ||
        final_status == PORTABLE_MENU_MODAL_RETURNED ||
        final_status == PORTABLE_MENU_MODAL_FORWARDED_SOURCE_EVENT)
        export_result(&interaction, result);
    {
        HostInputState state;
        if (host_get_input_state(host, &state)) {
            result->input_state_valid = 1;
            result->pointer_x = state.x;
            result->pointer_y = state.y;
            result->left_button_down = state.left_button_down;
            result->observed_dos_modifiers = state.dos_modifiers;
        } else {
            input_state_ok = 0;
        }
    }
    if (!restore_ok) return PORTABLE_MENU_MODAL_RESTORE_ERROR;
    if (!input_state_ok && final_status < PORTABLE_MENU_MODAL_BAD_ARGUMENT)
        return PORTABLE_MENU_MODAL_HOST_ERROR;
    return final_status;
}

const char *portable_menu_modal_status_string(PortableMenuModalStatus status)
{
    switch (status) {
    case PORTABLE_MENU_MODAL_COMMAND: return "command dispatched";
    case PORTABLE_MENU_MODAL_RETURNED: return "returned without command";
    case PORTABLE_MENU_MODAL_FORWARDED_SOURCE_EVENT: return "source event forwarded";
    case PORTABLE_MENU_MODAL_PHYSICAL_TITLE_EVENT: return "physical title event returned";
    case PORTABLE_MENU_MODAL_QUIT: return "host quit";
    case PORTABLE_MENU_MODAL_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_MENU_MODAL_INTERACTION_ERROR: return "menu interaction failed";
    case PORTABLE_MENU_MODAL_RENDER_ERROR: return "menu rendering failed";
    case PORTABLE_MENU_MODAL_HOST_ERROR: return "host service failed";
    case PORTABLE_MENU_MODAL_UNSUPPORTED_PHYSICAL_EVENT:
        return "physical event requires an unsupported host service";
    case PORTABLE_MENU_MODAL_RESTORE_ERROR: return "popup restoration failed";
    }
    return "unknown menu modal status";
}
