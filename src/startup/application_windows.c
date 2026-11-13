/*
 * Initializes application windows and installs drawing and control hooks. It loads saved window
 * headers and handles window closure or control changes.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 00BA; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory.
 */

#include "windows_ids.h"

typedef char far * far *Handle;

struct WinFileHeader {
    int x0;
    int x2;
    int x4;
    long headers;
    int xA;
    int xC;
};

extern int far win_LoadAllWindows(void);
extern void _fastcall win_SetWinDrawHook(int win, void (far *hook)(int flags));
extern void far win_DrawEditWindow(int flags);
extern void far win_DrawMapWindow(int flags);
extern void far win_DrawHistoryWindow(int flags);
extern void far win_DrawModeWindow(int flags);
extern void far win_DrawCasteWindow(int flags);
extern void far win_DrawYardWindow(int flags);
extern void far win_DrawInfoWindow(int flags);
extern void _fastcall win_set_state_change_hook(void (far *hook)(void));
void far app_window_state_changed(void);
extern void _fastcall win_set_layout_change_hook(void (far *hook)(int item));
void far app_window_layout_changed(int item);
extern void _fastcall win_set_before_close_hook(void (far *hook)(void));
void far app_before_window_close(void);
extern void far win_copy_obj_layout_origin(int, int);
extern void far InitMapFunctions(void);
extern int far startup_executable_fd;
/* read() and lseek() are called without prototypes (no <io.h>): with the MSC prototype
   (unsigned count) the 0x100 size argument of mem_Alloc is pushed as mov ax,100h; cwd
   instead of the original mov cx,100h; sub dx,dx (PROTO-1 family, worker resG). */
extern Handle far mem_Alloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern Handle far mem_Unlock(Handle h);
extern void far mem_Free(Handle h);
extern Handle far startup_info_block_handle;

void far InitApplicationWindows(void)
{
    struct WinFileHeader hdr;
    Handle h;
    int n;

    win_LoadAllWindows();
    win_SetWinDrawHook(WIN_EDIT, win_DrawEditWindow);
    win_SetWinDrawHook(WIN_MAP, win_DrawMapWindow);
    win_SetWinDrawHook(WIN_HISTORY, win_DrawHistoryWindow);
    win_SetWinDrawHook(WIN_BEHAVIOR, win_DrawModeWindow);
    win_SetWinDrawHook(WIN_CASTE, win_DrawCasteWindow);
    win_SetWinDrawHook(WIN_YARD, win_DrawYardWindow);
    win_SetWinDrawHook(WIN_INFO, win_DrawInfoWindow);
    win_set_state_change_hook(app_window_state_changed);
    win_set_layout_change_hook(app_window_layout_changed);
    win_set_before_close_hook(app_before_window_close);
    win_copy_obj_layout_origin(WIN_YARD, WIN_MAP);
    InitMapFunctions();
    if (startup_executable_fd == 0)
        return;
    lseek(startup_executable_fd, 0L, 0);
    read(startup_executable_fd, &hdr, sizeof hdr);
    lseek(startup_executable_fd, hdr.headers + sizeof hdr, 0);
    h = mem_Alloc(0x100UL, 1, "winheaders");
    n = read(startup_executable_fd, mem_Lock(h), 0x100);
    read(startup_executable_fd, mem_Lock(h), 1);
    mem_Unlock(h);
    mem_Unlock(h);
    if (n != 0x100)
        mem_Free(h);
    else
        startup_info_block_handle = h;
}

extern void far initStuff(void);

void far InitApplicationStuff(void)
{
    initStuff();
}

extern void far win_CasteControlChanged(void);
extern void far win_ModeControlChanged(void);
extern void far win_EditChanged(void);
extern void far f_00F8_00A4(void);
extern void far f_00F8_0002(void);

/*
 * Mirror map/yard window origins and notify dependent views after layout changes.
 */
void far app_window_layout_changed(int item)
{
    switch (item) {
    case WIN_MAP:
        win_copy_obj_layout_origin(WIN_MAP, WIN_YARD);
        break;
    case WIN_YARD:
        win_copy_obj_layout_origin(WIN_YARD, WIN_MAP);
        break;
    }
    win_CasteControlChanged();
    win_ModeControlChanged();
    win_EditChanged();
    f_00F8_00A4();
    f_00F8_0002();
}

extern void far win_ModeControlClosed(void);
extern void far win_CasteControlClosed(void);

/*
 * Run yard and control-window cleanup before a window closes.
 */
void far app_before_window_close(void)
{
    f_00F8_0002();
    win_ModeControlClosed();
    win_CasteControlClosed();
}

/*
 * Refresh control and view state through the application window-state hook.
 */
void far app_window_state_changed(void)
{
    win_CasteControlClosed();
    win_ModeControlClosed();
    win_EditChanged();
    f_00F8_00A4();
    f_00F8_0002();
}
