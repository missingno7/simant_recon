#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Overlay section S14, code frame 384C: score, scenario and picture dialogs.
 *
 * Source-form evidence (worker resF):
 *  - Every font choice is written `if (g_3DB2 == 320) f_24AB_02AD(a); else f_24AB_02AD(b);`
 *    (six sites).  The two calls are cross-jumped into the same bytes as a `?:` argument, but
 *    each if/else adds two /Zi line entries; with all six the 52-entry LINNUM flushes land where
 *    the oracle's relocation order needs record breaks (DrawCastePopUp, PictureDialog,
 *    SpiderDialog: 0 violations of 115 order constraints).
 *  - Identifier counts (symbol-table state, periodic mod 17) include local and prototype
 *    parameters. The forward prototypes of CalcScore/DoWinHelp/SetDefaultWindPrompt/
 *    PictStrnDialog are named (+6, CalcScore operand order), g_9134's and PictureDialog's forward
 *    declaration are unnamed (-5 before DrawCastePopUp, -4 before PictureDialog).
 *    CalcScore scopes its history index separately from the later matrix index; f_00F8_02F7 has an unnamed real prototype parameter.
 *    Alternative scopes and prototype-name removals also match; these forms are inferred.
 */

#include <stdio.h>
#include <string.h>
int32_t  CalcScore(int16_t  *scores);
int16_t  DoScenario(void);
void  DoWinHelp(int16_t win);
void  ScoreDialog(void);
void  DrawCastePopUp(void);
void  SetDefaultWindPrompt(int16_t mode);
void  PictStrnDialog(int16_t picture, int16_t object, int16_t force);
void  PictureDialog(char  *  *, int16_t, int16_t, int16_t);
void  EndGameDialog(void);
void  SpiderDialog(void);
void  CustomerIDDialog(void);


extern int16_t  fd_3D57_0828;
extern int16_t  fd_50F6_0EAC;
extern uint8_t  fd_3D57_00A4[12][16];

static char weights[8] = { 13, 17, 19, 23, 29, 31, 37, 41 };

int32_t  CalcScore(int16_t  *scores)
{
    int16_t i, j, k, n, t;
    int16_t sum, sum2;
    int32_t score, q;

    for (i = 0; i < 8; i++)
        scores[i] = 0;

    k = (native_state_fd_50F6_04F4.signed_value - fd_3D57_0828) & 0x3f;
    sum = 0;
    for (i = 0; i < fd_3D57_0828; i++) {
        sum += native_sim_state_fd_50F6_073C.signed_values[k];
        k = (k + 1) & 0x3f;
    }
    if (i > 0)
        scores[0] = sum / i;
    else
        scores[0] = 0;

    {
        int16_t historyIndex;
        historyIndex = (native_state_fd_50F6_04F4.signed_value - fd_3D57_0828) & 0x3f;
        sum = sum2 = 0;
        for (k = 0; k < fd_3D57_0828; k++) {
            sum += native_sim_state_fd_50F6_0626.signed_values[historyIndex];
            sum2 += native_sim_state_fd_50F6_06AE.signed_values[historyIndex];
            historyIndex = (historyIndex + 1) & 0x3f;
        }
        historyIndex = sum2 + sum;
        if (historyIndex > 0)
            scores[1] = (int32_t)sum * 100 / historyIndex;
        else
            scores[1] = 0;
    }

    if (native_state_fd_50F6_0FC2.signed_value > 0)
        scores[2] = (native_state_fd_50F6_0FC2.signed_value - native_state_fd_50F6_1000.signed_value) * 100 / native_state_fd_50F6_0FC2.signed_value;
    else
        scores[2] = 100;

    n = native_state_fd_50F6_09FA.signed_value + native_state_fd_50F6_0A00.signed_value;
    if (n > 0)
        scores[3] = native_state_fd_50F6_09FA.signed_value * 100 / n;
    else
        scores[3] = 100;

    if (fd_50F6_0EAC == 2 || fd_50F6_0EAC == 3) {
        n = native_state_fd_50F6_0AC4.signed_value + native_state_fd_50F6_0A90.signed_value;
        if (n > 0)
            scores[4] = (int32_t)native_state_fd_50F6_0A90.signed_value * 100 / n;
        else
            scores[4] = 100;
        n = native_state_fd_50F6_0A9E.signed_value + native_state_fd_50F6_0A90.signed_value;
        if (n > 0)
            scores[5] = (int32_t)native_state_fd_50F6_0A90.signed_value * 100 / n;
        else
            scores[5] = 100;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = j < 5 ? 3 : 2; k < 12; k++)
                if (fd_3D57_00A4[k][j])
                    sum++;
        if (sum > 0)
            scores[6] = (int32_t)sum * 100 / 155;
        else
            scores[6] = 0;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = 0; k < 2 || (j < 5 && k < 3); k++)
                if (fd_3D57_00A4[k][j])
                    sum++;
        if (sum > 0)
            scores[7] = (int32_t)sum * 100 / 37;
        else
            scores[7] = 0;
    }

    score = native_state_MeHealth.signed_value;
    for (k = 0; k < 8; k++)
        score += (int32_t)scores[k] * weights[k] * 51;

    if (fd_50F6_0EAC != 2) {
        score = score * 29 / 10;
        if (native_state_fd_50F6_0C26.signed_value < 4100) {
            q = native_state_fd_50F6_0C26.signed_value / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 41;
        }
    } else {
        if (native_state_fd_50F6_0C26.signed_value < 8100) {
            q = native_state_fd_50F6_0C26.signed_value / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 81;
        }
        score *= 5;
    }
    return native_state_fd_50F6_0C26.signed_value + score;
}


struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t h;
    int16_t v;
};

extern void  win_Open(int16_t win, ...);
extern void  win_FlushEvents(void);
extern int16_t  win_GetEvent(struct Event  *ev);
extern void  DialogClearWait(void);
extern int16_t  DialogAbort(void);
extern void  win_Close(int16_t win);
extern void  WinPrintf(char  *format, ...);

int16_t  DoScenario(void)
{
    struct Event ev;

    win_Open(0x200);
    win_FlushEvents();
    do {
        if (win_GetEvent(&ev) && (ev.code >> 8) == 2) {
            win_Close(0x200);
            WinPrintf("\nGOT Scenario %x", ev.code);
            return ev.code;
        }
        DialogClearWait();
    } while (!DialogAbort());
    win_Close(0x200);
    return 0x205;
}

extern void  win_LockWin(int16_t win);
extern int16_t  f_22BF_0AEF(int16_t win);
extern void  clip_SetWin(int16_t win);
extern void  win_MakeObjVisible(int16_t obj);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  win_DrawObjectNum(int16_t objNum);
extern void  f_2505_08EA(int16_t win);
extern void  ButtonHeldInit(void);
extern int16_t  win_Events(void);
extern int16_t  win_IsWinOpen(int16_t win);
extern int16_t  ButtonHeld(void);
extern void  win_MakeObjInvisible(int16_t obj);
extern void  f_2505_0831(int16_t win);
extern void  clip_SubInclude(struct Rect  *rect);
extern void ( *  g_62E0)(int16_t win);
extern void  win_DrawWindow(int16_t win);
extern int16_t  f_22BF_0B25(int16_t win);
extern void  clip_Off(void);
extern void  win_UnlockWin(int16_t win);

void  DoWinHelp(int16_t win)
{
    int16_t shown;
    struct Rect r;

    win_LockWin(win);
    shown = f_22BF_0AEF(win);
    clip_SetWin(win);
    win_MakeObjVisible(win);
    win_GetObjRect(win, &r);
    win_DrawObjectNum(win);
    f_2505_08EA(win);
    win_FlushEvents();
    ButtonHeldInit();
    while (!win_Events()) {
        if (!win_IsWinOpen(win) || !ButtonHeld())
            break;
    }
    win_FlushEvents();
    win_MakeObjInvisible(win);
    if (win_IsWinOpen(win)) {
        f_2505_0831(win);
        clip_SubInclude(&r);
        (*g_62E0)(win);
        win_DrawWindow(win);
    }
    if (!shown)
        f_22BF_0B25(win);
    clip_Off();
    win_UnlockWin(win);
}

extern void  win_SetObjFormatStr(int16_t obj, ...);
extern char  *  *  fd_50F6_034C;
extern void  f_24AB_02AD(int16_t font);
extern void  win_PrintfAtObj(int16_t obj, char  *format, ...);
extern char  *  *  fd_50F6_0368;
extern char  *  *  fd_50F6_0324;

void  ScoreDialog(void)
{
    int16_t scores[8];
    struct Event ev;
    char title[80];
    int16_t i;

    native_state_fd_50F6_0ADA.signed_value = CalcScore(scores);
    win_LockWin(0x1800);
    for (i = 0; i < 4; i++)
        win_SetObjFormatStr(0x1802 + i, scores[i]);
    win_SetObjFormatStr(0x180c, fd_50F6_034C[14]);
    win_FlushEvents();
    win_Open(0x1800);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        f_24AB_02AD(0);
    else
        f_24AB_02AD(4);
    if (fd_50F6_0EAC == 2) {
        for (i = 4; i < 8; i++)
            win_PrintfAtObj(0x1802 + i, "%d%%", scores[i]);
    } else {
        for (i = 4; i < 8; i++)
            win_PrintfAtObj(0x1802 + i, fd_50F6_0368[16]);
    }
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        f_24AB_02AD(3);
    else
        f_24AB_02AD(4);
    if (fd_50F6_0EAC == 3) {
        win_PrintfAtObj(0x180a, fd_50F6_0368[17]);
        win_PrintfAtObj(0x180b, fd_50F6_0368[18]);
        ev.code = 0;
    } else {
        title[0] = 0;
        _fstrcat(title, fd_50F6_0368[13]);
        _fstrcat(title, fd_50F6_0324[fd_50F6_0EAC]);
        _fstrcat(title, fd_50F6_0368[14]);
        win_PrintfAtObj(0x180a, title);
        win_PrintfAtObj(0x180b, "%ld", native_state_fd_50F6_0ADA.signed_value);
        ev.code = 0;
    }
    f_24AB_02AD(0);
    while (win_IsWinOpen(0x1800)) {
        if (win_GetEvent(&ev) && !(ev.code & 0x8000))
            break;
    }
    win_Close(0x1800);
    win_FlushEvents();
    win_UnlockWin(0x1800);
}

extern int16_t  f_24AB_0367(int16_t c);
extern int16_t  f_24AB_030B(void);
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);

void  DrawCastePopUp(void)
{
    struct Rect r;
    char buf[30];
    int16_t half, rem, acc, gap, lineh, width, left, maxw, h, top;
    int16_t i, w, y, max, a, b;

    native_state_fd_50F6_1074.signed_value = 1;
    half = SIM_GRAPHICS_SOURCE_g_3DB2 == 320 ? 1 : 2;
    win_Open(0x1700);
    ButtonHeldInit();
    win_GetObjRect(0x1702, &r);
    clip_SubInclude(&r);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        f_24AB_02AD(0);
    else
        f_24AB_02AD(2);
    maxw = 0;
    for (i = '0'; i <= '9'; i++) {
        w = f_24AB_0367(i);
        if (w > maxw)
            maxw = w;
    }
    left = maxw * 4 + r.left + 2;
    width = r.right - left;
    lineh = f_24AB_030B();
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        lineh--;
    gap = r.bottom - lineh * 12 - r.top;
    if (SIM_GRAPHICS_SOURCE_g_3DB2 != 320)
        gap += 3;
    rem = gap % 5;
    acc = 0;
    gap /= 5;
    h = lineh;
    y = top = r.top;
    max = 1;
    for (i = 1; i < 6; i++) {
        if (native_sim_state_fd_50F6_0AEC.signed_values[i] > max)
            max = native_sim_state_fd_50F6_0AEC.signed_values[i];
        if (native_sim_state_fd_50F6_0AFA.signed_values[i] > max)
            max = native_sim_state_fd_50F6_0AFA.signed_values[i];
    }
    for (i = 0; i < 6; i++, y += lineh * 2 + gap) {
        acc += rem;
        if (acc > 5) {
            y++;
            acc -= 5;
        }
        if (i == 5)
            y--;
        a = native_sim_state_fd_50F6_0AEC.signed_values[i] * (int32_t)width / max;
        b = native_sim_state_fd_50F6_0AFA.signed_values[i] * (int32_t)width / max;
        win_SetColorFromObjNum(0x1703);
        dos_sprintf(buf, "%d", native_sim_state_fd_50F6_0AEC.signed_values[i]);
        f_24AB_038D(r.left, y, buf);
        if (i)
            (*g_9134)(left, half / 2 + y, left + a, h - half + y, SIM_GRAPHICS_SOURCE_g_3DE0);
        win_SetColorFromObjNum(0x1704);
        dos_sprintf(buf, "%d", native_sim_state_fd_50F6_0AFA.signed_values[i]);
        f_24AB_038D(r.left, h + y, buf);
        if (i)
            (*g_9134)(left, half / 2 + h + y, left + b, h * 2 - half + y, SIM_GRAPHICS_SOURCE_g_3DE0);
    }
    f_24AB_02AD(0);
    ButtonHeldInit();
    do
        win_Events();
    while (win_IsWinOpen(0x1700) && ButtonHeld());
    win_Close(0x1700);
}


extern void  EditMessage(void  *text, int32_t pos, int16_t mode);

void  SetDefaultWindPrompt(int16_t mode)
{
    if (native_state_fd_50F6_047E.signed_value == 0)
        EditMessage(0L, -2L, mode);
    else if (native_state_fd_50F6_105E.signed_value == -1)
        EditMessage(fd_50F6_034C[2], -2L, mode);
    else if (native_state_fd_50F6_105E.signed_value == 10)
        EditMessage(fd_50F6_034C[3], -2L, mode);
    else if (native_state_fd_50F6_105E.signed_value == 11)
        EditMessage(fd_50F6_034C[17], -2L, mode);
}

extern int16_t  fd_3D57_07A8[];
extern char  *  *  LoadStringAnt(int16_t object);
void  PictureDialog(char  *  *, int16_t, int16_t, int16_t);
extern void  dos_free(char  *  *block);
extern void  db_PurgeObject(int16_t object, int16_t kind);

void  PictStrnDialog(int16_t picture, int16_t object, int16_t force)
{
    int16_t count;
    char  *  *strings;

    WinPrintf("StrnID=%d", object);
    if (force || fd_3D57_07A8[3]) {
        count = 0;
        strings = LoadStringAnt(object);
        if (strings)
            while (strings[count])
                count++;
        PictureDialog(strings, count, picture, force);
        if (strings) {
            dos_free(strings);
            db_PurgeObject(object, 4);
        }
    }
}

extern void  f_208F_0419(struct Pt  *size, int16_t id);
extern int16_t  f_24AB_0329(char  *text);
extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);
extern void  f_208F_0093(struct Rect  *rect, char  *text);
extern void  DialogWaitInit(int16_t);
extern int16_t  DialogAbortOrCont(void);

void  PictureDialog(char  *  *strings, int16_t count, int16_t picture, int16_t force)
{
    struct Pt size;
    int16_t lineh, h, maxw, i, w;
    struct Rect r;
    struct Event ev;

    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        f_24AB_02AD(3);
    else
        f_24AB_02AD(4);
    lineh = f_24AB_030B();
    if (picture)
        f_208F_0419(&size, picture);
    h = (picture ? size.v + 2 : 0) + count * lineh + 8;
    maxw = 50;
    for (i = 0; i < count; i++) {
        w = f_24AB_0329(strings[i]);
        if (w > maxw)
            maxw = w;
    }
    maxw += 8;
    r.top = (SIM_GRAPHICS_SOURCE_g_3DB4 - h) / 2;
    r.bottom = r.top + h;
    r.left = (SIM_GRAPHICS_SOURCE_g_3DB2 - maxw) / 2;
    r.right = r.left + maxw;
    win_Open(0x1e00, r.left, r.top, r.right, r.bottom);
    WinPrintf("Pict=%d", picture);
    if (picture) {
        win_DrawBitMap((r.left + r.right - size.h) / 2, r.top, picture);
        r.top += size.v + 2;
    }
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        f_24AB_02AD(3);
    else
        f_24AB_02AD(4);
    win_SetColorFromObjNum(0x1e01);
    for (i = 0; i < count; i++) {
        r.bottom = r.top + lineh;
        f_208F_0093(&r, strings[i]);
        WinPrintf("line %d:%s", i, strings[i]);
        r.top += lineh;
    }
    DialogWaitInit(15);
    while (!DialogAbortOrCont() && win_IsWinOpen(0x1e00)) {
        if (win_GetEvent(&ev) && !(ev.code & 0x8000))
            break;
    }
    win_Close(0x1e00);
    WinPrintf("PictStrnDialog: %d", picture);
    f_24AB_02AD(0);
}


extern void  myBeginSong(int16_t id, int16_t arg);
extern char  *  *  fd_50F6_0328;
extern int16_t  mySongIsDone(void);
extern int16_t  SRand2(void);
extern int16_t  NewGame(int16_t a);
extern void  MenuQuit(void);

void  EndGameDialog(void)
{
    int16_t scores[8];
    int32_t score, s;
    int16_t level, played;

    if (fd_3D57_07A8[1]) {
        if (native_state_fd_50F6_0366.signed_value == 0)
            myBeginSong(0x271a, 0x7e);
        else if (fd_50F6_0EAC == 2)
            myBeginSong(0x2718, 0x7e);
        else
            myBeginSong(0x2718, 0x7e);
    }
    score = CalcScore(scores);
    s = fd_50F6_0EAC == 2 ? score / 5 : score;
    if (s < 214220L)
        level = 0;
    else if (s < 428440L)
        level = 1;
    else if (s < 642660L)
        level = 2;
    else if (s < 856880L)
        level = 3;
    else
        level = 4;
    if (native_state_fd_50F6_0366.signed_value == 0)
        level += 5;
    win_Open(0x400);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
        f_24AB_02AD(2);
    else
        f_24AB_02AD(4);
    win_PrintfAtObj(0x402, fd_50F6_0324[fd_50F6_0EAC]);
    win_PrintfAtObj(0x403, "%ld", score);
    win_PrintfAtObj(0x404, fd_50F6_0328[level]);
    played = 0;
    f_24AB_02AD(0);
    DialogWaitInit(100);
    while (win_IsWinOpen(0x400)) {
        if (win_Events() || DialogAbortOrCont())
            win_Close(0x400);
        if (mySongIsDone() && !played) {
            played++;
            myBeginSong(SRand2() + 0x2713, 0x7e);
        }
    }
    if (NewGame(0) < 0)
        MenuQuit();
}

extern void  win_SetObjBitmap(int16_t obj, int16_t bitmap);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern int32_t  MacTickCount(void);
extern int16_t  fd_3D57_09B4[];
extern void  myDelay(int32_t ticks);
extern int16_t  SRand1(int16_t range);

void  SpiderDialog(void)
{
    struct Rect r;
    int32_t t;
    int16_t bmp, frame;

    win_LockWin(0x1a00);
    bmp = 0x2ee0;
    win_SetObjBitmap(0x1a01, bmp);
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &r);
    frame = 0;
    myBeginSound(0x2d, frame, 0x7e);
    MacTickCount();
    t = MacTickCount() + 8;
    DialogWaitInit(8);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 != 320) {
        r.left += 0x2e;
        r.top += 0x4d;
    }
    while (!DialogAbortOrCont()) {
        if (win_Events())
            break;
        if (MacTickCount() >= t) {
            t = MacTickCount() + 8;
            frame++;
            if (frame > 3) {
                frame = 0;
                myBeginSound(0x2d, frame, 0x7e);
            }
            bmp = fd_3D57_09B4[frame] + 0x2ee1;
            win_DrawBitMap(r.left, r.top, bmp);
        }
        myDelay(1L);
    }
    frame = SRand1(2) ? 0x2740 : 0x273f;
    if (bmp)
        win_DrawBitMap(r.left, r.top, bmp);
    PictStrnDialog(0, frame, 1);
    win_FlushEvents();
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}


extern char  *  *  db_LoadObject(int16_t object, int16_t kind);
extern char  *  f_171C_1B84(char  *  *handle);
extern char  *  *  fd_50F6_3836;
extern char  *  *  fd_50F6_3938;
extern char  *  *  fd_50F6_3934;
extern int16_t  f_1F58_0038(void);
extern void  f_1F58_0090(void);
extern void  f_171C_1BBA(char  *  *handle);
extern void  db_ReleaseHandle(char  *  *handle);

void  CustomerIDDialog(void)
{
    char  *  *h83;
    char  *  *h84;
    char  *strings[6];

    h83 = db_LoadObject(0x83, 10);
    h84 = db_LoadObject(0x84, 10);
    strings[0] = f_171C_1B84(h83);
    strings[1] = f_171C_1B84(fd_50F6_3836);
    strings[2] = f_171C_1B84(fd_50F6_3938);
    strings[3] = " ";
    strings[4] = f_171C_1B84(h84);
    strings[5] = f_171C_1B84(fd_50F6_3934);
    win_FlushEvents();
    while (f_1F58_0038())
        f_1F58_0090();
    PictureDialog(strings, 6, 0, 1);
    f_171C_1BBA(h83);
    f_171C_1BBA(h84);
    f_171C_1BBA(fd_50F6_3836);
    f_171C_1BBA(fd_50F6_3934);
    db_ReleaseHandle(h83);
    db_ReleaseHandle(h84);
}

#pragma pack(pop)
