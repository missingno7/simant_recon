/*
 * Defines the functional full screen clip rectangle followed by its terminator. Drawing setup
 * uses this as a clipping list.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Functional screen clip list; historical TU/order/placement unclaimed.
 */

struct Rect { int left; int top; int right; int bottom; };
#define RECT_END ((int)0x8000)
/*
 * Full-screen clip rectangle followed by its existing terminator.
 */
struct Rect near gfx_screen_clip_list[2] = {
    { 0, 0, 349, 639 },
    { RECT_END, RECT_END, RECT_END, RECT_END }
};
