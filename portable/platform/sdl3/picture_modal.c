#include "picture_modal.h"
#include "../../ui_model/input/input.h"

#include <stdlib.h>
#include <string.h>

enum { SOURCE_DIALOG_TICKS = 15 * 0x12, POLL_WAIT_MS = 8 };

/* The source's INT 08h tick is nominally about 55 ms. This host-time mapping
 * preserves the intended 15-second dialog timeout without claiming exact PIT
 * phase equivalence on the host. */
#define SOURCE_DIALOG_TIMEOUT_NS UINT64_C(14850000000)

static int framebuffer_byte_count(const PortableFramebuffer *framebuffer,
                                  size_t *byte_count)
{
    if (framebuffer == NULL || byte_count == NULL || framebuffer->pixels == NULL ||
        framebuffer->width != HOST_LOGICAL_WIDTH ||
        framebuffer->height != HOST_LOGICAL_HEIGHT ||
        framebuffer->stride < (size_t)framebuffer->width ||
        framebuffer->stride > SIZE_MAX / (size_t)framebuffer->height)
        return 0;
    *byte_count = framebuffer->stride * (size_t)framebuffer->height;
    return 1;
}

static int point_inside_dialog(const PortablePictureDialog *dialog,
                               const HostEvent *event)
{
    return event->x >= dialog->window.rect.left &&
           event->x < dialog->window.rect.right &&
           event->y >= dialog->window.rect.top &&
           event->y < dialog->window.rect.bottom;
}

static HostPalette host_palette_from_portable(const PortablePalette *palette)
{
    HostPalette result;
    memcpy(result.rgb, palette->rgb, sizeof(result.rgb));
    return result;
}

int portable_picture_modal_deadline_reached(uint32_t start_tick,
                                           uint32_t current_tick)
{
    uint32_t deadline = start_tick + (uint32_t)SOURCE_DIALOG_TICKS;
    /* WaitedEnough(long *timer, int delay) first checks TickCount()<*timer,
     * then compares *timer+delay to unsigned TickCount. The addition wraps at
     * the 32-bit source counter boundary on the supported DOS toolchain. */
    return current_tick < start_tick || deadline <= current_tick;
}

static PortablePictureModalStatus run_internal(
    Host *host, const PortablePalette *palette, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer, PortableDatabase *shared_database,
    PortableDatabase *window_database, PortablePictureDialogRequest request,
    PortablePictureModalTickSource tick_source, void *clock_context,
    int use_nominal_host_clock, volatile int *quit_flag)
{
    PortablePictureDialog dialog = {0};
    PortableFramebuffer *framebuffer;
    HostPalette host_palette;
    uint8_t *underlay = NULL;
    size_t underlay_size;
    uint64_t started = 0;
    uint32_t source_started = 0;
    PortablePictureModalStatus result = PORTABLE_PICTURE_MODAL_BAD_ARGUMENT;
    PortablePictureDialogStatus dialog_status;
    int restore_frame = 0;
    if (quit_flag != NULL && *quit_flag)
        return PORTABLE_PICTURE_MODAL_QUIT_REJECTED;
    if (host == NULL || palette == NULL || fonts == NULL || renderer == NULL ||
        shared_database == NULL || window_database == NULL ||
        (tick_source == NULL && !use_nominal_host_clock) ||
        !framebuffer_byte_count(renderer->framebuffer, &underlay_size) ||
        request.screen_width != HOST_LOGICAL_WIDTH ||
        request.screen_height != HOST_LOGICAL_HEIGHT)
        return PORTABLE_PICTURE_MODAL_BAD_ARGUMENT;
    framebuffer = renderer->framebuffer;
    underlay = (uint8_t *)malloc(underlay_size);
    if (underlay == NULL)
        return PORTABLE_PICTURE_MODAL_OUT_OF_MEMORY;
    memcpy(underlay, framebuffer->pixels, underlay_size);
    host_palette = host_palette_from_portable(palette);
    portable_picture_dialog_init(&dialog);
    dialog_status = portable_picture_dialog_prepare(&dialog, shared_database,
                                                     window_database, fonts,
                                                     request);
    if (dialog_status == PORTABLE_PICTURE_DIALOG_SUPPRESSED) {
        result = PORTABLE_PICTURE_MODAL_SUPPRESSED;
        goto cleanup;
    }
    if (dialog_status != PORTABLE_PICTURE_DIALOG_OK) {
        result = PORTABLE_PICTURE_MODAL_PREPARE_ERROR;
        goto cleanup;
    }
    restore_frame = 1;
    dialog_status = portable_picture_dialog_render(&dialog, fonts, renderer);
    if (dialog_status != PORTABLE_PICTURE_DIALOG_OK) {
        result = PORTABLE_PICTURE_MODAL_RENDER_ERROR;
        goto cleanup;
    }
    if (!host_present(host, framebuffer->pixels, framebuffer->stride, &host_palette)) {
        result = PORTABLE_PICTURE_MODAL_HOST_ERROR;
        goto cleanup;
    }
    if (tick_source != NULL)
        source_started = tick_source(clock_context);
    else
        started = host_time_ns();
    for (;;) {
        HostEvent event;
        /* DialogAbortOrCont checks DialogWait before consuming a BIOS key. */
        if ((tick_source != NULL &&
             portable_picture_modal_deadline_reached(source_started,
                                                       tick_source(clock_context))) ||
            (tick_source == NULL &&
             host_time_ns() - started >= SOURCE_DIALOG_TIMEOUT_NS)) {
            result = PORTABLE_PICTURE_MODAL_DISMISSED_BY_SOURCE_TIMEOUT;
            break;
        }
        int poll_status = host_poll_event(host, &event);
        if (poll_status < 0) {
            result = PORTABLE_PICTURE_MODAL_HOST_ERROR;
            break;
        }
        if (poll_status > 0) {
            if (event.kind == HOST_EVENT_QUIT) {
                if (quit_flag != NULL) *quit_flag = 1;
                result = PORTABLE_PICTURE_MODAL_QUIT_REJECTED;
                break;
            }
            /* Host modifier transitions are not BIOS keystrokes. Match the
             * same BIOS-word decoding used by the game input boundary. */
            if (event.kind == HOST_EVENT_KEY_DOWN) {
                int16_t logical_key;
                if (portable_input_decode_bios_key(event.key, &logical_key) ==
                        PORTABLE_INPUT_OK && logical_key != 0) {
                    result = PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY;
                    break;
                }
            }
            /* f_218D_0451 closes the active window on an outside mouse-down
             * when source window flag bit 0 is set. Clicks
             * inside ordinary dialog content do not dismiss PictureDialog. */
            if (event.kind == HOST_EVENT_MOUSE_DOWN &&
                (dialog.window.flags & PORTABLE_WINDOW_CLOSE_ON_SWITCH) != 0 &&
                !point_inside_dialog(&dialog, &event)) {
                result = PORTABLE_PICTURE_MODAL_DISMISSED_BY_WINDOW_CLICK;
                break;
            }
            if (!host_present(host, framebuffer->pixels, framebuffer->stride,
                              &host_palette)) {
                result = PORTABLE_PICTURE_MODAL_HOST_ERROR;
                break;
            }
        }
        host_wait_ms(POLL_WAIT_MS);
    }
cleanup:
    if (restore_frame) {
        memcpy(framebuffer->pixels, underlay, underlay_size);
        if (!host_present(host, framebuffer->pixels, framebuffer->stride,
                          &host_palette) &&
            (result == PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY ||
             result == PORTABLE_PICTURE_MODAL_DISMISSED_BY_WINDOW_CLICK ||
             result == PORTABLE_PICTURE_MODAL_DISMISSED_BY_SOURCE_TIMEOUT ||
             result == PORTABLE_PICTURE_MODAL_SUPPRESSED))
            result = PORTABLE_PICTURE_MODAL_HOST_ERROR;
    }
    portable_picture_dialog_dismiss(&dialog);
    portable_picture_dialog_release(&dialog);
    free(underlay);
    return result;
}

PortablePictureModalStatus portable_picture_modal_run(
    Host *host, const PortablePalette *palette, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer, PortableDatabase *shared_database,
    PortableDatabase *window_database, PortablePictureDialogRequest request,
    volatile int *quit_flag)
{
    return run_internal(host, palette, fonts, renderer, shared_database,
                        window_database, request, NULL, NULL, 1, quit_flag);
}

PortablePictureModalStatus portable_picture_modal_run_clocked(
    Host *host, const PortablePalette *palette, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer, PortableDatabase *shared_database,
    PortableDatabase *window_database, PortablePictureDialogRequest request,
    PortablePictureModalTickSource tick_count, void *clock_context,
    volatile int *quit_flag)
{
    return run_internal(host, palette, fonts, renderer, shared_database,
                        window_database, request, tick_count, clock_context,
                        0, quit_flag);
}

const char *portable_picture_modal_status_string(PortablePictureModalStatus status)
{
    switch (status) {
    case PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY: return "dismissed-by-key";
    case PORTABLE_PICTURE_MODAL_DISMISSED_BY_WINDOW_CLICK: return "dismissed-by-window-click";
    case PORTABLE_PICTURE_MODAL_DISMISSED_BY_SOURCE_TIMEOUT: return "dismissed-by-source-timeout";
    case PORTABLE_PICTURE_MODAL_SUPPRESSED: return "suppressed";
    case PORTABLE_PICTURE_MODAL_QUIT_REJECTED: return "quit-rejected";
    case PORTABLE_PICTURE_MODAL_BAD_ARGUMENT: return "bad-argument";
    case PORTABLE_PICTURE_MODAL_OUT_OF_MEMORY: return "out-of-memory";
    case PORTABLE_PICTURE_MODAL_PREPARE_ERROR: return "prepare-error";
    case PORTABLE_PICTURE_MODAL_RENDER_ERROR: return "render-error";
    case PORTABLE_PICTURE_MODAL_HOST_ERROR: return "host-error";
    default: return "unknown";
    }
}
