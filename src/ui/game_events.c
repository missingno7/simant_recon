/*
 * Runs the main game event dispatcher and keyboard command handling. The same file provides a
 * debug memory report.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 19 (S19); segment 384C; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory.
 */

#include "events_ids.h"
#include "windows_ids.h"

#include "event.h"

struct KeyCmd {
    int key;
    int cmd;
};

char fd_55B3_2CBA = 0;
/*
 * Queued menu selection consumed and cleared by DoEvent.
 */
int ui_pending_menu_item = 0;
struct KeyCmd g_2CBE[] = {
    { 0x821, EVENT_MENU_BAR_BASE }, { 0x811, EVENT_MENU_BAR_WINDOW }, { 0x82f, EVENT_MENU_BAR_VIEW }, { 0x818, EVENT_MENU_BAR_OPTIONS },
    { 0x81f, EVENT_MENU_BAR_SPEED }, { 0x83c, EVENT_MENU_BAR_BASE }, { 0x83d, EVENT_MENU_BAR_WINDOW }, { 0x83e, EVENT_MENU_BAR_VIEW },
    { 0x83f, EVENT_MENU_BAR_OPTIONS }, { 0x840, EVENT_MENU_BAR_SPEED }, { 0x29, EVENT_MENU_PAUSE }, { 0x21, EVENT_MENU_SLOW },
    { 0x40, EVENT_MENU_NORMAL }, { 0x23, EVENT_MENU_FAST }, { 0x24, EVENT_MENU_ULTRA }, { 0x0e, EVENT_MENU_NEW },
    { 0x13, EVENT_MENU_SAVE }, { 0x01, EVENT_MENU_SAVE_AS }, { 0x0c, EVENT_MENU_LOAD }, { 0x05, EVENT_MENU_EDIT },
    { 0x0d, EVENT_MENU_MAP }, { 0x02, EVENT_MENU_BEHAVIOR }, { 0x03, EVENT_MENU_CASTE }, { 0x14, EVENT_MENU_STATUS },
    { 0x07, EVENT_MENU_AUTOTRACK }, { 0x0a, EVENT_MENU_MUSIC }, { 0x0b, EVENT_MENU_SOUND_EFFECTS }, { 0x18, EVENT_MENU_QUIT },
    { 0x11, EVENT_MENU_QUIT }, { 0x19, EVENT_MENU_YARD }, { 0, 0 }
};
int g_2D3A = 0;

extern void far win_NoWindowsShouldBeLocked(void);
extern int far LoadGame(char far *name);
extern int far CurGameType;
extern int far NewGame(int a);
extern void far MenuQuit(void);
extern int far SaveGame(int useLast);
extern int far win_Events(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern void far win_close_auto_dismiss(void);
extern int far WinPrintf(char far *format, ...);
extern void far ProcEditEvent(struct Event far *ev);
extern void far ProcMapEvent(struct Event far *ev);
extern void far ProcInfoEvent(struct Event far *ev);
extern void far ProcModeEvent(struct Event far *ev);
extern void far ProcCasteEvent(struct Event far *ev);
void far input_translate_special_key(struct Event far *ev);
extern void far ProcMenu(struct Event far *ev);
extern void far input_capture_screen(void);
extern void (far * near g_9130)(void);
extern int far menu_track_bar_selection(struct Event far *ev);
extern void far font_SetFont(int font);
extern void far input_release_screen_capture(void);
extern int far kbd_scan_state(int key);
extern int far edit_scroll_and_redraw(int dx, int dy);
extern int far kbd_poll_bios_key(void);
void far input_dispatch_game_key(void);

int far DoEvent(void)
{
    struct Event ev;
    int dy;
    int dx;

    if (g_2D3A) return 0;
    g_2D3A = 1;
    win_NoWindowsShouldBeLocked();
    if (ui_pending_menu_item) {
        switch (ui_pending_menu_item) {
        case MENU_CMD_LOAD:
            if (LoadGame(0L) == 0 && CurGameType == -1 && NewGame(1) < 0)
                MenuQuit();
            break;
        case MENU_CMD_SAVE:
            SaveGame(1);
            break;
        case MENU_CMD_SAVE_AS:
            SaveGame(0);
            break;
        case MENU_CMD_QUIT:
            MenuQuit();
            break;
        }
        ui_pending_menu_item = 0;
    }
    if (win_Events()) {
        win_GetEvent(&ev);
        win_close_auto_dismiss();
        WinPrintf("\nEVENT=%x", ev.code);
        switch (ev.code & WIN_ID_MASK) {
        case WIN_EDIT:
            ProcEditEvent(&ev);
            break;
        case WIN_MAP:
            ProcMapEvent(&ev);
            break;
        case WIN_INFO:
            ProcInfoEvent(&ev);
            break;
        case WIN_BEHAVIOR:
            ProcModeEvent(&ev);
            break;
        case WIN_CASTE:
            ProcCasteEvent(&ev);
            break;
        case WIN_HISTORY:
            ProcHistoryEvent(&ev);
            break;
        case WIN_YARD:
            ProcYardEvent(&ev);
            break;
        case EVENT_KEY_SCAN_BASE:
            input_translate_special_key(&ev);
            break;
        case EVENT_MENU_COMMAND_BASE:
            ProcMenu(&ev);
            break;
        case EVENT_MENU_BAR_BASE:
            input_capture_screen();
            (*g_9130)();
            menu_track_bar_selection(&ev);
            font_SetFont(0);
            input_release_screen_capture();
            break;
        }
    }
    while (kbd_scan_state(0x1d)) {
        dx = dy = 0;
        if (kbd_scan_state(0x47))
            dy = dx = -1;
        if (kbd_scan_state(0x49)) {
            dx++;
            dy--;
        }
        if (kbd_scan_state(0x4f)) {
            dx--;
            dy++;
        }
        if (kbd_scan_state(0x51)) {
            dx++;
            dy++;
        }
        if (kbd_scan_state(0x4d))
            dx++;
        if (kbd_scan_state(0x4b))
            dx--;
        if (kbd_scan_state(0x48))
            dy--;
        if (kbd_scan_state(0x50))
            dy++;
        if ((dx == 0 && dy == 0) || !edit_scroll_and_redraw(dx, dy))
            break;
    }
    if (kbd_poll_bios_key())
        input_dispatch_game_key();
    g_2D3A = 0;
}

extern int far kbd_read_key_code(void);
extern void far CheatKeys(int key);
void far ui_show_memory_statistics(void);
extern void far mem_dump_heap(char far *where);
extern void far mem_discard_soft_blocks(void);
extern char far * far version_message_pointer;
extern void far ui_message_transient(char far *msg);
extern void far input_enqueue_event_args();
extern int far YellowCommandKey(int key);

void far input_dispatch_game_key(void)
{
    int key;
    int i;

    key = kbd_read_key_code();
    CheatKeys(key);
    if (kbd_scan_state(0x1d)) {
        switch (key) {
        case 0x817:
            ui_show_memory_statistics();
            return;
        case 0x821:
            WinPrintf("FLUSH");
            mem_discard_soft_blocks();
            return;
        case 0x820:
            mem_dump_heap("User Request");
            return;
        case 0x82f:
            ui_message_transient(version_message_pointer);
            return;
        }
    }
    WinPrintf("\nKeypress=%x", key);
    for (i = 0; g_2CBE[i].key; i++)
        if (g_2CBE[i].key == key) {
            input_enqueue_event_args(g_2CBE[i].cmd, 0, 0, 0);
            break;
        }
    if (g_2CBE[i].key == 0) {
        WinPrintf("\nCOMMAND KEY:%c", key);
        YellowCommandKey(key);
    }
}

extern long far RallocMemoryFree(void);
extern long far RallocMemorySoft(void);
extern long far startup_free_memory_bytes;
extern int far sprintf(char far *buf, const char far *fmt, ...);

/*
 * Show startup, free, discardable and total available memory in bytes.
 */
void far ui_show_memory_statistics(void)
{
    char buf[200];

    sprintf(buf, "%ld bytes @ startup\n %ld bytes free now\n %ld bytes discardable stuff\n %ld AVAILABLE",
            startup_free_memory_bytes, RallocMemoryFree(), RallocMemorySoft(), RallocMemoryFree() + RallocMemorySoft());
    ui_message_transient(buf);
}

extern void far YardToMap(void);
extern void far YellowCommand(int cmd);
extern void far DoTab(void);

void far input_translate_special_key(struct Event far *ev)
{
    int cmd;

    WinPrintf("\nKEYEVENT=%x, %x", ev->code, ev->bios_shift_flags);
    if (ev->bios_shift_flags & 4) {
        switch (ev->code) {
        case EVENT_SCAN_PATCH_SHORTCUT:
            YardToMap();
            return;
        case EVENT_SCAN_HOUSE_SHORTCUT:
            cmd = EVENT_MENU_HOUSE;
            break;
        case EVENT_SCAN_STRATEGIC_SHORTCUT:
            cmd = EVENT_MENU_STRATEGIC;
            break;
        case EVENT_SCAN_GRAPHIC_SHORTCUT:
            cmd = EVENT_MENU_GRAPHIC;
            break;
        case EVENT_SCAN_SURFACE_SHORTCUT:
            cmd = EVENT_MENU_SURFACE;
            break;
        case EVENT_SCAN_BLACK_NEST_SHORTCUT:
            cmd = EVENT_MENU_BLACK_NEST;
            break;
        case EVENT_SCAN_RED_NEST_SHORTCUT:
            cmd = EVENT_MENU_RED_NEST;
            break;
        case EVENT_SCAN_INFO_SHORTCUT:
            cmd = EVENT_MENU_INFO;
            break;
        case EVENT_SCAN_HISTORY_SHORTCUT:
            cmd = EVENT_MENU_HISTORY;
            break;
        default:
            return;
        }
        input_enqueue_event_args(cmd, 0, 0, 0, 0);
    } else if (ev->bios_shift_flags & 8) {
        switch (ev->code) {
        case EVENT_SCAN_RECRUIT_THOUSAND_SHORTCUT:
            YellowCommand(3);
            break;
        }
    } else {
        switch (ev->code) {
        case 0xfa0e:
            YellowCommandKey(0x88);
            break;
        case EVENT_SCAN_TAB_SHORTCUT:
            DoTab();
            break;
        }
    }
}
