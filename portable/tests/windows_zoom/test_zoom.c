#include "../../ui_model/windows/zoom.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static PortableWindowZoomState seed(void)
{
    PortableWindowZoomState s;
    memset(&s, 0, sizeof(s));
    s.window_rect = (PortableWindowRect){100, 100, 300, 250};
    s.frame_rect = (PortableWindowRect){100, 100, 200, 150};
    s.flags = PORTABLE_WINDOW_ZOOM_ENABLED;
    s.min_width = 40;
    s.min_height = 30;
    s.grid_x = 8;
    s.grid_y = 8;
    return s;
}

int main(void)
{
    PortableWindowZoomState s, before;
    PortableWindowZoomBounds bounds = {24, 640, 400};
    PortableWindowZoomResidue residue = {0, 0, {12, 13, 14, 15}, {100, 100, 300, 250}};
    PortableWindowZoomStep steps[64];
    size_t count;
    int16_t stack[] = {0x0700, 0x0701, 0x0702, (int16_t)0x8000};
    PortableWindowRect object_rects[] = {{100,100,300,250},{0,0,100,80},{0,0,90,60},{0,0,0,0}};
    PortableWindowZoomStatus status;

    s = seed();
    before = s;
    status = portable_window_zoom_toggle(&s, &bounds, &residue, (int16_t)0x8000,
                                         stack, 4, object_rects, steps, 64, &count, 10000);
    assert(status == PORTABLE_WINDOW_ZOOM_OK && count == 0);
    assert(memcmp(&s, &before, sizeof(s)) == 0);

    s.flags = 0;
    before = s;
    status = portable_window_zoom_toggle(&s, &bounds, &residue, 0x0700,
                                         stack, 4, object_rects, steps, 64, &count, 10000);
    assert(status == PORTABLE_WINDOW_ZOOM_DISABLED && count == 2);
    assert(steps[0].kind == PORTABLE_ZOOM_LOCK && steps[1].kind == PORTABLE_ZOOM_UNLOCK);
    assert(memcmp(&s, &before, sizeof(s)) == 0);

    s = seed();
    status = portable_window_zoom_toggle(&s, &bounds, &residue, 0x0700,
                                         stack, 4, object_rects, steps, 64, &count, 10000);
    assert(status == PORTABLE_WINDOW_ZOOM_OK);
    assert((s.flags & PORTABLE_WINDOW_ZOOMED) != 0 && s.has_zoom_rect);
    assert(s.zoom_rect.left == 100 && s.zoom_rect.top == 100 &&
           s.zoom_rect.right == 200 && s.zoom_rect.bottom == 150);
    assert(steps[0].kind == PORTABLE_ZOOM_LOCK);
    assert(steps[1].kind == PORTABLE_ZOOM_RECALCULATE);
    assert(steps[2].kind == PORTABLE_ZOOM_REBUILD_CLIPS);
    assert(steps[3].kind == PORTABLE_ZOOM_WINDOW_CALLBACK);
    assert(steps[count - 3].kind == PORTABLE_ZOOM_DRAW_WINDOW);
    assert(steps[count - 2].kind == PORTABLE_ZOOM_BORDER_08EA);
    assert(steps[count - 1].kind == PORTABLE_ZOOM_BORDER_0831);
    assert(steps[count - 5].window_id == 0x0701);
    assert(steps[count - 14].window_id == 0x0702);

    /* A second toggle restores the saved object x/y/width/height words. */
    s.frame_rect = (PortableWindowRect){0, 24, 640, 376};
    status = portable_window_zoom_toggle(&s, &bounds, &residue, 0x0700,
                                         stack, 4, object_rects, steps, 64, &count, 10000);
    assert(status == PORTABLE_WINDOW_ZOOM_OK);
    assert((s.flags & PORTABLE_WINDOW_ZOOMED) == 0);
    assert(s.frame_rect.left == 100 && s.frame_rect.top == 100 &&
           s.frame_rect.right == 200 && s.frame_rect.bottom == 150);

    /* Source flag 0x1000 remains a raw constraint bit. */
    s = seed();
    s.flags |= PORTABLE_WINDOW_ZOOM_SOURCE_FLAG_1000;
    {
        PortableWindowRect r = {-10, 24, 650, 400};
        status = portable_window_zoom_constrain(&s, &bounds, 0, &r, 10000);
        assert(status == PORTABLE_WINDOW_ZOOM_OK);
        assert(r.left >= 0 && r.right <= bounds.screen_right && r.top >= bounds.desktop_top);
    }
    puts("window zoom semantic model: ok");
    return 0;
}
