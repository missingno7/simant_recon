#include "overview_view.h"

#include <limits.h>
#include <string.h>

enum {
    MAP_WINDOW_OBJECT = 0x0102,
    EDIT_VIEW_OBJECT = 0x0004,
    SOURCE_EDIT_CELL_SIZE = 16,
    SOURCE_MARGIN_COLOR = 15,
    SOURCE_CURSOR_OUTLINE_WIDTH = 2,
    SOURCE_EGA_COLOR_PLANE_MASK = 0x0f
};

static PortableOverviewViewStatus resolve_object_rect(
    PortableWindowRegistry *registry, uint16_t object_id,
    PortableWindowRect *rect)
{
    return portable_window_registry_get_object_rect(registry, object_id, rect) ==
                   PORTABLE_WINDOW_REGISTRY_OK
               ? PORTABLE_OVERVIEW_VIEW_OK
               : PORTABLE_OVERVIEW_VIEW_REGISTRY_ERROR;
}

static PortableOverviewViewStatus ensure_window_recalculated(
    PortableWindowRegistry *registry, int16_t window_id)
{
    PortableWindowRegistryStatus status;
    if (window_id < 0 || window_id >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_OVERVIEW_VIEW_REGISTRY_ERROR;
    status = portable_window_registry_load(registry, window_id);
    if (status != PORTABLE_WINDOW_REGISTRY_OK)
        return PORTABLE_OVERVIEW_VIEW_REGISTRY_ERROR;
    if (!registry->slots[window_id].recalculated) {
        status = portable_window_registry_recalculate(registry, window_id, 0);
        if (status != PORTABLE_WINDOW_REGISTRY_OK)
            return PORTABLE_OVERVIEW_VIEW_REGISTRY_ERROR;
    }
    return PORTABLE_OVERVIEW_VIEW_OK;
}

static int assign_rect(PortableWindowRect *rect, int32_t left, int32_t top,
                       int32_t right, int32_t bottom)
{
    if (left < INT16_MIN || left > INT16_MAX || top < INT16_MIN || top > INT16_MAX ||
        right < INT16_MIN || right > INT16_MAX || bottom < INT16_MIN || bottom > INT16_MAX)
        return 0;
    rect->left = (int16_t)left;
    rect->top = (int16_t)top;
    rect->right = (int16_t)right;
    rect->bottom = (int16_t)bottom;
    return 1;
}

PortableOverviewViewStatus portable_overview_view_prepare(
    PortableWindowRegistry *registry,
    const PortableOverviewViewInput *input,
    PortableOverviewView *view)
{
    PortableOverviewView prepared;
    SimOverviewInput source;
    PortableOverviewViewStatus status;
    int32_t edit_width, edit_height, columns, rows;
    int32_t left, top, right, bottom;
    uint8_t scale;

    if (registry == 0 || input == 0 || input->world == 0 || view == 0)
        return PORTABLE_OVERVIEW_VIEW_BAD_ARGUMENT;
    if (!input->map_window_open)
        return PORTABLE_OVERVIEW_VIEW_WINDOW_CLOSED;
    if (input->hardware_profile != 0 && input->hardware_profile != 8)
        return PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_PROFILE;
    if (input->map_mode < 1 || input->map_mode > 3)
        return PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_MODE;
    if (registry->profile_id != input->hardware_profile)
        return PORTABLE_OVERVIEW_VIEW_PROFILE_MISMATCH;

    status = ensure_window_recalculated(registry, 1);
    if (status != PORTABLE_OVERVIEW_VIEW_OK)
        return status;
    status = ensure_window_recalculated(registry, 0);
    if (status != PORTABLE_OVERVIEW_VIEW_OK)
        return status;

    memset(&prepared, 0, sizeof prepared);
    status = resolve_object_rect(registry, MAP_WINDOW_OBJECT,
                                 &prepared.image_rect);
    if (status != PORTABLE_OVERVIEW_VIEW_OK)
        return status;
    status = resolve_object_rect(registry, EDIT_VIEW_OBJECT,
                                 &prepared.edit_viewport_rect);
    if (status != PORTABLE_OVERVIEW_VIEW_OK)
        return status;
    if (prepared.image_rect.right <= prepared.image_rect.left ||
        prepared.image_rect.bottom <= prepared.image_rect.top ||
        prepared.edit_viewport_rect.right <= prepared.edit_viewport_rect.left ||
        prepared.edit_viewport_rect.bottom <= prepared.edit_viewport_rect.top)
        return PORTABLE_OVERVIEW_VIEW_BAD_GEOMETRY;

    source.world = input->world;
    source.mode = input->map_mode;
    source.hardware_profile = input->hardware_profile;
    source.fresh = 0;
    source.previous_mode = -1;
    source.previous_pixels = 0;
    if (sim_overview_prepare(&source, &prepared.image) != SIM_OVERVIEW_OK)
        return PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_MODE;
    scale = prepared.image.scale_x;

    /* m0250 derives the live Edit viewport extent as width/cell-step and
     * height/cell-step + 1; InitMapFunctions selects 16-pixel cells here. */
    edit_width = (int32_t)prepared.edit_viewport_rect.right -
                 prepared.edit_viewport_rect.left;
    edit_height = (int32_t)prepared.edit_viewport_rect.bottom -
                  prepared.edit_viewport_rect.top;
    columns = edit_width / SOURCE_EDIT_CELL_SIZE;
    rows = edit_height / SOURCE_EDIT_CELL_SIZE + 1;
    if (columns <= 0 || rows <= 0)
        return PORTABLE_OVERVIEW_VIEW_BAD_GEOMETRY;

    left = (int32_t)prepared.image_rect.left + prepared.image.left_margin +
           (int32_t)input->world->map_view_x * scale;
    top = (int32_t)prepared.image_rect.top +
          (int32_t)input->world->map_view_y * scale;
    right = left + columns * scale;
    bottom = top + rows * scale;
    if (!assign_rect(&prepared.cursor_rect, left, top, right, bottom))
        return PORTABLE_OVERVIEW_VIEW_BAD_GEOMETRY;
    prepared.cursor_rect_valid = 1;
    prepared.cursor_outline_width = SOURCE_CURSOR_OUTLINE_WIDTH;
    *view = prepared;
    return PORTABLE_OVERVIEW_VIEW_OK;
}

static PortableRect rect_intersection(PortableRect a, PortableRect b)
{
    PortableRect r;
    r.left = a.left > b.left ? a.left : b.left;
    r.top = a.top > b.top ? a.top : b.top;
    r.right = a.right < b.right ? a.right : b.right;
    r.bottom = a.bottom < b.bottom ? a.bottom : b.bottom;
    if (r.right < r.left) r.right = r.left;
    if (r.bottom < r.top) r.bottom = r.top;
    return r;
}

PortableOverviewViewStatus portable_overview_view_render(
    const PortableOverviewView *view,
    PortableFramebuffer *framebuffer)
{
    PortableRect saved_clip, map_rect, left_margin, right_margin;
    PortableOverviewViewStatus status;
    int32_t margin;

    if (view == 0 || framebuffer == 0 || framebuffer->pixels == 0 ||
        view->image_rect.right <= view->image_rect.left ||
        view->image_rect.bottom <= view->image_rect.top)
        return PORTABLE_OVERVIEW_VIEW_BAD_ARGUMENT;
    saved_clip = framebuffer->clip;
    map_rect = (PortableRect){view->image_rect.left, view->image_rect.top,
                              view->image_rect.right, view->image_rect.bottom};
    portable_framebuffer_set_clip(framebuffer,
                                  rect_intersection(saved_clip, map_rect));

    margin = view->image.left_margin;
    if (margin > 0) {
        /* f_1B4E_000D(15) indexes the initialized identity g_41C0 map. */
        left_margin = (PortableRect){view->image_rect.left, view->image_rect.top,
                                     view->image_rect.left + margin,
                                     view->image_rect.bottom};
        right_margin = (PortableRect){view->image_rect.right - margin,
                                      view->image_rect.top,
                                      view->image_rect.right,
                                      view->image_rect.bottom};
        portable_fill_rect(framebuffer, left_margin, SOURCE_MARGIN_COLOR);
        portable_fill_rect(framebuffer, right_margin, SOURCE_MARGIN_COLOR);
    }
    status = sim_overview_blit(&view->image, framebuffer,
                               view->image_rect.left, view->image_rect.top) ==
                     SIM_OVERVIEW_OK
                 ? PORTABLE_OVERVIEW_VIEW_OK
                 : PORTABLE_OVERVIEW_VIEW_RENDER_ERROR;
    portable_framebuffer_set_clip(framebuffer, saved_clip);
    return status;
}

PortableOverviewViewStatus portable_overview_view_render_cursor(
    const PortableOverviewView *view,
    PortableFramebuffer *framebuffer)
{
    PortableRect rect;
    int32_t width;

    if (view == 0 || framebuffer == 0 || framebuffer->pixels == 0 ||
        !view->cursor_rect_valid || view->cursor_outline_width == 0 ||
        view->cursor_rect.right <= view->cursor_rect.left ||
        view->cursor_rect.bottom <= view->cursor_rect.top)
        return PORTABLE_OVERVIEW_VIEW_BAD_ARGUMENT;

    rect = (PortableRect){view->cursor_rect.left, view->cursor_rect.top,
                          view->cursor_rect.right, view->cursor_rect.bottom};
    width = view->cursor_outline_width;

    /* Match f_1CE2_032B's four non-overlapping half-open strips, in order.
     * The DOS EGA/VGA g_913C service XORs each selected plane (mask 0x0f). */
    portable_xor_rect(framebuffer,
                      (PortableRect){rect.left + width, rect.top + width,
                                     rect.right - width, rect.top},
                      SOURCE_EGA_COLOR_PLANE_MASK);
    portable_xor_rect(framebuffer,
                      (PortableRect){rect.left + width, rect.bottom - width,
                                     rect.right - width, rect.bottom},
                      SOURCE_EGA_COLOR_PLANE_MASK);
    portable_xor_rect(framebuffer,
                      (PortableRect){rect.left + width, rect.top,
                                     rect.left, rect.bottom},
                      SOURCE_EGA_COLOR_PLANE_MASK);
    portable_xor_rect(framebuffer,
                      (PortableRect){rect.right, rect.top,
                                     rect.right - width, rect.bottom},
                      SOURCE_EGA_COLOR_PLANE_MASK);
    return PORTABLE_OVERVIEW_VIEW_OK;
}

const char *portable_overview_view_status_string(PortableOverviewViewStatus status)
{
    switch (status) {
    case PORTABLE_OVERVIEW_VIEW_OK: return "ok";
    case PORTABLE_OVERVIEW_VIEW_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_OVERVIEW_VIEW_WINDOW_CLOSED: return "map window is closed";
    case PORTABLE_OVERVIEW_VIEW_REGISTRY_ERROR: return "map or edit viewport geometry unavailable";
    case PORTABLE_OVERVIEW_VIEW_PROFILE_MISMATCH: return "window and renderer hardware profiles differ";
    case PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_PROFILE: return "overview supports hardware profiles 0 and 8";
    case PORTABLE_OVERVIEW_VIEW_UNSUPPORTED_MODE: return "yard or unsupported map mode";
    case PORTABLE_OVERVIEW_VIEW_BAD_GEOMETRY: return "invalid map or edit viewport geometry";
    case PORTABLE_OVERVIEW_VIEW_RENDER_ERROR: return "overview raster failed";
    }
    return "unknown overview view error";
}
