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
extern int far ConvColor(int color);
extern void _fastcall win_FillObjRect(int obj, int color);
void far drawHistGraph(int graph, int hilite, int slot);
extern int far StillDown(void);
void far win_DrawHistoryWindow(int flags);
extern void far clip_Off(void);

void far ProcHistoryEvent(struct Event far *ev)
{
    int i;

    switch (ev->code) {
    case 0x150d:
        DoWinHelp(0x150f);
        break;
    case 0x150e:
        clip_SetWin(0x1500);
        win_FillObjRect(0x150e, ConvColor(0));
        for (i = 0; i < 4; i++)
            if (shownGraphs[i] != (int)0x8000)
                drawHistGraph(shownGraphs[i], 1, i);
        while (StillDown())
            ;
        win_DrawHistoryWindow(3);
        clip_Off();
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
    clip_Off();
}

int far H_BPop[64];
int far H_RPop[64];
int far H_BFood[64];
int far H_RFood[64];
int far H_BHeal[64];
int far H_RHeal[64];
int far H_FoodA[64];
int far H_ADead[64];
int far H_PDead[64];
int far H_FDead[64];
extern long far OverallScore;
extern int far BColoniesStarted;
extern int far RColoniesStarted;
extern int far BColoniesKilled;
extern int far RColoniesKilled;
extern int far HistStart;
extern int far HistCnt;
extern long far BAntsEaten;
extern long far BAntsExpired;
extern long far BAntsKilled;
extern long far RAntsEaten;
extern long far RAntsExpired;
extern long far RAntsKilled;
extern long far TotalEggsLaidB;
extern long far TotalEggsDiedB;

void far ClearHistory(int newGame)
{
    int i;

    for (i = 0; i < 64; i++) {
        H_BPop[i] = 0;
        H_RPop[i] = 0;
        H_BFood[i] = 0;
        H_RFood[i] = 0;
        H_BHeal[i] = 0;
        H_RHeal[i] = 0;
        H_FoodA[i] = 0;
        H_ADead[i] = 0;
        H_PDead[i] = 0;
        H_FDead[i] = 0;
    }
    if (newGame == 1) {
        OverallScore = 0;
        BColoniesStarted = 1;
        RColoniesStarted = 1;
        BColoniesKilled = 0;
        RColoniesKilled = 0;
    }
    HistStart = 0x3f;
    HistCnt = 0;
    BAntsEaten = 0;
    BAntsExpired = 0;
    BAntsKilled = 0;
    RAntsEaten = 0;
    RAntsExpired = 0;
    RAntsKilled = 0;
    TotalEggsLaidB = 0;
    TotalEggsDiedB = 0;
}

void far win_DrawHistoryWindow(int flags)
{
    int i;

    if (flags & 2) {
        win_FillObjRect(0x150e, ConvColor(0));
        i = 0;
        while (i < 4) {
            if (shownGraphs[i] != (int)0x8000)
                drawHistGraph(shownGraphs[i], 0, i);
            i++;
        }
    }
}

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far * far HistGraphs[];
extern int far * far AltHistGraphs[];
extern void (far * near g_916C)(int, int, int, int, int);
extern char far * far * far HistGraphStrs;
extern int far sprintf(char far *buf, char far *fmt, ...);
extern void (far * near g_9128)(int, int, int);
extern void far font_SetFont(int font);
extern int far f_24AB_030B(void);
extern void far font_PrintStr(int x, int y, char far *text);
extern int far f_24AB_0329(char far *text);
extern void far GBoxOutline(int, int, int, int, int);


void far drawHistGraph(int graph, int hilite, int slot)
{
    struct Rect r;
    int color;
    int width;
    int height;
    /* MSC operand choices require this declaration order in the current TU. */
    int far *data2;
    int n;
    /* STEERED intermediate: grouping retains the snapshot/label homes.
       The original record identity is not established by the bytes. */
    struct { int count; int start; char label[20]; } range;
    int far *data;
    int j;
    int max;
    int mul;
    int div;
    int x;
    int y;
    int px;
    int py;
    char far *s;
    int ty;
    int th;

    color = graphColors[histColor[graph]];
    win_GetObjRect(0x150e, &r);
    width = r.right - r.left - 0x40;
    r.bottom -= 8;
    r.top += 8;
    height = r.bottom - r.top;
    graph = (graph & 1) * 5 + (graph >> 1);
    data = HistGraphs[graph];
    data2 = AltHistGraphs[graph];
    range.start = HistStart;
    range.count = HistCnt;
    j = (range.start - range.count) & 0x3f;
    max = 0;
    for (n = 0; range.count > n; n++) {
        if (data[j] > max)
            max = data[j];
        if (data2[j] > max)
            max = data2[j];
        j = (j + 1) & 0x3f;
    }
    div = 1;
    mul = 1;
    if (max > 0) {
        for (; max * mul < height; mul++)
            ;
        if (mul > 1)
            mul--;
        else
            while (max / div > height)
                div++;
    }
    j = range.start & 0x3f;
    x = r.left;
    if (div == 1)
        y = r.bottom - data[range.start] * mul;
    else
        y = r.bottom - data[range.start] / div;
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
        s = HistGraphStrs[graph];
    else {
        sprintf(range.label, "%d", data[j]);
        s = range.label;
    }
    (*g_9128)(color, 0, color);
    font_SetFont(3);
    font_PrintStr(x, ty = y - (th = f_24AB_030B()) / 2, s);
    width = f_24AB_0329(s);
    GBoxOutline(x - 1, ty - 1, width + x + 1, ty + th + 1, 1);
    font_SetFont(0);
}


extern int far BpopT;
extern int far RpopT;
extern int far FoodB;
extern int far FoodR;
extern int far HealthB;
extern int far HealthR;
extern int far FoodA;
extern int _fastcall win_IsWinOpen(int win);

void far HistUpdate(void)
{
    H_BPop[HistStart] = BpopT;
    H_RPop[HistStart] = RpopT;
    H_BFood[HistStart] = FoodB;
    H_RFood[HistStart] = FoodR;
    H_BHeal[HistStart] = HealthB;
    H_RHeal[HistStart] = HealthR;
    H_FoodA[HistStart] = FoodA;
    H_ADead[HistStart] = (int)BAntsExpired;
    H_PDead[HistStart] = (int)BAntsEaten;
    H_FDead[HistStart] = (int)BAntsKilled;
    if (HistCnt < 0x3f)
        HistCnt++;
    HistStart = (HistStart + 1) & 0x3f;
    if (win_IsWinOpen(0x1500)) {
        clip_SetWin(0x1500);
        win_DrawHistoryWindow(3);
        clip_Off();
    }
}
