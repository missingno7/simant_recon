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
extern void far f_0250_0EDA(int flags);
extern void far o12_384C_1035(int flags);
extern void far win_DrawHistoryWindow(int flags);
extern void far win_DrawModeWindow(int flags);
extern void far win_DrawCasteWindow(int flags);
extern void far win_DrawYardWindow(int flags);
extern void far win_DrawInfoWindow(int flags);
extern void _fastcall f_20E8_088B(void (far *hook)(void));
void far f_00BA_0228(void);
extern void _fastcall f_20E8_08DB(void (far *hook)(int item));
void far f_00BA_01C3(int item);
extern void _fastcall f_20E8_089F(void (far *hook)(void));
void far f_00BA_0211(void);
extern void far f_22BF_0E83(int, int);
extern void far InitMapFunctions(void);
extern int far fd_50F6_10D0;
extern long far lseek(int fh, long pos, int origin);
extern int far read(int fh, void far *buf, unsigned int count);
extern Handle far f_171C_1A9E(long size, int flags, char far *name);
extern char far * far f_171C_1B84(Handle h);
extern Handle far f_171C_1BBA(Handle h);
extern void far f_171C_1C0A(Handle h);
extern Handle far fd_50F6_10CC;

void far f_00BA_0002(void)
{
    int far *fh;
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
    fh = &fd_50F6_10D0;
    if (*fh == 0)
        return;
    lseek(*fh, 0L, 0);
    read(*fh, &hdr, sizeof hdr);
    lseek(*fh, hdr.headers + sizeof hdr, 0);
    h = f_171C_1A9E(0x100L, 1, "winheaders");
    n = read(*fh, f_171C_1B84(h), 0x100);
    read(*fh, f_171C_1B84(h), 1);
    f_171C_1BBA(h);
    f_171C_1BBA(h);
    if (n != 0x100)
        f_171C_1C0A(h);
    else
        fd_50F6_10CC = h;
}

extern void far initStuff(void);

void far f_00BA_01B6(void)
{
    initStuff();
}

extern void far win_CasteControlChanged(void);
extern void far win_ModeControlChanged(void);
extern void far f_0250_0E15(void);
extern void far f_00F8_00A4(void);
extern void far f_00F8_0002(void);

void far f_00BA_01C3(int item)
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
    f_0250_0E15();
    f_00F8_00A4();
    f_00F8_0002();
}
