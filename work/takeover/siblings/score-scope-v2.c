/* Overlay section S14, code frame 384C: score, scenario and picture dialogs.
 *
 * Source-form evidence (worker resF):
 *  - Every font choice is written `if (g_3DB2 == 320) f_24AB_02AD(a); else f_24AB_02AD(b);`
 *    (six sites).  The two calls are cross-jumped into the same bytes as a `?:` argument, but
 *    each if/else adds two /Zi line entries; with all six the 52-entry LINNUM flushes land where
 *    the oracle's relocation order needs record breaks (DrawCastePopUp, PictureDialog,
 *    SpiderDialog: 0 violations of 115 order constraints).
 *  - Identifier counts (symbol-table state, periodic mod 17) are set only by named prototype
 *    parameters: the forward prototypes of CalcScore/DoWinHelp/SetDefaultWindPrompt/
 *    PictStrnDialog are named (+6, CalcScore operand order), g_9134's and PictureDialog's forward
 *    declaration are unnamed (-5 before DrawCastePopUp, -4 before PictureDialog).  Which
 *    prototypes carry names is a byte-equivalent unknown; only the counts are fixed by the bytes.
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


extern int far fd_50F6_04F4;
extern int far fd_3D57_0828;
extern int far fd_50F6_073C[64];
extern int far fd_50F6_0626[64];
extern int far fd_50F6_06AE[64];
extern long far fd_50F6_0FC2;
extern long far fd_50F6_1000;
extern int far fd_50F6_09FA;
extern int far fd_50F6_0A00;
extern int far fd_50F6_0EAC;
extern int far fd_50F6_0A90;
extern int far fd_50F6_0AC4;
extern int far fd_50F6_0A9E;
extern unsigned char far fd_3D57_00A4[12][16];
extern int far MeHealth;
extern long far fd_50F6_0C26;

static char weights[8] = { 13, 17, 19, 23, 29, 31, 37, 41 };

long far CalcScore(int far *scores)
{
    int i, j, k, n, t;
    int sum;
    long score, q;

    for (i = 0; i < 8; i++)
        scores[i] = 0;

    k = (fd_50F6_04F4 - fd_3D57_0828) & 0x3f;
    sum = 0;
    for (i = 0; i < fd_3D57_0828; i++) {
        sum += fd_50F6_073C[k];
        k = (k + 1) & 0x3f;
    }
    if (i > 0)
        scores[0] = sum / i;
    else
        scores[0] = 0;

    {
    int j;
    int sum2;
    int sum;
    j = (fd_50F6_04F4 - fd_3D57_0828) & 0x3f;
    sum = sum2 = 0;
    for (k = 0; k < fd_3D57_0828; k++) {
        sum += fd_50F6_0626[j];
        sum2 += fd_50F6_06AE[j];
        j = (j + 1) & 0x3f;
    }
    j = sum2 + sum;
    if (j > 0)
        scores[1] = (long)sum * 100 / j;
    else
        scores[1] = 0;

    }

    if (fd_50F6_0FC2 > 0)
        scores[2] = (fd_50F6_0FC2 - fd_50F6_1000) * 100 / fd_50F6_0FC2;
    else
        scores[2] = 100;

    n = fd_50F6_09FA + fd_50F6_0A00;
    if (n > 0)
        scores[3] = fd_50F6_09FA * 100 / n;
    else
        scores[3] = 100;

    if (fd_50F6_0EAC == 2 || fd_50F6_0EAC == 3) {
        n = fd_50F6_0AC4 + fd_50F6_0A90;
        if (n > 0)
            scores[4] = (long)fd_50F6_0A90 * 100 / n;
        else
            scores[4] = 100;
        n = fd_50F6_0A9E + fd_50F6_0A90;
        if (n > 0)
            scores[5] = (long)fd_50F6_0A90 * 100 / n;
        else
            scores[5] = 100;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = j < 5 ? 3 : 2; k < 12; k++)
                if (fd_3D57_00A4[k][j])
                    sum++;
        if (sum > 0)
            scores[6] = (long)sum * 100 / 155;
        else
            scores[6] = 0;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = 0; k < 2 || (j < 5 && k < 3); k++)
                if (fd_3D57_00A4[k][j])
                    sum++;
        if (sum > 0)
            scores[7] = (long)sum * 100 / 37;
        else
            scores[7] = 0;
    }

    score = MeHealth;
    for (k = 0; k < 8; k++)
        score += (long)scores[k] * weights[k] * 51;

    if (fd_50F6_0EAC != 2) {
        score = score * 29 / 10;
        if (fd_50F6_0C26 < 4100) {
            q = fd_50F6_0C26 / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 41;
        }
    } else {
        if (fd_50F6_0C26 < 8100) {
            q = fd_50F6_0C26 / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 81;
        }
        score *= 5;
    }
    return fd_50F6_0C26 + score;
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
extern int _fastcall f_22BF_0AEF(int win);
extern void far clip_SetWin(int win);
extern void _fastcall f_22BF_0498(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void _fastcall f_2505_08EA(int win);
extern void far f_1FD2_057F(void);
extern int far f_218D_03E8(void);
extern int _fastcall f_22BF_09B0(int win);
extern int far f_1FD2_0598(void);
extern void _fastcall f_22BF_04A0(int obj);
extern void _fastcall f_2505_0831(int win);
extern void far clip_SubInclude(struct Rect far *rect);
extern void (far * far g_62E0)(int win);
extern void _fastcall f_21FA_08E2(int win);
extern int _fastcall f_22BF_0B25(int win);
extern void far f_1E57_0362(void);
extern void _fastcall f_23AE_01DB(int win);

void far DoWinHelp(int win)
{
    int shown;
    struct Rect r;

    f_23AE_0377(win);
    shown = f_22BF_0AEF(win);
    clip_SetWin(win);
    f_22BF_0498(win);
    win_GetObjRect(win, &r);
    win_DrawObjectNum(win);
    f_2505_08EA(win);
    f_218D_042B();
    f_1FD2_057F();
    while (!f_218D_03E8()) {
        if (!f_22BF_09B0(win) || !f_1FD2_0598())
            break;
    }
    f_218D_042B();
    f_22BF_04A0(win);
    if (f_22BF_09B0(win)) {
        f_2505_0831(win);
        clip_SubInclude(&r);
        (*g_62E0)(win);
        f_21FA_08E2(win);
    }
    if (!shown)
        f_22BF_0B25(win);
    f_1E57_0362();
    f_23AE_01DB(win);
}

extern long far fd_50F6_0ADA;
extern void far f_22BF_059A(int obj, ...);
extern char far * far * far fd_50F6_034C;
extern int near g_3DB2;
extern void far f_24AB_02AD(int font);
extern void far f_22BF_0D53(int obj, char far *format, ...);
extern char far * far * far fd_50F6_0368;
extern char far * far * far fd_50F6_0324;

void far ScoreDialog(void)
{
    int scores[8];
    struct Event ev;
    char title[80];
    int i;

    fd_50F6_0ADA = CalcScore(scores);
    f_23AE_0377(0x1800);
    for (i = 0; i < 4; i++)
        f_22BF_059A(0x1802 + i, scores[i]);
    f_22BF_059A(0x180c, fd_50F6_034C[14]);
    f_218D_042B();
    f_20E8_04B6(0x1800);
    if (g_3DB2 == 320)
        f_24AB_02AD(0);
    else
        f_24AB_02AD(4);
    if (fd_50F6_0EAC == 2) {
        for (i = 4; i < 8; i++)
            f_22BF_0D53(0x1802 + i, "%d%%", scores[i]);
    } else {
        for (i = 4; i < 8; i++)
            f_22BF_0D53(0x1802 + i, fd_50F6_0368[16]);
    }
    if (g_3DB2 == 320)
        f_24AB_02AD(3);
    else
        f_24AB_02AD(4);
    if (fd_50F6_0EAC == 3) {
        f_22BF_0D53(0x180a, fd_50F6_0368[17]);
        f_22BF_0D53(0x180b, fd_50F6_0368[18]);
        ev.code = 0;
    } else {
        title[0] = 0;
        _fstrcat(title, fd_50F6_0368[13]);
        _fstrcat(title, fd_50F6_0324[fd_50F6_0EAC]);
        _fstrcat(title, fd_50F6_0368[14]);
        f_22BF_0D53(0x180a, title);
        f_22BF_0D53(0x180b, "%ld", fd_50F6_0ADA);
        ev.code = 0;
    }
    f_24AB_02AD(0);
    while (f_22BF_09B0(0x1800)) {
        if (f_218D_03F1(&ev) && !(ev.code & 0x8000))
            break;
    }
    f_20E8_0635(0x1800);
    f_218D_042B();
    f_23AE_01DB(0x1800);
}

extern int far fd_50F6_1074;
extern int far f_24AB_0367(int c);
extern int far f_24AB_030B(void);
extern int far fd_50F6_0AEC[];
extern int far fd_50F6_0AFA[];
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far f_24AB_038D(int x, int y, char far *text);
extern int near g_3DE0;
extern void (far * near g_9134)(int, int, int, int, int);

void far DrawCastePopUp(void)
{
    struct Rect r;
    char buf[30];
    int half, rem, acc, gap, lineh, width, left, maxw, h, top;
    int i, w, y, max, a, b;

    fd_50F6_1074 = 1;
    half = g_3DB2 == 320 ? 1 : 2;
    f_20E8_04B6(0x1700);
    f_1FD2_057F();
    win_GetObjRect(0x1702, &r);
    clip_SubInclude(&r);
    if (g_3DB2 == 320)
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
        if (fd_50F6_0AEC[i] > max)
            max = fd_50F6_0AEC[i];
        if (fd_50F6_0AFA[i] > max)
            max = fd_50F6_0AFA[i];
    }
    for (i = 0; i < 6; i++, y += lineh * 2 + gap) {
        acc += rem;
        if (acc > 5) {
            y++;
            acc -= 5;
        }
        if (i == 5)
            y--;
        a = fd_50F6_0AEC[i] * (long)width / max;
        b = fd_50F6_0AFA[i] * (long)width / max;
        win_SetColorFromObjNum(0x1703);
        sprintf(buf, "%d", fd_50F6_0AEC[i]);
        f_24AB_038D(r.left, y, buf);
        if (i)
            (*g_9134)(left, half / 2 + y, left + a, h - half + y, g_3DE0);
        win_SetColorFromObjNum(0x1704);
        sprintf(buf, "%d", fd_50F6_0AFA[i]);
        f_24AB_038D(r.left, h + y, buf);
        if (i)
            (*g_9134)(left, half / 2 + h + y, left + b, h * 2 - half + y, g_3DE0);
    }
    f_24AB_02AD(0);
    f_1FD2_057F();
    do
        f_218D_03E8();
    while (f_22BF_09B0(0x1700) && f_1FD2_0598());
    f_20E8_0635(0x1700);
}


extern int far fd_50F6_047E;
extern int far fd_50F6_105E;
extern void far f_15D9_009C(void far *text, long pos, int mode);

void far SetDefaultWindPrompt(int mode)
{
    if (fd_50F6_047E == 0)
        f_15D9_009C(0L, -2L, mode);
    else if (fd_50F6_105E == -1)
        f_15D9_009C(fd_50F6_034C[2], -2L, mode);
    else if (fd_50F6_105E == 10)
        f_15D9_009C(fd_50F6_034C[3], -2L, mode);
    else if (fd_50F6_105E == 11)
        f_15D9_009C(fd_50F6_034C[17], -2L, mode);
}

extern int far fd_3D57_07A8[];
extern char far * far * far f_075B_0242(int object);
void far PictureDialog(char far * far *, int, int, int);
extern void far free(char far * far *block);
extern void far db_PurgeObject(int object, int kind);

void far PictStrnDialog(int picture, int object, int force)
{
    int count;
    char far * far *strings;

    WinPrintf("StrnID=%d", object);
    if (force || fd_3D57_07A8[3]) {
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

extern void far f_208F_0419(struct Pt far *size, int id);
extern int far f_24AB_0329(char far *text);
extern int near g_3DB4;
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far f_208F_0093(struct Rect far *rect, char far *text);
extern void far f_00F8_02F7(int ticks);
extern int far f_00F8_05F2(void);

void far PictureDialog(char far * far *strings, int count, int picture, int force)
{
    struct Pt size;
    int lineh, h, maxw, i, w;
    struct Rect r;
    struct Event ev;

    if (g_3DB2 == 320)
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
    f_00F8_02F7(15);
    while (!f_00F8_05F2() && f_22BF_09B0(0x1e00)) {
        if (f_218D_03F1(&ev) && !(ev.code & 0x8000))
            break;
    }
    f_20E8_0635(0x1e00);
    WinPrintf("PictStrnDialog: %d", picture);
    f_24AB_02AD(0);
}


extern int far fd_50F6_0366;
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

    if (fd_3D57_07A8[1]) {
        if (fd_50F6_0366 == 0)
            f_00DF_00B1(0x271a, 0x7e);
        else if (fd_50F6_0EAC == 2)
            f_00DF_00B1(0x2718, 0x7e);
        else
            f_00DF_00B1(0x2718, 0x7e);
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
    if (fd_50F6_0366 == 0)
        level += 5;
    f_20E8_04B6(0x400);
    if (g_3DB2 == 320)
        f_24AB_02AD(2);
    else
        f_24AB_02AD(4);
    f_22BF_0D53(0x402, fd_50F6_0324[fd_50F6_0EAC]);
    f_22BF_0D53(0x403, "%ld", score);
    f_22BF_0D53(0x404, fd_50F6_0328[level]);
    played = 0;
    f_24AB_02AD(0);
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
extern int far fd_3D57_09B4[];
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
            bmp = fd_3D57_09B4[frame] + 0x2ee1;
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
extern char far * far f_171C_1B84(char far * far *handle);
extern char far * far * far fd_50F6_3836;
extern char far * far * far fd_50F6_3938;
extern char far * far * far fd_50F6_3934;
extern int far f_1F58_0038(void);
extern void far f_1F58_0090(void);
extern void far f_171C_1BBA(char far * far *handle);
extern void far db_ReleaseHandle(char far * far *handle);

void far CustomerIDDialog(void)
{
    char far * far *h83;
    char far * far *h84;
    char far *strings[6];

    h83 = db_LoadObject(0x83, 10);
    h84 = db_LoadObject(0x84, 10);
    strings[0] = f_171C_1B84(h83);
    strings[1] = f_171C_1B84(fd_50F6_3836);
    strings[2] = f_171C_1B84(fd_50F6_3938);
    strings[3] = " ";
    strings[4] = f_171C_1B84(h84);
    strings[5] = f_171C_1B84(fd_50F6_3934);
    f_218D_042B();
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
