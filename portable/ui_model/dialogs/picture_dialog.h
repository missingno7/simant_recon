#ifndef SIMANT_PORTABLE_UI_MODEL_PICTURE_DIALOG_H
#define SIMANT_PORTABLE_UI_MODEL_PICTURE_DIALOG_H

#include "../windows/render.h"
#include "../../game/resources/fonts.h"

typedef enum PortablePictureDialogStatus {
    PORTABLE_PICTURE_DIALOG_OK = 0,
    PORTABLE_PICTURE_DIALOG_SUPPRESSED,
    PORTABLE_PICTURE_DIALOG_BAD_ARGUMENT,
    PORTABLE_PICTURE_DIALOG_DATABASE_ERROR,
    PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE,
    PORTABLE_PICTURE_DIALOG_UNSUPPORTED,
    PORTABLE_PICTURE_DIALOG_OUT_OF_MEMORY,
    PORTABLE_PICTURE_DIALOG_RENDER_ERROR
} PortablePictureDialogStatus;

typedef struct PortablePictureDialogRequest {
    int16_t picture_id;
    int16_t string_object_id;
    uint8_t force;
    uint8_t strings_enabled; /* Source fd_3D57_07A8[3]. */
    uint16_t screen_width;   /* Source g_3DB2. */
    uint16_t screen_height;  /* Source g_3DB4. */
} PortablePictureDialogRequest;

typedef struct PortablePictureDialogLine {
    const uint8_t *bytes; /* Borrowed from the retained kind-4 record. */
    size_t length;
    int16_t draw_x;
    int16_t draw_y;
} PortablePictureDialogLine;

typedef struct PortablePictureDialog {
    PortableDbRecord strings_record;
    PortableDbRecord picture_record;
    PortableDbRecord window_record;
    PortableWindowResource window;
    PortablePictureDialogLine *lines;
    size_t line_count;
    PortablePictureDialogRequest request;
    PortableWindowRect rect;
    uint16_t picture_width;
    uint16_t picture_height;
    int16_t font_id;
    uint8_t text_color_index;
    uint8_t visible;
    uint8_t dismissed;
} PortablePictureDialog;

void portable_picture_dialog_init(PortablePictureDialog *dialog);

/* Prepare exact PictureDialog state from the supplied database/font assets.
 * The returned model owns its records and window parse; its font pointer is
 * borrowed from `fonts` only during prepare/render. A suppressed PictStrnDialog
 * does not load resources or become modal. */
PortablePictureDialogStatus portable_picture_dialog_prepare(
    PortablePictureDialog *dialog, PortableDatabase *shared_database,
    PortableDatabase *window_database,
    const PortableFontSet *fonts, PortablePictureDialogRequest request);

/* Render the native window, optional kind-2 image, then centered source text.
 * Caller presents the framebuffer and handles synchronous modal input. */
PortablePictureDialogStatus portable_picture_dialog_render(
    const PortablePictureDialog *dialog, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer);

/* The SDL host calls this after its modal event loop ends. */
void portable_picture_dialog_dismiss(PortablePictureDialog *dialog);
void portable_picture_dialog_release(PortablePictureDialog *dialog);
const char *portable_picture_dialog_status_string(
    PortablePictureDialogStatus status);

#endif
