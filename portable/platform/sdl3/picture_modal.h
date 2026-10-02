#ifndef SIMANT_PORTABLE_SDL3_PICTURE_MODAL_H
#define SIMANT_PORTABLE_SDL3_PICTURE_MODAL_H

#include "../host.h"
#include "../../render/palette.h"
#include "../../ui_model/dialogs/picture_dialog.h"

typedef enum PortablePictureModalStatus {
    PORTABLE_PICTURE_MODAL_DISMISSED_BY_KEY = 0,
    PORTABLE_PICTURE_MODAL_DISMISSED_BY_WINDOW_CLICK,
    PORTABLE_PICTURE_MODAL_DISMISSED_BY_SOURCE_TIMEOUT,
    PORTABLE_PICTURE_MODAL_SUPPRESSED,
    PORTABLE_PICTURE_MODAL_QUIT_REJECTED,
    PORTABLE_PICTURE_MODAL_BAD_ARGUMENT,
    PORTABLE_PICTURE_MODAL_OUT_OF_MEMORY,
    PORTABLE_PICTURE_MODAL_PREPARE_ERROR,
    PORTABLE_PICTURE_MODAL_RENDER_ERROR,
    PORTABLE_PICTURE_MODAL_HOST_ERROR
} PortablePictureModalStatus;

/* Returns the raw BIOS TickCount value. Do not multiply by three: the dialog's
 * source WaitedEnough deadline is expressed in TickCount units, not Mac ticks. */
typedef uint32_t (*PortablePictureModalTickSource)(void *context);

/* Exact WaitedEnough predicate used by DialogWait for a 270-tick timeout.
 * This keeps the source's unsigned TickCount comparisons and wrapped deadline
 * addition explicit for callers and boundary tests. */
int portable_picture_modal_deadline_reached(uint32_t start_tick,
                                           uint32_t current_tick);

/* Synchronously show one source PictureDialog over the current indexed frame.
 * The underlying frame is restored on every return. A key closes the source
 * dialog; a click outside closes it only when the source window permits that
 * action. A host quit reports QUIT_REJECTED and sets quit_flag when supplied.
 * The compatibility wrapper below uses a nominal host-time deadline. */
PortablePictureModalStatus portable_picture_modal_run(
    Host *host, const PortablePalette *palette, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer, PortableDatabase *shared_database,
    PortableDatabase *window_database, PortablePictureDialogRequest request,
    volatile int *quit_flag);

/* Live integration path. The source samples TickCount after drawing, then
 * expires when WaitedEnough reports start+270 <= now or now < start. */
PortablePictureModalStatus portable_picture_modal_run_clocked(
    Host *host, const PortablePalette *palette, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer, PortableDatabase *shared_database,
    PortableDatabase *window_database, PortablePictureDialogRequest request,
    PortablePictureModalTickSource tick_count, void *clock_context,
    volatile int *quit_flag);

const char *portable_picture_modal_status_string(PortablePictureModalStatus status);

#endif
