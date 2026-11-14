/* Execute the converted canonical branch under two interrupt placements in
 * one observed-service interval. The late control matches DOS's callback
 * inside MacTickCount; neither placement changes the game branch itself. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int16_t mouse_x_pixels, mouse_y_pixels;
int16_t gfx_screen_width_pixels=640, gfx_screen_height_pixels=480;
int16_t ui_pending_menu_item;
static unsigned samples, scrolls;
static int early;
extern void ui_pump_events_edge_scroll(int16_t incoming_si);
int16_t win_Events(void) { return 0; }
int16_t kbd_poll_bios_key(void) { return 0; }
int16_t kbd_scan_state(int16_t scan) { (void)scan; return 0; }
void DoEvent(int16_t incoming_si) { (void)incoming_si; abort(); }
int16_t kbd_scroll_lock_state(void) {
    ++samples;
    if (early) mouse_x_pixels=mouse_y_pixels=0;
    return 0;
}
int16_t edit_scroll_and_redraw(int16_t dx,int16_t dy) {
    if (dx!=-1 || dy!=-1) abort();
    ++scrolls;
    return 0;
}
int main(void) {
    early=0; mouse_x_pixels=200; mouse_y_pixels=200;
    ui_pump_events_edge_scroll(0);
    /* DOS has reached the next MacTickCount body before the callback. */
    mouse_x_pixels=mouse_y_pixels=0;
    if (samples!=1 || scrolls) return 1;
    early=1; mouse_x_pixels=200; mouse_y_pixels=200;
    ui_pump_events_edge_scroll(0);
    if (samples!=2 || scrolls!=1) return 2;
    /* Negative controls: inclusive x=1, strict y<1; no foreground check. */
    early=0; mouse_x_pixels=2; mouse_y_pixels=1;
    ui_pump_events_edge_scroll(0);
    if (samples!=3 || scrolls!=1) return 3;
    puts("PASS canonical edge phase: equal service ordinal does not fix interrupt placement");
    return 0;
}
