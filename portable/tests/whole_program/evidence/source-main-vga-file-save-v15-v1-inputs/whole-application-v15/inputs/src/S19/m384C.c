/* Overlay section S19, code frame 384C: the main event pump, key commands and the
 * debug memory report. */

struct Event {
    int what;
    int message;
    int x4;
    int x6;
    int h;
    int v;
    int code;
    int xE;
};

struct KeyCmd {
    int key;
    int cmd;
};

char fd_55B3_2CBA = 0;
int fd_55B3_2CBC = 0;
struct KeyCmd g_2CBE[] = {
    { 0x821, 0xfe00 }, { 0x811, 0xfe01 }, { 0x82f, 0xfe02 }, { 0x818, 0xfe03 },
    { 0x81f, 0xfe04 }, { 0x83c, 0xfe00 }, { 0x83d, 0xfe01 }, { 0x83e, 0xfe02 },
    { 0x83f, 0xfe03 }, { 0x840, 0xfe04 }, { 0x29, 0xfd41 }, { 0x21, 0xfd43 },
    { 0x40, 0xfd44 }, { 0x23, 0xfd45 }, { 0x24, 0xfd46 }, { 0x0e, 0xfd03 },
    { 0x13, 0xfd05 }, { 0x01, 0xfd06 }, { 0x0c, 0xfd04 }, { 0x05, 0xfd11 },
    { 0x0d, 0xfd12 }, { 0x02, 0xfd13 }, { 0x03, 0xfd14 }, { 0x14, 0xfd17 },
    { 0x07, 0xfd31 }, { 0x0a, 0xfd32 }, { 0x0b, 0xfd33 }, { 0x18, 0xfd08 },
    { 0x11, 0xfd08 }, { 0x19, 0xfd21 }, { 0, 0 }
};
int g_2D3A = 0;

extern void far win_NoWindowsShouldBeLocked(void);
extern int far LoadGame(char far *name);
extern int far fd_50F6_0EAC;
extern int far NewGame(int a);
extern void far MenuQuit(void);
extern int far o09_35F5_0188(int useLast);
extern int far win_Events(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern void far f_20E8_0A21(void);
extern int far WinPrintf(char far *format, ...);
extern void far ProcEditEvent(struct Event far *ev);
extern void far ProcMapEvent(struct Event far *ev);
extern void far ProcInfoEvent(struct Event far *ev);
extern void far ProcModeEvent(struct Event far *ev);
extern void far ProcCasteEvent(struct Event far *ev);
void far o19_384C_0383(struct Event far *ev);
extern void far ProcMenu(struct Event far *ev);
extern void far f_1FD2_02FF(void);
extern void (far * near g_9130)(void);
extern int far o10_35F5_01C3(struct Event far *ev);
extern void far f_24AB_02AD(int font);
extern void far f_1FD2_031A(void);
extern int far f_1B73_0A30(int key);
extern int far f_0250_0D10(int dx, int dy);
extern int far f_1F58_0038(void);
void far o19_384C_0246(void);

int far o19_384C_0000(void)
{
    struct Event ev;
    int dy;
    int dx;

    if (g_2D3A) return 0;
    g_2D3A = 1;
    win_NoWindowsShouldBeLocked();
    if (fd_55B3_2CBC) {
        switch (fd_55B3_2CBC) {
        case 4:
            if (LoadGame(0L) == 0 && fd_50F6_0EAC == -1 && NewGame(1) < 0)
                MenuQuit();
            break;
        case 5:
            o09_35F5_0188(1);
            break;
        case 6:
            o09_35F5_0188(0);
            break;
        case 8:
            MenuQuit();
            break;
        }
        fd_55B3_2CBC = 0;
    }
    if (win_Events()) {
        win_GetEvent(&ev);
        f_20E8_0A21();
        WinPrintf("\nEVENT=%x", ev.code);
        switch (ev.code & 0xff00) {
        case 0:
            ProcEditEvent(&ev);
            break;
        case 0x100:
            ProcMapEvent(&ev);
            break;
        case 0x500:
            ProcInfoEvent(&ev);
            break;
        case 0x1200:
            ProcModeEvent(&ev);
            break;
        case 0x1300:
            ProcCasteEvent(&ev);
            break;
        case 0x1500:
            ProcHistoryEvent(&ev);
            break;
        case 0x1900:
            ProcYardEvent(&ev);
            break;
        case 0xfa00:
            o19_384C_0383(&ev);
            break;
        case 0xfd00:
            ProcMenu(&ev);
            break;
        case 0xfe00:
            f_1FD2_02FF();
            (*g_9130)();
            o10_35F5_01C3(&ev);
            f_24AB_02AD(0);
            f_1FD2_031A();
            break;
        }
    }
    while (f_1B73_0A30(0x1d)) {
        dx = dy = 0;
        if (f_1B73_0A30(0x47))
            dy = dx = -1;
        if (f_1B73_0A30(0x49)) {
            dx++;
            dy--;
        }
        if (f_1B73_0A30(0x4f)) {
            dx--;
            dy++;
        }
        if (f_1B73_0A30(0x51)) {
            dx++;
            dy++;
        }
        if (f_1B73_0A30(0x4d))
            dx++;
        if (f_1B73_0A30(0x4b))
            dx--;
        if (f_1B73_0A30(0x48))
            dy--;
        if (f_1B73_0A30(0x50))
            dy++;
        if ((dx == 0 && dy == 0) || !f_0250_0D10(dx, dy))
            break;
    }
    if (f_1F58_0038())
        o19_384C_0246();
    g_2D3A = 0;
}

extern int far f_1F58_0090(void);
extern void far CheatKeys(int key);
void far o19_384C_0320(void);
extern void far f_171C_030C(char far *where);
extern void far f_171C_1EFA(void);
extern char far * far fd_55B3_0064;
extern void far f_1C62_00C0(char far *msg);
extern void far f_1B73_030F();
extern int far YellowCommandKey(int key);

void far o19_384C_0246(void)
{
    int key;
    int i;

    key = f_1F58_0090();
    CheatKeys(key);
    if (f_1B73_0A30(0x1d)) {
        switch (key) {
        case 0x817:
            o19_384C_0320();
            return;
        case 0x821:
            WinPrintf("FLUSH");
            f_171C_1EFA();
            return;
        case 0x820:
            f_171C_030C("User Request");
            return;
        case 0x82f:
            f_1C62_00C0(fd_55B3_0064);
            return;
        }
    }
    WinPrintf("\nKeypress=%x", key);
    for (i = 0; g_2CBE[i].key; i++)
        if (g_2CBE[i].key == key) {
            f_1B73_030F(g_2CBE[i].cmd, 0, 0, 0);
            break;
        }
    if (g_2CBE[i].key == 0) {
        WinPrintf("\nCOMMAND KEY:%c", key);
        YellowCommandKey(key);
    }
}

extern long far f_171C_1750(void);
extern long far f_171C_1772(void);
extern long far fd_50F6_3944;
extern int far sprintf(char far *buf, const char far *fmt, ...);

void far o19_384C_0320(void)
{
    char buf[200];

    sprintf(buf, "%ld bytes @ startup\n %ld bytes free now\n %ld bytes discardable stuff\n %ld AVAILABLE",
            fd_50F6_3944, f_171C_1750(), f_171C_1772(), f_171C_1750() + f_171C_1772());
    f_1C62_00C0(buf);
}

extern void far YardToMap(void);
extern void far YellowCommand(int cmd);
extern void far DoTab(void);

void far o19_384C_0383(struct Event far *ev)
{
    int cmd;

    WinPrintf("\nKEYEVENT=%x, %x", ev->code, ev->message);
    if (ev->message & 4) {
        switch (ev->code) {
        case 0xfa05:
            YardToMap();
            return;
        case 0xfa06:
            cmd = 0xfd22;
            break;
        case 0xfa07:
            cmd = 0xfd23;
            break;
        case 0xfa08:
            cmd = 0xfd24;
            break;
        case 0xfa09:
            cmd = 0xfd26;
            break;
        case 0xfa0a:
            cmd = 0xfd27;
            break;
        case 0xfa0b:
            cmd = 0xfd28;
            break;
        case 0xfa17:
            cmd = 0xfd16;
            break;
        case 0xfa23:
            cmd = 0xfd15;
            break;
        default:
            return;
        }
        f_1B73_030F(cmd, 0, 0, 0, 0);
    } else if (ev->message & 8) {
        switch (ev->code) {
        case 0xfa03:
            YellowCommand(3);
            break;
        }
    } else {
        switch (ev->code) {
        case 0xfa0e:
            YellowCommandKey(0x88);
            break;
        case 0xfa0f:
            DoTab();
            break;
        }
    }
}
