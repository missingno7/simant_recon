#include "recovered_state.h"
#include <stdint.h>
#include <stddef.h>

/* Overlay section S24, code frame 39C7: history graph window (Win16 SIMANT_MODULE OpenHistoryWindow..HistUpdate). */



struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    uint16_t code;
    int16_t xE;
};

extern void  win_Open();

void  OpenHistoryWindow(void)
{
    win_Open(0x1500);
}

static int16_t graphColors[4] = { 0x43, 0x46, 0x49, 0x45 };
static int16_t shownGraphs[4] = { (int16_t)0x8000, (int16_t)0x8000, (int16_t)0x8000, (int16_t)0x8000 };
static int16_t freeColors = 0x0f;
static int16_t histColor[20];
static char histShown[10];

extern void  DoWinHelp(int16_t topic);
void  ToggleHistButton(int16_t item);
extern void  clip_SetWin(int16_t win);
extern int16_t  f_1B4E_000D(int16_t color);
extern void  win_FillObjRect(int16_t obj, int16_t color);
void  drawHistGraph(int16_t graph, int16_t hilite, int16_t slot);
extern int16_t  StillDown(void);
void  win_DrawHistoryWindow(int16_t flags);
extern void  clip_Off(void);

void  ProcHistoryEvent(struct Event  *ev)
{
    int16_t i;

    switch (ev->code) {
    case 0x150d:
        DoWinHelp(0x150f);
        break;
    case 0x150e:
        clip_SetWin(0x1500);
        win_FillObjRect(0x150e, f_1B4E_000D(0));
        for (i = 0; i < 4; i++)
            if (shownGraphs[i] != (int16_t)0x8000)
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

extern void  *  _fmemmove(void  *dst, void  *src, unsigned n);
extern void  win_MakeObjUnselected(int16_t obj);

void  ToggleHistButton(int16_t item)
{
    int16_t i;
    int16_t g;
    int16_t c;
    int16_t bit;

    clip_SetWin(0x1500);
    g = item - 0x1503;
    if (histShown[g]) {
        for (i = 0; i < 4; i++)
            if (shownGraphs[i] == g) {
                _fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (4 - i) * 2);
                shownGraphs[3] = (int16_t)0x8000;
                break;
            }
        histShown[g] = 0;
        freeColors |= 1 << histColor[g];
    } else {
        histShown[g] = 1;
        if ((i = shownGraphs[3]) != (int16_t)0x8000) {
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


























void  ClearHistory(int16_t newGame)
{
    int16_t i;

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

void  win_DrawHistoryWindow(int16_t flags)
{
    int16_t i;

    if (flags & 2) {
        win_FillObjRect(0x150e, f_1B4E_000D(0));
        i = 0;
        while (i < 4) {
            if (shownGraphs[i] != (int16_t)0x8000)
                drawHistGraph(shownGraphs[i], 0, i);
            i++;
        }
    }
}

extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);


extern void ( *  g_916C)(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t color);

extern int16_t  sprintf(char  *buf, char  *fmt, ...);
extern void ( *  g_9128)(int16_t a, int16_t b, int16_t c);
extern void  f_24AB_02AD(int16_t font);
extern int16_t  f_24AB_030B(void);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);
extern int16_t  f_24AB_0329(char  *text);
extern void  f_1CE2_01F8(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width);

void  drawHistGraph(int16_t graph, int16_t hilite, int16_t slot); /* scaffold body excluded: unresolved external/native binding */







extern int16_t  win_IsWinOpen(int16_t win);

void  HistUpdate(void)
{
    fd_50F6_0516[fd_50F6_04F4] = BpopT;
    fd_50F6_05A0[fd_50F6_04F4] = RpopT;
    fd_50F6_0626[fd_50F6_04F4] = FoodB;
    fd_50F6_06AE[fd_50F6_04F4] = FoodR;
    fd_50F6_073C[fd_50F6_04F4] = HealthB;
    fd_50F6_07CE[fd_50F6_04F4] = HealthR;
    fd_50F6_0856[fd_50F6_04F4] = fd_50F6_1040;
    fd_50F6_08F0[fd_50F6_04F4] = (int16_t)fd_50F6_0F30;
    fd_50F6_0970[fd_50F6_04F4] = (int16_t)BAntsEaten;
    fd_50F6_0A0A[fd_50F6_04F4] = (int16_t)fd_50F6_0EFC;
    if (fd_3D57_0828 < 0x3f)
        fd_3D57_0828++;
    fd_50F6_04F4 = (fd_50F6_04F4 + 1) & 0x3f;
    if (win_IsWinOpen(0x1500)) {
        clip_SetWin(0x1500);
        win_DrawHistoryWindow(3);
        clip_Off();
    }
}

/* Explicit state-bound native entry points; original bodies remain unchanged. */
