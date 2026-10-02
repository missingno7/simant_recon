#include "navigation_adapter.h"

#include "audio_adapter.h"
#include "recovered_state.h"

#include <stdlib.h>
#include <string.h>

static _Thread_local SimRecoveredNavigationBinding *active_navigation;
static _Thread_local unsigned map_plane_depth;

static void emit(SimRecoveredNavigationEventKind kind, int16_t a, int16_t b,
                 int16_t c, int16_t d)
{
    SimRecoveredNavigationEvent *event;
    if (active_navigation == NULL) abort();
    if (active_navigation->failed) return;
    if (active_navigation->event_count >=
        SIM_RECOVERED_NAVIGATION_EVENT_CAPACITY) {
        active_navigation->failed = 1;
        return;
    }
    event = &active_navigation->events[active_navigation->event_count++];
    event->kind = kind;
    event->a = a;
    event->b = b;
    event->c = c;
    event->d = d;
    if (active_navigation->event_sink != NULL &&
        !active_navigation->event_sink(active_navigation->event_context, event))
        active_navigation->failed = 1;
}

void sim_recovered_navigation_bind(SimRecoveredNavigationBinding *binding)
{
    SimRecoveredNavigationEffect event_sink;
    void *event_context;
    if (binding == NULL || active_navigation != NULL) abort();
    event_sink = binding->event_sink;
    event_context = binding->event_context;
    memset(binding, 0, sizeof(*binding));
    binding->event_sink = event_sink;
    binding->event_context = event_context;
    active_navigation = binding;
    map_plane_depth = 0;
}

void sim_recovered_navigation_unbind(SimRecoveredNavigationBinding *binding)
{
    if (binding == NULL || active_navigation != binding) abort();
    active_navigation = NULL;
    map_plane_depth = 0;
}

static void invalidate_map(void)
{
    emit(SIM_NAV_INVALIDATE_MAP, 0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
}

static int16_t clamp_i16(int32_t value, int16_t low, int16_t high)
{
    if (value < low) return low;
    if (value > high) return high;
    return (int16_t)value;
}

/* Source f_0250_0D10 uses a 16.16 error accumulator. Preserve its one-step
 * minor-axis rounding, then apply f_0250_0F2C's map-bound clamp. */
static void center_edit(int16_t x, int16_t y)
{
    int16_t target_x, target_y;
    int16_t dx, dy, sx, sy;
    uint32_t error = 0;
    uint32_t fraction;
    int32_t x_distance, y_distance;
    int32_t i;
    int32_t map_width;

    target_x = (int16_t)(x - fd_50F6_10E0 / 2);
    target_y = (int16_t)(y - fd_50F6_10DE / 2);
    dx = (int16_t)(target_x - fd_50F6_0508[0]);
    dy = (int16_t)(target_y - fd_50F6_0508[1]);
    sx = dx < 0 ? -1 : 1;
    sy = dy < 0 ? -1 : 1;
    x_distance = dx < 0 ? -(int32_t)dx : dx;
    y_distance = dy < 0 ? -(int32_t)dy : dy;

    if (x_distance == 0) {
        for (i = 0; i < y_distance; ++i) fd_50F6_0508[1] += sy;
    } else if (y_distance == 0) {
        for (i = 0; i < x_distance; ++i) fd_50F6_0508[0] += sx;
    } else if (y_distance >= x_distance) {
        fraction = ((uint32_t)x_distance << 16) / (uint32_t)y_distance;
        for (i = 0; i < y_distance; ++i) {
            fd_50F6_0508[1] += sy;
            error += fraction;
            if ((error >> 16) & 1u) {
                fd_50F6_0508[0] += sx;
                error ^= UINT32_C(0x10000);
            }
        }
    } else {
        fraction = ((uint32_t)y_distance << 16) / (uint32_t)x_distance;
        for (i = 0; i < x_distance; ++i) {
            fd_50F6_0508[0] += sx;
            error += fraction;
            if ((error >> 16) & 1u) {
                fd_50F6_0508[1] += sy;
                error ^= UINT32_C(0x10000);
            }
        }
    }

    map_width = (MapPlane == 0 || MapPlane == 1) ? 128 : 64;
    fd_50F6_0508[0] = clamp_i16(fd_50F6_0508[0], 0,
        (int16_t)(map_width - fd_50F6_10E0));
    fd_50F6_0508[1] = clamp_i16(fd_50F6_0508[1], 0,
        (int16_t)(64 - fd_50F6_10DE));
    emit(SIM_NAV_CENTER_VIEW, MapPlane, x, y, 0);
}

static void update_edit(void)
{
    emit(SIM_NAV_UPDATE_EDIT, 0, 0, 0, 0);
}

static void set_map_title(void)
{
    emit(SIM_NAV_SET_MAP_TITLE, 0, 0, 0, 0);
}

static void set_map_mode_ant(int16_t mode)
{
    if (fd_3D57_07C8[0] == mode && mode >= 4 && mode <= 8) mode = 1;
    switch (mode) {
    case 0:
        fd_3D57_07C8[0] = 0;
        if (YardMode == 4) {
            SetMapPlane(fd_50F6_0332);
            set_map_title();
        } else {
            /* This event stands for the source SetYardMode(YardMode) call,
             * including its own title update and object/window work. */
            emit(SIM_NAV_REFRESH_YARD, YardMode, 0, 0, 0);
        }
        break;
    case 4: case 5: case 6: case 7: case 8:
        /* SetMapPlane(1) in the source. */
        if (MapPlane != 1) SetMapPlane(1);
        /* fall through */
    case 1: case 2: case 3:
        fd_3D57_07C8[0] = mode;
        set_map_title();
        if (mode >= 4 && mode <= 8)
            emit(SIM_NAV_SELECT_OBJECT,
                 (int16_t)(mode == 4 ? 0x109 : mode == 5 ? 0x10a :
                           mode == 6 ? 0x10c : mode == 7 ? 0x10d : 0x10b),
                 0, 0, 0);
        else
            emit(SIM_NAV_UNSELECT_GROUP, 0x100, 2, 0, 0);
        break;
    default:
        /* Other modes are not used by this source call path. */
        abort();
    }
}

void SetMapPlaneLocation(int16_t plane, int16_t x, int16_t y)
{
    int16_t win = 0, obj = 0;
    if (plane < 0 || plane > 3) abort();
    if (plane != 0)
        invalidate_map();
    else
        fd_50F6_0332 = MapPlane;
    MapPlane = plane;
    fd_50F6_0F36 = (int16_t)((plane == 1 ? 0x80 : 0x40) -
                             fd_50F6_0FB6);
    if (MapPlane != 0) {
        center_edit(x, y);
        update_edit();
    } else {
        fd_50F6_07BC[0] = fd_50F6_07CA[0];
        fd_50F6_07BC[1] = fd_50F6_07CA[1];
    }
    set_map_mode_ant(MapPlane);
    switch (MapPlane) {
    case 0: obj = 0x105; break;
    case 1: win = 8; obj = 0x106; break;
    case 2: win = 9; obj = 0x107; break;
    case 3: win = 10; obj = 0x108; break;
    }
    if (win != 0) {
        emit(SIM_NAV_CLIP_SET_WINDOW, 0, 0, 0, 0);
        emit(SIM_NAV_SELECT_WINDOW, win, 0, 0, 0);
        emit(SIM_NAV_CLIP_OFF, 0, 0, 0, 0);
    }
    if (obj != 0) {
        emit(SIM_NAV_CLIP_SET_WINDOW, 0x100, 0, 0, 0);
        emit(SIM_NAV_SELECT_OBJECT, obj, 0, 0, 0);
        emit(SIM_NAV_UNSELECT_GROUP, 0x100, 2, 0, 0);
        emit(SIM_NAV_CLIP_OFF, 0, 0, 0, 0);
    }
}

void GotoMapPoint(int16_t plane, int16_t x, int16_t y)
{
    if (plane < 0 || plane > 3) abort();
    if (MapPlane == plane && plane > 0) {
        center_edit(x, y);
        fd_50F6_0AA6 = 0;
    } else {
        SetMapPlaneLocation(plane, x, y);
    }
}

void SetMapPlane(int16_t plane)
{
    int16_t x, y;
    if (plane < 0 || plane > 3 || ++map_plane_depth > 4) abort();
    if (plane != 0)
        invalidate_map();
    else
        fd_50F6_0332 = MapPlane;
    MapPlane = plane;
    fd_50F6_0F36 = (int16_t)((plane == 1 ? 0x80 : 0x40) -
                             fd_50F6_0FB6);
    fd_50F6_0D70 = fd_3D57_07C0[plane];
    switch (plane) {
    case 0: x = fd_50F6_07BC[0]; y = fd_50F6_07BC[1]; break;
    case 1: x = fd_50F6_0596[0]; y = fd_50F6_0596[1]; break;
    case 2: x = fd_50F6_06A6[0]; y = fd_50F6_06A6[1]; break;
    default: x = fd_50F6_072E[0]; y = fd_50F6_072E[1]; break;
    }
    emit(SIM_NAV_SET_EDIT_MODE, fd_50F6_0D70, plane, 0, 0);
    SetMapPlaneLocation(plane, x, y);
    if (MapPlane != 0) center_edit(x, y);
    set_map_mode_ant(MapPlane);
    update_edit();
    --map_plane_depth;
}

void CenterAnt(void)
{
    fd_50F6_1074 = 1;
    if (MePlane != MapPlane) SetMapPlane(MePlane);
    center_edit(MeLocX, MeLocY);
}

void GotoMyAnt(void)
{
    fd_50F6_1074 = 1;
    if (fd_50F6_0EAC == 3)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(MePlane, MeLocX, MeLocY);
}
