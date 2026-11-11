/* Overlay section S14, code frame 384C: score, scenario and picture dialogs.
 *
 * Source-form evidence (worker resF):
 *  - Every font choice is written `if (g_3DB2 == 320) font_SetFont(a); else font_SetFont(b);`
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
long far CalcScore(int far *scores);
int far DoScenario(void);
void far DoWinHelp(int win);
void far ScoreDialog(void);
void far DrawCastePopUp(void);
void far SetDefaultWindPrompt(int mode);
void far PictStrnDialog(int picture, int object, int force);
void far PictureDialog(char far * far *, int, int, int);
void far EndGameDialog(void);
void far SpiderDialog(void);
void far CustomerIDDialog(void);


extern int far HistStart;
extern int far HistCnt;
extern int far H_BHeal[64];
extern int far H_BFood[64];
extern int far H_RFood[64];
extern long far TotalEggsLaidB;
extern long far TotalEggsDiedB;
extern int far BlackLost;
extern int far RedLost;
extern int far CurGameType;
extern int far BColoniesStarted;
extern int far RColoniesStarted;
extern int far BColoniesKilled;
extern unsigned char far YMapPopB[12][16];
extern int far MeHealth;
extern long far GameTime;

static char weights[8] = { 13, 17, 19, 23, 29, 31, 37, 41 };

long far CalcScore(int far *scores)
{
    int i, j, k, n, t;
    int sum, sum2;
    long score, q;

    for (i = 0; i < 8; i++)
        scores[i] = 0;

    k = (HistStart - HistCnt) & 0x3f;
    sum = 0;
    for (i = 0; i < HistCnt; i++) {
        sum += H_BHeal[k];
        k = (k + 1) & 0x3f;
    }
    if (i > 0)
        scores[0] = sum / i;
    else
        scores[0] = 0;

    {
        int historyIndex;
        historyIndex = (HistStart - HistCnt) & 0x3f;
        sum = sum2 = 0;
        for (k = 0; k < HistCnt; k++) {
            sum += H_BFood[historyIndex];
            sum2 += H_RFood[historyIndex];
            historyIndex = (historyIndex + 1) & 0x3f;
        }
        historyIndex = sum2 + sum;
        if (historyIndex > 0)
            scores[1] = (long)sum * 100 / historyIndex;
        else
            scores[1] = 0;
    }

    if (TotalEggsLaidB > 0)
        scores[2] = (TotalEggsLaidB - TotalEggsDiedB) * 100 / TotalEggsLaidB;
    else
        scores[2] = 100;

    n = BlackLost + RedLost;
    if (n > 0)
        scores[3] = BlackLost * 100 / n;
    else
        scores[3] = 100;

    if (CurGameType == 2 || CurGameType == 3) {
        n = RColoniesStarted + BColoniesStarted;
        if (n > 0)
            scores[4] = (long)BColoniesStarted * 100 / n;
        else
            scores[4] = 100;
        n = BColoniesKilled + BColoniesStarted;
        if (n > 0)
            scores[5] = (long)BColoniesStarted * 100 / n;
        else
            scores[5] = 100;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = j < 5 ? 3 : 2; k < 12; k++)
                if (YMapPopB[k][j])
                    sum++;
        if (sum > 0)
            scores[6] = (long)sum * 100 / 155;
        else
            scores[6] = 0;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = 0; k < 2 || (j < 5 && k < 3); k++)
                if (YMapPopB[k][j])
                    sum++;
        if (sum > 0)
            scores[7] = (long)sum * 100 / 37;
        else
            scores[7] = 0;
    }

    score = MeHealth;
    for (k = 0; k < 8; k++)
        score += (long)scores[k] * weights[k] * 51;

    if (CurGameType != 2) {
        score = score * 29 / 10;
        if (GameTime < 4100) {
            q = GameTime / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 41;
        }
    } else {
        if (GameTime < 8100) {
            q = GameTime / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 81;
        }
        score *= 5;
    }
    return GameTime + score;
}


struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pt {
    int h;
    int v;
};

extern void far f_20E8_04B6(int win, ...);
extern void far f_218D_042B(void);
extern int _fastcall f_218D_03F1(struct Event far *ev);
extern void far f_00F8_032A(void);
extern int far f_00F8_05C9(void);
extern void _fastcall f_20E8_0635(int win);
extern void far WinPrintf(char far *format, ...);

int far DoScenario(void)
{
    struct Event ev;

    f_20E8_04B6(0x200);
    f_218D_042B();
    do {
        if (f_218D_03F1(&ev) && (ev.code >> 8) == 2) {
            f_20E8_0635(0x200);
            WinPrintf("\nGOT Scenario %x", ev.code);
            return ev.code;
        }
        f_00F8_032A();
    } while (!f_00F8_05C9());
    f_20E8_0635(0x200);
    return 0x205;
}

extern void _fastcall f_23AE_0377(int win);
extern int _fastcall win_set_flag_0040(int win);
extern void far clip_SetWin(int win);
extern void _fastcall f_22BF_0498(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void _fastcall win_deactivate_pointer_regions(int win);
extern void far f_1FD2_057F(void);
extern int far f_218D_03E8(void);
extern int _fastcall f_22BF_09B0(int win);
extern int far f_1FD2_0598(void);
extern void _fastcall f_22BF_04A0(int obj);
extern void _fastcall win_activate_pointer_regions(int win);
extern void far clip_SubInclude(struct Rect far *rect);
extern void (far * far g_62E0)(int win);
extern void _fastcall f_21FA_08E2(int win);
extern int _fastcall win_clear_flag_0040(int win);
extern void far f_1E57_0362(void);
extern void _fastcall f_23AE_01DB(int win);

void far DoWinHelp(int win)
{
    int shown;
    struct Rect r;

    f_23AE_0377(win);
    shown = win_set_flag_0040(win);
    clip_SetWin(win);
    f_22BF_0498(win);
    win_GetObjRect(win, &r);
    win_DrawObjectNum(win);
    win_deactivate_pointer_regions(win);
    f_218D_042B();
    f_1FD2_057F();
    while (!f_218D_03E8()) {
        if (!f_22BF_09B0(win) || !f_1FD2_0598())
            break;
    }
    f_218D_042B();
    f_22BF_04A0(win);
    if (f_22BF_09B0(win)) {
        win_activate_pointer_regions(win);
        clip_SubInclude(&r);
        (*g_62E0)(win);
        f_21FA_08E2(win);
    }
    if (!shown)
        win_clear_flag_0040(win);
    f_1E57_0362();
    f_23AE_01DB(win);
}

extern long far OverallScore;
extern void far f_22BF_059A(int obj, ...);
extern char far * far * far WindPromptStrs;
extern int near g_3DB2;
extern void far font_SetFont(int font);
extern void far f_22BF_0D53(int obj, char far *format, ...);
extern char far * far * far fd_50F6_0368;
extern char far * far * far fd_50F6_0324;

void far ScoreDialog(void)
{
    int scores[8];
    struct Event ev;
    char title[80];
    int i;

    OverallScore = CalcScore(scores);
    f_23AE_0377(0x1800);
    for (i = 0; i < 4; i++)
        f_22BF_059A(0x1802 + i, scores[i]);
    f_22BF_059A(0x180c, WindPromptStrs[14]);
    f_218D_042B();
    f_20E8_04B6(0x1800);
    if (g_3DB2 == 320)
        font_SetFont(0);
    else
        font_SetFont(4);
    if (CurGameType == 2) {
        for (i = 4; i < 8; i++)
            f_22BF_0D53(0x1802 + i, "%d%%", scores[i]);
    } else {
        for (i = 4; i < 8; i++)
            f_22BF_0D53(0x1802 + i, fd_50F6_0368[16]);
    }
    if (g_3DB2 == 320)
        font_SetFont(3);
    else
        font_SetFont(4);
    if (CurGameType == 3) {
        f_22BF_0D53(0x180a, fd_50F6_0368[17]);
        f_22BF_0D53(0x180b, fd_50F6_0368[18]);
        ev.code = 0;
    } else {
        title[0] = 0;
        _fstrcat(title, fd_50F6_0368[13]);
        _fstrcat(title, fd_50F6_0324[CurGameType]);
        _fstrcat(title, fd_50F6_0368[14]);
        f_22BF_0D53(0x180a, title);
        f_22BF_0D53(0x180b, "%ld", OverallScore);
        ev.code = 0;
    }
    font_SetFont(0);
    while (f_22BF_09B0(0x1800)) {
        if (f_218D_03F1(&ev) && !(ev.code & 0x8000))
            break;
    }
    f_20E8_0635(0x1800);
    f_218D_042B();
    f_23AE_01DB(0x1800);
}

extern int far LessonTemp;
extern int far font_CharWidth(int c);
extern int far font_FontHeight(void);
extern int far CastePopB[];
extern int far CastePopR[];
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far font_PrintStr(int x, int y, char far *text);
extern int near _foreColor;
extern void (far * near g_9134)(int, int, int, int, int);

void far DrawCastePopUp(void)
{
    struct Rect r;
    char buf[30];
    int half, rem, acc, gap, lineh, width, left, maxw, h, top;
    int i, w, y, max, a, b;

    LessonTemp = 1;
    half = g_3DB2 == 320 ? 1 : 2;
    f_20E8_04B6(0x1700);
    f_1FD2_057F();
    win_GetObjRect(0x1702, &r);
    clip_SubInclude(&r);
    if (g_3DB2 == 320)
        font_SetFont(0);
    else
        font_SetFont(2);
    maxw = 0;
    for (i = '0'; i <= '9'; i++) {
        w = font_CharWidth(i);
        if (w > maxw)
            maxw = w;
    }
    left = maxw * 4 + r.left + 2;
    width = r.right - left;
    lineh = font_FontHeight();
    if (g_3DB2 == 320)
        lineh--;
    gap = r.bottom - lineh * 12 - r.top;
    if (g_3DB2 != 320)
        gap += 3;
    rem = gap % 5;
    acc = 0;
    gap /= 5;
    h = lineh;
    y = top = r.top;
    max = 1;
    for (i = 1; i < 6; i++) {
        if (CastePopB[i] > max)
            max = CastePopB[i];
        if (CastePopR[i] > max)
            max = CastePopR[i];
    }
    for (i = 0; i < 6; i++, y += lineh * 2 + gap) {
        acc += rem;
        if (acc > 5) {
            y++;
            acc -= 5;
        }
        if (i == 5)
            y--;
        a = CastePopB[i] * (long)width / max;
        b = CastePopR[i] * (long)width / max;
        win_SetColorFromObjNum(0x1703);
        sprintf(buf, "%d", CastePopB[i]);
        font_PrintStr(r.left, y, buf);
        if (i)
            (*g_9134)(left, half / 2 + y, left + a, h - half + y, _foreColor);
        win_SetColorFromObjNum(0x1704);
        sprintf(buf, "%d", CastePopR[i]);
        font_PrintStr(r.left, h + y, buf);
        if (i)
            (*g_9134)(left, half / 2 + h + y, left + b, h * 2 - half + y, _foreColor);
    }
    font_SetFont(0);
    f_1FD2_057F();
    do
        f_218D_03E8();
    while (f_22BF_09B0(0x1700) && f_1FD2_0598());
    f_20E8_0635(0x1700);
}


extern int far GamePaused;
extern int far CurGameTool;
extern void far f_15D9_009C(void far *text, long pos, int mode);

void far SetDefaultWindPrompt(int mode)
{
    if (GamePaused == 0)
        f_15D9_009C(0L, -2L, mode);
    else if (CurGameTool == -1)
        f_15D9_009C(WindPromptStrs[2], -2L, mode);
    else if (CurGameTool == 10)
        f_15D9_009C(WindPromptStrs[3], -2L, mode);
    else if (CurGameTool == 11)
        f_15D9_009C(WindPromptStrs[17], -2L, mode);
}

extern int far OptionStates[];
extern char far * far * far f_075B_0242(int object);
void far PictureDialog(char far * far *, int, int, int);
extern void far free(char far * far *block);
extern void far db_PurgeObject(int object, int kind);

void far PictStrnDialog(int picture, int object, int force)
{
    int count;
    char far * far *strings;

    WinPrintf("StrnID=%d", object);
    if (force || OptionStates[3]) {
        count = 0;
        strings = f_075B_0242(object);
        if (strings)
            while (strings[count])
                count++;
        PictureDialog(strings, count, picture, force);
        if (strings) {
            free(strings);
            db_PurgeObject(object, 4);
        }
    }
}

extern void far gr_BitMapSize(struct Pt far *size, int id);
extern int far font_StringWidth(char far *text);
extern int near g_3DB4;
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far gr_CenterStrInRect(struct Rect far *rect, char far *text);
extern void far f_00F8_02F7(int);
extern int far f_00F8_05F2(void);

void far PictureDialog(char far * far *strings, int count, int picture, int force)
{
    struct Pt size;
    int lineh, h, maxw, i, w;
    struct Rect r;
    struct Event ev;

    if (g_3DB2 == 320)
        font_SetFont(3);
    else
        font_SetFont(4);
    lineh = font_FontHeight();
    if (picture)
        gr_BitMapSize(&size, picture);
    h = (picture ? size.v + 2 : 0) + count * lineh + 8;
    maxw = 50;
    for (i = 0; i < count; i++) {
        w = font_StringWidth(strings[i]);
        if (w > maxw)
            maxw = w;
    }
    maxw += 8;
    r.top = (g_3DB4 - h) / 2;
    r.bottom = r.top + h;
    r.left = (g_3DB2 - maxw) / 2;
    r.right = r.left + maxw;
    f_20E8_04B6(0x1e00, r.left, r.top, r.right, r.bottom);
    WinPrintf("Pict=%d", picture);
    if (picture) {
        win_DrawBitMap((r.left + r.right - size.h) / 2, r.top, picture);
        r.top += size.v + 2;
    }
    if (g_3DB2 == 320)
        font_SetFont(3);
    else
        font_SetFont(4);
    win_SetColorFromObjNum(0x1e01);
    for (i = 0; i < count; i++) {
        r.bottom = r.top + lineh;
        gr_CenterStrInRect(&r, strings[i]);
        WinPrintf("line %d:%s", i, strings[i]);
        r.top += lineh;
    }
    f_00F8_02F7(15);
    while (!f_00F8_05F2() && f_22BF_09B0(0x1e00)) {
        if (f_218D_03F1(&ev) && !(ev.code & 0x8000))
            break;
    }
    f_20E8_0635(0x1e00);
    WinPrintf("PictStrnDialog: %d", picture);
    font_SetFont(0);
}


extern int far BlackWon;
extern void far f_00DF_00B1(int id, int arg);
extern char far * far * far fd_50F6_0328;
extern int far f_00DF_0138(void);
extern int far SRand2(void);
extern int far o15_384C_03C6(int a);
extern void far o15_384C_01EE(void);

void far EndGameDialog(void)
{
    int scores[8];
    long score, s;
    int level, played;

    if (OptionStates[1]) {
        if (BlackWon == 0)
            f_00DF_00B1(0x271a, 0x7e);
        else if (CurGameType == 2)
            f_00DF_00B1(0x2718, 0x7e);
        else
            f_00DF_00B1(0x2718, 0x7e);
    }
    score = CalcScore(scores);
    s = CurGameType == 2 ? score / 5 : score;
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
    if (BlackWon == 0)
        level += 5;
    f_20E8_04B6(0x400);
    if (g_3DB2 == 320)
        font_SetFont(2);
    else
        font_SetFont(4);
    f_22BF_0D53(0x402, fd_50F6_0324[CurGameType]);
    f_22BF_0D53(0x403, "%ld", score);
    f_22BF_0D53(0x404, fd_50F6_0328[level]);
    played = 0;
    font_SetFont(0);
    f_00F8_02F7(100);
    while (f_22BF_09B0(0x400)) {
        if (f_218D_03E8() || f_00F8_05F2())
            f_20E8_0635(0x400);
        if (f_00DF_0138() && !played) {
            played++;
            f_00DF_00B1(SRand2() + 0x2713, 0x7e);
        }
    }
    if (o15_384C_03C6(0) < 0)
        o15_384C_01EE();
}

extern void _fastcall f_22BF_0967(int obj, int bitmap);
extern void far myBeginSound(int sound, int a, int b);
extern long far f_00F8_02BE(void);
extern int far AnTab[];
extern void far f_00F8_0265(long ticks);
extern int far SRand1(int range);

void far SpiderDialog(void)
{
    struct Rect r;
    long t;
    int bmp, frame;

    f_23AE_0377(0x1a00);
    bmp = 0x2ee0;
    f_22BF_0967(0x1a01, bmp);
    f_20E8_04B6(0x1a00);
    win_GetObjRect(0x1a01, &r);
    frame = 0;
    myBeginSound(0x2d, frame, 0x7e);
    f_00F8_02BE();
    t = f_00F8_02BE() + 8;
    f_00F8_02F7(8);
    if (g_3DB2 != 320) {
        r.left += 0x2e;
        r.top += 0x4d;
    }
    while (!f_00F8_05F2()) {
        if (f_218D_03E8())
            break;
        if (f_00F8_02BE() >= t) {
            t = f_00F8_02BE() + 8;
            frame++;
            if (frame > 3) {
                frame = 0;
                myBeginSound(0x2d, frame, 0x7e);
            }
            bmp = AnTab[frame] + 0x2ee1;
            win_DrawBitMap(r.left, r.top, bmp);
        }
        f_00F8_0265(1L);
    }
    frame = SRand1(2) ? 0x2740 : 0x273f;
    if (bmp)
        win_DrawBitMap(r.left, r.top, bmp);
    PictStrnDialog(0, frame, 1);
    f_218D_042B();
    f_23AE_01DB(0x1a00);
    f_20E8_0635(0x1a00);
}


extern char far * far * far db_LoadObject(int object, int kind);
extern char far * far mem_Lock(char far * far *handle);
extern char far * far * far fd_50F6_3836;
extern char far * far * far fd_50F6_3938;
extern char far * far * far fd_50F6_3934;
extern int far kbd_poll_bios_key(void);
extern void far kbd_read_key_code(void);
extern void far mem_Unlock(char far * far *handle);
extern void far db_ReleaseHandle(char far * far *handle);

void far CustomerIDDialog(void)
{
    char far * far *h83;
    char far * far *h84;
    char far *strings[6];

    h83 = db_LoadObject(0x83, 10);
    h84 = db_LoadObject(0x84, 10);
    strings[0] = mem_Lock(h83);
    strings[1] = mem_Lock(fd_50F6_3836);
    strings[2] = mem_Lock(fd_50F6_3938);
    strings[3] = " ";
    strings[4] = mem_Lock(h84);
    strings[5] = mem_Lock(fd_50F6_3934);
    f_218D_042B();
    while (kbd_poll_bios_key())
        kbd_read_key_code();
    PictureDialog(strings, 6, 0, 1);
    mem_Unlock(h83);
    mem_Unlock(h84);
    mem_Unlock(fd_50F6_3836);
    mem_Unlock(fd_50F6_3934);
    db_ReleaseHandle(h83);
    db_ReleaseHandle(h84);
}
