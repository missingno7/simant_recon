/* Overlay section S24, code frame 39C7: history graph window (Win16 SIMANT_MODULE OpenHistoryWindow..HistUpdate). */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    unsigned code;
    int xE;
};

extern void far win_Open();

void far OpenHistoryWindow(void)
{
    win_Open(0x1500);
}

static int graphColors[4] = { 0x43, 0x46, 0x49, 0x45 };
static int shownGraphs[4] = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };
static int freeColors = 0x0f;
static int histColor[20];
static char histShown[10];

extern void far DoWinHelp(int topic);
void far ToggleHistButton(int item);
extern void far clip_SetWin(int win);
extern int far f_1B4E_000D(int color);
extern void _fastcall win_FillObjRect(int obj, int color);
void far drawHistGraph(int graph, int hilite, int slot);
extern int far f_1FD2_0542(void);
void far win_DrawHistoryWindow(int flags);
extern void far f_1E57_0362(void);

void far ProcHistoryEvent(struct Event far *ev)
{
    int i;

    switch (ev->code) {
    case 0x150d:
        DoWinHelp(0x150f);
        break;
    case 0x150e:
        clip_SetWin(0x1500);
        win_FillObjRect(0x150e, f_1B4E_000D(0));
        for (i = 0; i < 4; i++)
            if (shownGraphs[i] != (int)0x8000)
                drawHistGraph(shownGraphs[i], 1, i);
        while (f_1FD2_0542())
            ;
        win_DrawHistoryWindow(3);
        f_1E57_0362();
        break;
    default:
        if (ev->code >= 0x1503 && ev->code <= 0x150c)
            ToggleHistButton(ev->code);
        break;
    }
}

extern void far * far _fmemmove(void far *dst, void far *src, unsigned n);
extern void _fastcall win_MakeObjUnselected(int obj);

void far ToggleHistButton(int item)
{
    int i;
    int g;
    int c;
    int bit;

    clip_SetWin(0x1500);
    g = item - 0x1503;
    if (histShown[g]) {
        for (i = 0; i < 4; i++)
            if (shownGraphs[i] == g) {
                _fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (4 - i) * 2);
                shownGraphs[3] = (int)0x8000;
                break;
            }
        histShown[g] = 0;
        freeColors |= 1 << histColor[g];
    } else {
        histShown[g] = 1;
        if ((i = shownGraphs[3]) != (int)0x8000) {
            histShown[i] = 0;
            win_MakeObjUnselected(i + 0x1503);
            freeColors |= 1 << histColor[i];
        }
        _fmemmove(&shownGraphs[1], &shownGraphs[0], 6);
        shownGraphs[0] = g;
        c = 0;
        bit = 1;
        for (; c < 4; c++, bit <<= 1)
            if (freeColors & bit) {
                freeColors &= ~bit;
                histColor[g] = c;
                break;
            }
    }
    win_DrawHistoryWindow(3);
    f_1E57_0362();
}

extern int far fd_50F6_0516[64];
extern int far fd_50F6_05A0[64];
extern int far fd_50F6_0626[64];
extern int far fd_50F6_06AE[64];
extern int far fd_50F6_073C[64];
extern int far fd_50F6_07CE[64];
extern int far fd_50F6_0856[64];
extern int far fd_50F6_08F0[64];
extern int far fd_50F6_0970[64];
extern int far fd_50F6_0A0A[64];
extern long far fd_50F6_0ADA;
extern int far fd_50F6_0A90;
extern int far fd_50F6_0AC4;
extern int far fd_50F6_0A9E;
extern int far fd_50F6_0AC8;
extern int far fd_50F6_04F4;
extern int far fd_3D57_0828;
extern long far BAntsEaten;
extern long far fd_50F6_0F30;
extern long far fd_50F6_0EFC;
extern long far RAntsEaten;
extern long far fd_50F6_0FBC;
extern long far fd_50F6_0F3E;
extern long far fd_50F6_0FC2;
extern long far fd_50F6_1000;

void far ClearHistory(int newGame)
{
    int i;

    for (i = 0; i < 64; i++) {
        fd_50F6_0516[i] = 0;
        fd_50F6_05A0[i] = 0;
        fd_50F6_0626[i] = 0;
        fd_50F6_06AE[i] = 0;
        fd_50F6_073C[i] = 0;
        fd_50F6_07CE[i] = 0;
        fd_50F6_0856[i] = 0;
        fd_50F6_08F0[i] = 0;
        fd_50F6_0970[i] = 0;
        fd_50F6_0A0A[i] = 0;
    }
    if (newGame == 1) {
        fd_50F6_0ADA = 0;
        fd_50F6_0A90 = 1;
        fd_50F6_0AC4 = 1;
        fd_50F6_0A9E = 0;
        fd_50F6_0AC8 = 0;
    }
    fd_50F6_04F4 = 0x3f;
    fd_3D57_0828 = 0;
    BAntsEaten = 0;
    fd_50F6_0F30 = 0;
    fd_50F6_0EFC = 0;
    RAntsEaten = 0;
    fd_50F6_0FBC = 0;
    fd_50F6_0F3E = 0;
    fd_50F6_0FC2 = 0;
    fd_50F6_1000 = 0;
}

void far win_DrawHistoryWindow(int flags)
{
    int i;

    if (flags & 2) {
        win_FillObjRect(0x150e, f_1B4E_000D(0));
        i = 0;
        while (i < 4) {
            if (shownGraphs[i] != (int)0x8000)
                drawHistGraph(shownGraphs[i], 0, i);
            i++;
        }
    }
}

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far * far fd_3D57_082A[];
extern int far * far fd_3D57_0852[];
extern void (far * near g_916C)(int x0, int y0, int x1, int y1, int color);
extern char far * far * far fd_50F6_02BA;
extern int far sprintf(char far *buf, char far *fmt, ...);
extern void (far * near g_9128)(int a, int b, int c);
extern void far f_24AB_02AD(int font);
extern int far f_24AB_030B(void);
extern void far f_24AB_038D(int x, int y, char far *text);
extern int far f_24AB_0329(char far *text);
extern void far f_1CE2_01F8(int left, int top, int right, int bottom, int width);

void far drawHistGraph(int graph, int hilite, int slot)
{
    struct Rect r;
    int color;
    int width;
    int height;
    int far *data;
    int far *data2;
    int start;
    int count;
    int j;
    int max;
    int n;
    int mul;
    int div;
    int x;
    int y;
    int px;
    int py;
    char far *s;
    char buf[30];
    int ty;
    int th;

    color = graphColors[histColor[graph]];
    win_GetObjRect(0x150e, &r);
    width = r.right - r.left - 0x40;
    r.bottom -= 8;
    r.top += 8;
    height = r.bottom - r.top;
    graph = (graph & 1) * 5 + (graph >> 1);
    data = fd_3D57_082A[graph];
    data2 = fd_3D57_0852[graph];
    start = fd_50F6_04F4;
    count = fd_3D57_0828;
    j = (start - count) & 0x3f;
    max = 0;
    for (n = 0; n < count; n++) {
        if (data[j] > max)
            max = data[j];
        if (data2[j] > max)
            max = data2[j];
        j = (j + 1) & 0x3f;
    }
    div = 1;
    mul = 1;
    if (max > 0) {
        for (mul = 1; max * mul < height; mul++)
            ;
        if (mul > 1)
            mul--;
        else
            while (max / div > height)
                div++;
    }
    j = start & 0x3f;
    x = r.left;
    if (div == 1)
        y = r.bottom - data[start] * mul;
    else
        y = r.bottom - data[start] / div;
    px = x;
    py = y;
    for (n = 1; n < 64; n++) {
        j = (j + 1) & 0x3f;
        x = n * width / 64 + slot + r.left;
        if (div == 1)
            y = r.bottom - data[j] * mul;
        else
            y = r.bottom - data[j] / div;
        (*g_916C)(px, py, x, y, color);
        px = x;
        py = y;
    }
    if (hilite == 0)
        s = fd_50F6_02BA[graph];
    else {
        sprintf(buf, "%d", data[j] + 1);
        s = buf;
    }
    (*g_9128)(color, 0, color);
    f_24AB_02AD(3);
    f_24AB_038D(x, ty = y - (th = f_24AB_030B()) / 2, s);
    f_1CE2_01F8(x - 1, ty - 1, f_24AB_0329(s) + x + 1, ty + th + 1, 1);
    f_24AB_02AD(0);
}

extern int far BpopT;
extern int far RpopT;
extern int far FoodB;
extern int far FoodR;
extern int far HealthB;
extern int far HealthR;
extern int far fd_50F6_1040;
extern int _fastcall win_IsWinOpen(int win);

void far HistUpdate(void)
{
    fd_50F6_0516[fd_50F6_04F4] = BpopT;
    fd_50F6_05A0[fd_50F6_04F4] = RpopT;
    fd_50F6_0626[fd_50F6_04F4] = FoodB;
    fd_50F6_06AE[fd_50F6_04F4] = FoodR;
    fd_50F6_073C[fd_50F6_04F4] = HealthB;
    fd_50F6_07CE[fd_50F6_04F4] = HealthR;
    fd_50F6_0856[fd_50F6_04F4] = fd_50F6_1040;
    fd_50F6_08F0[fd_50F6_04F4] = (int)fd_50F6_0F30;
    fd_50F6_0970[fd_50F6_04F4] = (int)BAntsEaten;
    fd_50F6_0A0A[fd_50F6_04F4] = (int)fd_50F6_0EFC;
    if (fd_3D57_0828 < 0x3f)
        fd_3D57_0828++;
    fd_50F6_04F4 = (fd_50F6_04F4 + 1) & 0x3f;
    if (win_IsWinOpen(0x1500)) {
        clip_SetWin(0x1500);
        win_DrawHistoryWindow(3);
        f_1E57_0362();
    }
}
