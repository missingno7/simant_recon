#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/state/game_views.h"
#pragma pack(push, 2)
/* Root module 00BA: application window setup (draw hooks, saved window headers)
 * and the window-close/control-change hooks. */

typedef char  *  *Handle;

struct WinFileHeader {
    int16_t x0;
    int16_t x2;
    int16_t x4;
    int32_t headers;
    int16_t xA;
    int16_t xC;
};

extern int16_t  win_LoadAllWindows(void);
extern void  win_SetWinDrawHook(int16_t win, void ( *hook)(int16_t flags));
extern void  f_0250_0EDA(int16_t flags);
extern void  o12_384C_1035(int16_t flags);
extern void  win_DrawHistoryWindow(int16_t flags);
extern void  win_DrawModeWindow(int16_t flags);
extern void  win_DrawCasteWindow(int16_t flags);
extern void  win_DrawYardWindow(int16_t flags);
extern void  win_DrawInfoWindow(int16_t flags);
extern void  f_20E8_088B(void ( *hook)(void));
void  f_00BA_0228(void);
extern void  f_20E8_08DB(void ( *hook)(int16_t item));
void  f_00BA_01C3(int16_t item);
extern void  f_20E8_089F(void ( *hook)(void));
void  f_00BA_0211(void);
extern void  f_22BF_0E83(int16_t, int16_t);
extern void  InitMapFunctions(void);
extern int16_t  fd_50F6_10D0;
/* read() and lseek() are called without prototypes (no <io.h>): with the MSC prototype
   (unsigned count) the 0x100 size argument of f_171C_1A9E is pushed as mov ax,100h; cwd
   instead of the original mov cx,100h; sub dx,dx (PROTO-1 family, worker resG). */
extern Handle  f_171C_1A9E(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(Handle h);
extern Handle  f_171C_1BBA(Handle h);
extern void  f_171C_1C0A(Handle h);

void  f_00BA_0002(void)
{
    struct WinFileHeader hdr;
    Handle h;
    int16_t n;

    win_LoadAllWindows();
    win_SetWinDrawHook(0, f_0250_0EDA);
    win_SetWinDrawHook(0x100, o12_384C_1035);
    win_SetWinDrawHook(0x1500, win_DrawHistoryWindow);
    win_SetWinDrawHook(0x1200, win_DrawModeWindow);
    win_SetWinDrawHook(0x1300, win_DrawCasteWindow);
    win_SetWinDrawHook(0x1900, win_DrawYardWindow);
    win_SetWinDrawHook(0x500, win_DrawInfoWindow);
    f_20E8_088B(f_00BA_0228);
    f_20E8_08DB(f_00BA_01C3);
    f_20E8_089F(f_00BA_0211);
    f_22BF_0E83(0x1900, 0x100);
    InitMapFunctions();
    if (fd_50F6_10D0 == 0)
        return;
    dos_lseek(fd_50F6_10D0, 0L, 0);
    dos_read(fd_50F6_10D0, &hdr, sizeof hdr);
    dos_lseek(fd_50F6_10D0, hdr.headers + sizeof hdr, 0);
    h = f_171C_1A9E(0x100UL, 1, "winheaders");
    n = dos_read(fd_50F6_10D0, f_171C_1B84(h), 0x100);
    dos_read(fd_50F6_10D0, f_171C_1B84(h), 1);
    f_171C_1BBA(h);
    f_171C_1BBA(h);
    if (n != 0x100)
        f_171C_1C0A(h);
    else
        native_game_fd_50F6_10CC[0] = h;
}

extern void  initStuff(void);

void  f_00BA_01B6(void)
{
    initStuff();
}

extern void  win_CasteControlChanged(void);
extern void  win_ModeControlChanged(void);
extern void  f_0250_0E15(void);
extern void  win_MapChanged(void);
extern void  win_YardClosed(void);

void  f_00BA_01C3(int16_t item)
{
    switch (item) {
    case 0x100:
        f_22BF_0E83(0x100, 0x1900);
        break;
    case 0x1900:
        f_22BF_0E83(0x1900, 0x100);
        break;
    }
    win_CasteControlChanged();
    win_ModeControlChanged();
    f_0250_0E15();
    win_MapChanged();
    win_YardClosed();
}

extern void  win_ModeControlClosed(void);
extern void  win_CasteControlClosed(void);

void  f_00BA_0211(void)
{
    win_YardClosed();
    win_ModeControlClosed();
    win_CasteControlClosed();
}

void  f_00BA_0228(void)
{
    win_CasteControlClosed();
    win_ModeControlClosed();
    f_0250_0E15();
    win_MapChanged();
    win_YardClosed();
}

#pragma pack(pop)
