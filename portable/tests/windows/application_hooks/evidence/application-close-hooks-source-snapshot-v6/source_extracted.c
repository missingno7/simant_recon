#include <stdint.h>
#include <string.h>
#include "recovered_state.h"

#define far
#define _fastcall
#define g_19BE fd_55B3_19BE
#define g_19C0 fd_55B3_19C0
#define g_19CE source_g_19CE
#define f_00F8_0002 win_YardClosed
#define f_00F8_00A4 win_MapChanged
#define fd_50F6_0508 (*((struct Pt *)(void *)&fd_50F6_0508[0]))

typedef void *Handle;
struct WinFileHeader { int16_t x0, x2, x4; int32_t headers; int16_t xA, xC; };

extern int16_t fd_50F6_10D0;
extern void *fd_50F6_10CC;
extern void *fd_50F6_10DA;
extern int16_t fd_50F6_15C4[30][40];
extern int16_t source_g_19CE;

extern int16_t win_LoadAllWindows(void);
extern void win_SetWinDrawHook(int16_t, void (*)(int16_t));
extern void f_20E8_088B(void (*)(void));
extern void f_20E8_08DB(void (*)(int16_t));
extern void f_20E8_089F(void (*)(void));
extern void f_22BF_0E83(int16_t, int16_t);
extern void InitMapFunctions(void);
extern Handle f_171C_1A9E(int32_t, int16_t, char *);
extern char *f_171C_1B84(Handle);
extern Handle f_171C_1BBA(Handle);
extern void f_171C_1C0A(Handle);
extern long lseek(int16_t, int32_t, int16_t);
extern int16_t read(int16_t, void *, uint16_t);

extern void f_0250_0EDA(int16_t);
extern void o12_384C_1035(int16_t);
extern void win_DrawHistoryWindow(int16_t);
extern void win_DrawModeWindow(int16_t);
extern void win_DrawCasteWindow(int16_t);
extern void win_DrawYardWindow(int16_t);
extern void win_DrawInfoWindow(int16_t);
extern void f_00BA_01C3(int16_t);

extern void clip_Push(void);
extern void clip_SetWin(int16_t);
extern void clip_Pop(void);
extern void hanim_RemoveAllAnimObjects(Handle);
extern void hanim_RenderAnimSet(Handle);
extern void hanim_RemoveAnimSet(Handle);
extern int16_t win_IsWinOpen(int16_t);
extern void win_GetObjRect(int16_t, struct Rect *);
extern void EraseYardCursor(void);
extern void EraseMapCursor(void);
extern void *_fmemset(void *, int16_t, uint16_t);
extern void f_00BA_0002(void);
extern void f_00BA_0211(void);
extern void f_00BA_0228(void);
extern void win_YardClosed(void);
extern void win_MapChanged(void);
extern void f_0250_05CB(void);
extern void f_0250_0E15(void);
extern void f_0250_0F2C(void);
extern void win_ModeControlClosed(void);
extern void win_CasteControlClosed(void);

/* Extracted verbatim: src/root/m00BA.c:42-75; source SHA-256 d72629d827e2bccd7557566b725f652862d2b1199f40390361179c61cc9ff5dc */
void far f_00BA_0002(void)
{
    struct WinFileHeader hdr;
    Handle h;
    int n;

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
    lseek(fd_50F6_10D0, 0L, 0);
    read(fd_50F6_10D0, &hdr, sizeof hdr);
    lseek(fd_50F6_10D0, hdr.headers + sizeof hdr, 0);
    h = f_171C_1A9E(0x100UL, 1, "winheaders");
    n = read(fd_50F6_10D0, f_171C_1B84(h), 0x100);
    read(fd_50F6_10D0, f_171C_1B84(h), 1);
    f_171C_1BBA(h);
    f_171C_1BBA(h);
    if (n != 0x100)
        f_171C_1C0A(h);
    else
        fd_50F6_10CC = h;
}

/* Extracted verbatim: src/root/m00BA.c:110-115; source SHA-256 d72629d827e2bccd7557566b725f652862d2b1199f40390361179c61cc9ff5dc */
void far f_00BA_0211(void)
{
    f_00F8_0002();
    win_ModeControlClosed();
    win_CasteControlClosed();
}

/* Extracted verbatim: src/root/m00BA.c:117-124; source SHA-256 d72629d827e2bccd7557566b725f652862d2b1199f40390361179c61cc9ff5dc */
void far f_00BA_0228(void)
{
    win_CasteControlClosed();
    win_ModeControlClosed();
    f_0250_0E15();
    f_00F8_00A4();
    f_00F8_0002();
}

/* Extracted verbatim: src/root/m00F8.c:29-45; source SHA-256 4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a */
void far win_YardClosed(void)
{
    if (fd_50F6_10DA) {
        clip_Push();
        clip_SetWin(0x1900);
        hanim_RemoveAllAnimObjects(fd_50F6_10DA);
        hanim_RenderAnimSet(fd_50F6_10DA);
        hanim_RemoveAnimSet(fd_50F6_10DA);
        clip_Pop();
        fd_50F6_10DA = 0;
    }
    if (win_IsWinOpen(0x1902)) {
        win_GetObjRect(0x1902, &fd_50F6_10D2);
        fd_50F6_10D2.left++;
        EraseYardCursor();
    }
}

/* Extracted verbatim: src/root/m00F8.c:50-57; source SHA-256 4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a */
void far win_MapChanged(void)
{
    if (win_IsWinOpen(0x100)) {
        EraseMapCursor();
        win_GetObjRect(0x102, &fd_50F6_10D2);
        fd_55B3_29A2 = 1;
    }
}

/* Extracted verbatim: src/root/m0250.c:249-252; source SHA-256 bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b */
void far f_0250_05CB(void)
{
    _fmemset(fd_50F6_15C4, -1, 0x960);
}

/* Extracted verbatim: src/root/m0250.c:594-602; source SHA-256 bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b */
void far f_0250_0E15(void)
{
    win_GetObjRect(4, &fd_50F6_110C);
    fd_50F6_10E0 = (fd_50F6_110C.right - fd_50F6_110C.left) / g_19BE;
    fd_50F6_10DE = (fd_50F6_110C.bottom - fd_50F6_110C.top) / g_19C0 + 1;
    f_0250_05CB();
    g_19CE = 1;
    f_0250_0F2C();
}

/* Extracted verbatim: src/root/m0250.c:669-691; source SHA-256 bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b */
void far f_0250_0F2C(void)
{
    int limit;
    int ylimit;

    ylimit = 0x40;
    switch (MapPlane) {
    case 0:
    case 1:
        limit = 0x80;
        break;
    default:
        limit = 0x40;
    }
    if (fd_50F6_0508.x < 0)
        fd_50F6_0508.x = 0;
    else if (fd_50F6_0508.x + fd_50F6_10E0 > limit)
        fd_50F6_0508.x = limit - fd_50F6_10E0;
    if (fd_50F6_0508.y < 0)
        fd_50F6_0508.y = 0;
    else if (fd_50F6_0508.y + fd_50F6_10DE > ylimit)
        fd_50F6_0508.y = ylimit - fd_50F6_10DE;
}

/* Extracted verbatim: src/root/m0798.c:352-358; source SHA-256 ecf807dc3159f583f6ee3ea8a9f5422650a64bb557d4551e9c97b5dcc7b6a1b8 */
void far win_ModeControlClosed(void)
{
    if (fd_50F6_37F6) {
        hanim_RemoveAnimSet(fd_50F6_37F6);
        fd_50F6_37F6 = 0;
    }
}

/* Extracted verbatim: src/root/m0798.c:383-389; source SHA-256 ecf807dc3159f583f6ee3ea8a9f5422650a64bb557d4551e9c97b5dcc7b6a1b8 */
void far win_CasteControlClosed(void)
{
    if (fd_50F6_37F2) {
        hanim_RemoveAnimSet(fd_50F6_37F2);
        fd_50F6_37F2 = 0;
    }
}
