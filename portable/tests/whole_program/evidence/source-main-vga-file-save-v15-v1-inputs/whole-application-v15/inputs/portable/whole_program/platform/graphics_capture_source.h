#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_CAPTURE_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_CAPTURE_SOURCE_H

#include "portable/whole_program/platform/graphics.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef int16_t (*SimGraphicsCaptureSizeCallback)(int16_t left, int16_t top,
                                                   int16_t right, int16_t bottom);
typedef void (*SimGraphicsCaptureCallback)(int16_t left, int16_t top,
                                          int16_t right, int16_t bottom,
                                          char *buffer);

/* S00 table slots 6..8 (o00_31AD_0522, _11FB, _0550). */
extern SimGraphicsCaptureSizeCallback g_9140;
extern SimGraphicsCaptureSizeCallback g_9144;
extern SimGraphicsCaptureCallback g_9148;

/* Install/uninstall the three source callbacks after the common source owner
 * has been bound. The callback reuses that owner's sole indexed framebuffer. */
SimGraphicsStatus sim_graphics_source_capture_bind(SimGraphicsDriver *graphics);
void sim_graphics_source_capture_unbind(void);

/* Temporarily authorize exterior padding for the cursor's one save-under
 * buffer. Generic captures remain bounded to the logical framebuffer. */
SimGraphicsStatus sim_graphics_source_capture_cursor_buffer(
    uint8_t *buffer, size_t capacity);
void sim_graphics_source_capture_cursor_buffer_clear(uint8_t *buffer);

/* Checked test/host API. Size returns the low source AX word; the checked
 * variant rejects source rectangles outside the active logical framebuffer. */
uint16_t sim_graphics_s00_capture_size_word(int16_t left, int16_t top,
                                           int16_t right, int16_t bottom);
uint16_t sim_graphics_s00_mask_capture_size_word(int16_t left, int16_t top,
                                                 int16_t right, int16_t bottom);
SimGraphicsStatus sim_graphics_s00_capture_size_checked(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, size_t *size_out);
SimGraphicsStatus sim_graphics_s00_capture_rect(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size);

/* Source ABI support for rectangles whose lower rows extend beyond the
 * displayed viewport but remain inside the original 64 KiB planar aperture.
 * Visible rows come from the single indexed framebuffer owner; hidden rows
 * come from the already-bound source plane backing. */
SimGraphicsStatus sim_graphics_s00_capture_rect_source_aperture(
    const SimGraphicsDriver *graphics, int16_t left, int16_t top,
    int16_t right, int16_t bottom, uint8_t *buffer, size_t buffer_size);

#ifdef __cplusplus
}
#endif
#endif
