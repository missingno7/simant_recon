/* Calls the actual converted owners. Host dependencies are controlled; no
 * duplicate menu/keyboard implementation is linked into this fixture. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern int16_t g_2D3A, ui_pending_menu_item;
extern void test_set_menu(int16_t);
extern int16_t menu_track_popup(char *, void *, int16_t);
extern void input_dispatch_game_key(int16_t);
extern int16_t DoEvent(int16_t);
extern void ui_pump_events_edge_scroll(int16_t);
static int ctrl_once, ctrl_reads, calls;

void __wrap_portable_m1b73_event_enqueue_four_word_command(
    int16_t code, int16_t segment, int16_t modifiers, int16_t h, int16_t v)
{
    if (segment || modifiers || h) exit(2);
    printf("%d %d\n", code, v);
    ++calls;
}
int16_t __wrap_kbd_read_key_code(void) { return 0x821; }
void __wrap_CheatKeys(int16_t key) { (void)key; }
int16_t __wrap_kbd_scan_state(int16_t key)
{
    if (key == 0x1d) return ctrl_once && ctrl_reads++ == 0;
    return key == 0x48;
}
int16_t __wrap_WinPrintf(char *fmt, ...) { (void)fmt; return 0; }
int16_t __wrap_win_Events(void) { return 0; }
int16_t __wrap_kbd_poll_bios_key(void) { return 1; }
int16_t __wrap_kbd_scroll_lock_state(void) { return 1; }
void __wrap_win_NoWindowsShouldBeLocked(void) {}
int16_t __wrap_edit_scroll_and_redraw(int16_t dx, int16_t dy)
{ (void)dx; (void)dy; return 0; }

int main(void)
{
    char selection = 99;
    test_set_menu(5);
    menu_track_popup(&selection, NULL, 20);
    if (selection != 0) return 3;
    menu_track_popup(&selection, NULL, 0x1212);
    input_dispatch_game_key(0x1234);
    input_dispatch_game_key((int16_t)0xabcd);
    g_2D3A = ui_pending_menu_item = 0;
    DoEvent(1234);
    ctrl_once = 1; ctrl_reads = 0;
    DoEvent(1234); /* Ctrl+Up leaves SI = dy = -1. */
    ctrl_once = 0;
    ui_pump_events_edge_scroll(2345);
    return calls == 7 ? 0 : 4;
}
