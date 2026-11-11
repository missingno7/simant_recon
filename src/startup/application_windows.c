/* Root module 00BA: application window setup (draw hooks, saved window headers)
 * and the window-close/control-change hooks. */

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
void far f_00BA_0228(void);
extern void _fastcall win_set_layout_change_hook(void (far *hook)(int item));
void far f_00BA_01C3(int item);
extern void _fastcall win_set_before_close_hook(void (far *hook)(void));
void far f_00BA_0211(void);
extern void far win_copy_obj_layout_origin(int, int);
extern void far InitMapFunctions(void);
extern int far fd_50F6_10D0;
/* read() and lseek() are called without prototypes (no <io.h>): with the MSC prototype
   (unsigned count) the 0x100 size argument of mem_Alloc is pushed as mov ax,100h; cwd
   instead of the original mov cx,100h; sub dx,dx (PROTO-1 family, worker resG). */
extern Handle far mem_Alloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern Handle far mem_Unlock(Handle h);
extern void far mem_Free(Handle h);
extern Handle far fd_50F6_10CC;

void far InitApplicationWindows(void)
{
    struct WinFileHeader hdr;
    Handle h;
    int n;

    win_LoadAllWindows();
    win_SetWinDrawHook(0, win_DrawEditWindow);
    win_SetWinDrawHook(0x100, win_DrawMapWindow);
    win_SetWinDrawHook(0x1500, win_DrawHistoryWindow);
    win_SetWinDrawHook(0x1200, win_DrawModeWindow);
    win_SetWinDrawHook(0x1300, win_DrawCasteWindow);
    win_SetWinDrawHook(0x1900, win_DrawYardWindow);
    win_SetWinDrawHook(0x500, win_DrawInfoWindow);
    win_set_state_change_hook(f_00BA_0228);
    win_set_layout_change_hook(f_00BA_01C3);
    win_set_before_close_hook(f_00BA_0211);
    win_copy_obj_layout_origin(0x1900, 0x100);
    InitMapFunctions();
    if (fd_50F6_10D0 == 0)
        return;
    lseek(fd_50F6_10D0, 0L, 0);
    read(fd_50F6_10D0, &hdr, sizeof hdr);
    lseek(fd_50F6_10D0, hdr.headers + sizeof hdr, 0);
    h = mem_Alloc(0x100UL, 1, "winheaders");
    n = read(fd_50F6_10D0, mem_Lock(h), 0x100);
    read(fd_50F6_10D0, mem_Lock(h), 1);
    mem_Unlock(h);
    mem_Unlock(h);
    if (n != 0x100)
        mem_Free(h);
    else
        fd_50F6_10CC = h;
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

void far f_00BA_01C3(int item)
{
    switch (item) {
    case 0x100:
        win_copy_obj_layout_origin(0x100, 0x1900);
        break;
    case 0x1900:
        win_copy_obj_layout_origin(0x1900, 0x100);
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

void far f_00BA_0211(void)
{
    f_00F8_0002();
    win_ModeControlClosed();
    win_CasteControlClosed();
}

void far f_00BA_0228(void)
{
    win_CasteControlClosed();
    win_ModeControlClosed();
    win_EditChanged();
    f_00F8_00A4();
    f_00F8_0002();
}
