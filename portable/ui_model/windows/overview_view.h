#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_OVERVIEW_VIEW_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_OVERVIEW_VIEW_H

#include "registry.h"
#include "../../game/render/overview.h"

typedef enum PortableOverviewViewStatus {
    PORTABLE_OVERVIEW_VIEW_OK = 0,
    PORTABLE_OVERVIEW_VIEW_BAD_ARGUMENT,
    PORTABLE_OVERVIEW_VIEW_WINDOW_CLOSED,
    PORTABLE_OVERVIEW_VIEW_REGISTRY_ERROR,
    PORTABLE_OVERVIEW_VIEW_PROFILE_MISMATCH,
    PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_PROFILE,
    PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_MODE,
    PORTABLE_OVERVIEW_VIEW_BAD_GEOMETRY,
    PORTABLE_OVERVIEW_VIEW_RENDER_ERROR
} PortableOverviewViewStatus;

typedef struct PortableOverviewViewInput {
    const SimGameWorld *world;
    int16_t map_mode;          /* Source fd_3D57_07C8: 1 surface, 2/3 nests. */
    int16_t hardware_profile;  /* Source g_5A97; this projection supports 0 and 8. */
    uint8_t map_window_open;    /* Source win_IsWinOpen(0x0100) gate. */
} PortableOverviewViewInput;

typedef struct PortableOverviewView {
    PortableWindowRect image_rect; /* win_GetObjRect(0x0102), left/top is source origin. */
    PortableWindowRect edit_viewport_rect; /* win_GetObjRect(0x0004), used for cursor extent. */
    PortableWindowRect cursor_rect; /* S12 DrawMapCursor source geometry; not XOR-rendered. */
    uint8_t cursor_rect_valid;
    uint8_t cursor_outline_width; /* Source GRectInvOutline width=2. */
    SimOverviewImage image;
} PortableOverviewView;

/* Resolve actual HCEGANT window geometry and prepare the selected S12 image.
 * The registry's profile must match input.hardware_profile. Mode 0 is the
 * separate yard renderer and remains unsupported here. */
PortableOverviewViewStatus portable_overview_view_prepare(
    PortableWindowRegistry *registry,
    const PortableOverviewViewInput *input,
    PortableOverviewView *view);

/* Draw the indexed overview clipped to object 0x0102. Nest side margins use
 * the source f_1B4E_000D(15) mapping (identity palette entry 15). The source
 * XOR cursor outline is returned as geometry but not applied here because its
 * display-driver g_913C inversion contract is not established for host pixels. */
PortableOverviewViewStatus portable_overview_view_render(
    const PortableOverviewView *view,
    PortableFramebuffer *framebuffer);

/* Apply the source EGA/VGA map cursor outline using the active framebuffer
 * clip (the caller supplies the clip_SetWin(0x0100) region).  S00 g_913C
 * selects XOR across all four color planes, so indexed colors toggle by 0x0F.
 * The active clip is preserved. */
PortableOverviewViewStatus portable_overview_view_render_cursor(
    const PortableOverviewView *view,
    PortableFramebuffer *framebuffer);

const char *portable_overview_view_status_string(PortableOverviewViewStatus status);

#endif
