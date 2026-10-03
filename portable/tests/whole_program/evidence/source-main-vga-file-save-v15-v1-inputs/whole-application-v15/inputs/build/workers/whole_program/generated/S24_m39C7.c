#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

extern void  *  fd_3D57_082A[];
/* Overlay section S24, code frame 39C7: history graph window (Win16 SIMANT_MODULE OpenHistoryWindow..HistUpdate). */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

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

extern void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) ;

void  OpenHistoryWindow(void)
{
    win_Open(0x1500, 0, 0, 0, 0, 0);
}

static int16_t graphColors[4] = { 0x43, 0x46, 0x49, 0x45 };
static int16_t shownGraphs[4] = { (int16_t)0x8000, (int16_t)0x8000, (int16_t)0x8000, (int16_t)0x8000 };
static int16_t freeColors = 0x0f;
static int16_t histColor[20];
static char histShown[10];

extern void  DoWinHelp(int16_t topic);
void  ToggleHistButton(int16_t item);
extern void  clip_SetWin(int16_t win);
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
                /* Native lowering: the one-past read feeds only the slot
                 * immediately replaced by the sentinel. */
                _fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (3 - i) * 2);
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

extern int16_t  fd_3D57_0828;

void  ClearHistory(int16_t newGame)
{
    int16_t i;

    for (i = 0; i < 64; i++) {
        native_sim_state_fd_50F6_0516.signed_values[i] = 0;
        native_sim_state_fd_50F6_05A0.signed_values[i] = 0;
        native_sim_state_fd_50F6_0626.signed_values[i] = 0;
        native_sim_state_fd_50F6_06AE.signed_values[i] = 0;
        native_sim_state_fd_50F6_073C.signed_values[i] = 0;
        native_sim_state_fd_50F6_07CE.signed_values[i] = 0;
        native_sim_state_fd_50F6_0856.signed_values[i] = 0;
        native_sim_state_fd_50F6_08F0.signed_values[i] = 0;
        native_sim_state_fd_50F6_0970.signed_values[i] = 0;
        native_sim_state_fd_50F6_0A0A.signed_values[i] = 0;
    }
    if (newGame == 1) {
        native_state_fd_50F6_0ADA.signed_value = 0;
        native_state_fd_50F6_0A90.signed_value = 1;
        native_state_fd_50F6_0AC4.signed_value = 1;
        native_state_fd_50F6_0A9E.signed_value = 0;
        native_state_fd_50F6_0AC8.signed_value = 0;
    }
    native_state_fd_50F6_04F4.signed_value = 0x3f;
    fd_3D57_0828 = 0;
    native_state_BAntsEaten.signed_value = 0;
    native_state_fd_50F6_0F30.signed_value = 0;
    native_state_fd_50F6_0EFC.signed_value = 0;
    native_state_RAntsEaten.signed_value = 0;
    native_state_fd_50F6_0FBC.signed_value = 0;
    native_state_fd_50F6_0F3E.signed_value = 0;
    native_state_fd_50F6_0FC2.signed_value = 0;
    native_state_fd_50F6_1000.signed_value = 0;
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
extern char  *  *  fd_50F6_02BA;
extern void  f_24AB_02AD(int16_t font);
extern int16_t  f_24AB_030B(void);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);
extern int16_t  f_24AB_0329(char  *text);
extern void  f_1CE2_01F8(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width);

/* SCAFFOLD BEGIN: drawHistGraph best draft (714 vs 732 bytes): logic complete; the original keeps the loop counter n, x and y in BP slots (frame 0x46, SI/DI only for temporaries and the label pointer), this draft enregisters n and uses an 0x4E frame */
void  drawHistGraph(int16_t graph, int16_t hilite, int16_t slot)
{
    struct Rect r;
    int16_t color;
    int16_t width;
    int16_t height;
    int16_t  *data;
    int16_t  *data2;
    int16_t start;
    int16_t count;
    int16_t j;
    int16_t max;
    int16_t n;
    int16_t mul;
    int16_t div;
    int16_t x;
    int16_t y;
    int16_t px;
    int16_t py;
    char  *s;
    char buf[30];
    int16_t ty;
    int16_t th;

    color = graphColors[histColor[graph]];
    win_GetObjRect(0x150e, &r);
    width = r.right - r.left - 0x40;
    r.bottom -= 8;
    r.top += 8;
    height = r.bottom - r.top;
    graph = (graph & 1) * 5 + (graph >> 1);
    data = fd_3D57_082A[graph];
    data2 = ((int16_t  *  *)(fd_3D57_082A + 10))[graph];
    start = native_state_fd_50F6_04F4.signed_value;
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
        dos_sprintf(buf, "%d", data[j]);
        s = buf;
    }
    (*g_9128)(color, 0, color);
    f_24AB_02AD(3);
    f_24AB_038D(x, ty = y - (th = f_24AB_030B()) / 2, s);
    f_1CE2_01F8(x - 1, ty - 1, f_24AB_0329(s) + x + 1, ty + th + 1, 1);
    f_24AB_02AD(0);
}
/* SCAFFOLD END */

extern int16_t  win_IsWinOpen(int16_t win);

void  HistUpdate(void)
{
    native_sim_state_fd_50F6_0516.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_BpopT.signed_value;
    native_sim_state_fd_50F6_05A0.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_RpopT.signed_value;
    native_sim_state_fd_50F6_0626.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_FoodB.signed_value;
    native_sim_state_fd_50F6_06AE.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_FoodR.signed_value;
    native_sim_state_fd_50F6_073C.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_HealthB.signed_value;
    native_sim_state_fd_50F6_07CE.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_HealthR.signed_value;
    native_sim_state_fd_50F6_0856.signed_values[native_state_fd_50F6_04F4.signed_value] = native_state_fd_50F6_1040.signed_value;
    native_sim_state_fd_50F6_08F0.signed_values[native_state_fd_50F6_04F4.signed_value] = (int16_t)native_state_fd_50F6_0F30.signed_value;
    native_sim_state_fd_50F6_0970.signed_values[native_state_fd_50F6_04F4.signed_value] = (int16_t)native_state_BAntsEaten.signed_value;
    native_sim_state_fd_50F6_0A0A.signed_values[native_state_fd_50F6_04F4.signed_value] = (int16_t)native_state_fd_50F6_0EFC.signed_value;
    if (fd_3D57_0828 < 0x3f)
        fd_3D57_0828++;
    native_state_fd_50F6_04F4.signed_value = (native_state_fd_50F6_04F4.signed_value + 1) & 0x3f;
    if (win_IsWinOpen(0x1500)) {
        clip_SetWin(0x1500);
        win_DrawHistoryWindow(3);
        clip_Off();
    }
}

#pragma pack(pop)
