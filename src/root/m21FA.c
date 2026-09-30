/* Root module 21FA: DOS window-object drawing (partial). */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pt {
    int x;
    int y;
};

struct Sides {
    unsigned char left : 1;
    unsigned char top : 1;
    unsigned char right : 1;
    unsigned char bottom : 1;
};

extern int far f_24AB_030B(void);
extern int far f_24AB_0329(char far *text);
extern void far f_24AB_038D(int x, int y, char far *text);
extern void far f_24AB_02AD(int font);
extern void far f_1CE2_046D(struct Rect far *rect, int color);
extern void far f_1CE2_044D(struct Rect far *rect, int width);
extern void far f_1CE2_09E2(struct Rect far *rect, int width, struct Sides sides, int light, int dark);
extern void far f_1CE2_0278(struct Rect far *rect, int width, struct Sides sides, int color);
extern void far f_1CE2_0430(struct Rect far *rect);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_UnlockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_Push(void);
extern void far clip_SubInclude(char far *obj);
extern void far clip_Pop(void);
extern void _fastcall f_23E6_0392(char far *obj);
extern void _fastcall f_23E6_066C(char far *obj);
extern void _fastcall win_DrawBitMapAtObj(int id, struct Rect far *rect);
extern char far * far _fstrchr(char far *s, int c);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_208F_0419(struct Pt far *size, int id);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void _fastcall win_LockWinHigh(int win);
extern char far * far f_2505_0006(int win);
extern int far sprintf(char far *buffer, char far *format, ...);
extern void far f_1E57_0296(void);
extern void far f_1E57_0A9C(char far *p);
extern void far clip_SetWin(int win);
extern void far f_1E57_0362(void);
extern void far clip_SubExclude(struct Rect far *rect);
extern void far f_1FD2_05FD(void);
extern void far f_171C_1BBA(char far * far *handle);

extern char near g_5A97;
extern int near g_3DE0;
extern char near g_3DDC;
extern int near g_3DE2;
extern int g_3DA0;
extern int g_6300;
extern int g_5702[];
extern int near g_3DB2;
extern int far * near g_5AAC;
extern void (far * far win_drawHooks[])(int phase);
extern char far win_colors[][6];
extern void (far * near g_9128)(int fore, int back, int pattern);
extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern void (far * near g_9138)(int left, int top, int right, int bottom, int mode);

static char far *colorEntry;

void _fastcall gr_JustifyStrInRect(int mode, struct Rect far *rect, char far *text)
{
    struct Rect r;
    int x;

    r = *rect;
    switch (mode) {
    case 0:
    case 3:
        x = (r.left + (r.right - f_24AB_0329(text))) / 2;
        break;
    case 1:
        x = r.left + 4;
        break;
    case 2:
        x = r.right - f_24AB_0329(text) - 4;
        break;
    }
    if (r.left > x)
        x = r.left;
    r.top = (r.bottom + (r.top - f_24AB_030B())) / 2;
    f_24AB_038D(x, r.top, text);
    if (mode == 3) {
        (*g_9134)(g_3DA0, r.top, rect->right, r.top + g_3DDC, g_3DE2);
        (*g_9134)(rect->left, r.top, x, r.top + g_3DDC, g_3DE2);
    }
}

void _fastcall win_SetColorNum(int color)
{
    colorEntry = win_colors[color];
    if ((g_5A97 & 1) == 0)
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void _fastcall win_SetColorFromObj(char far *obj)
{
    if (obj[0x24] & 4)
        colorEntry = win_colors[obj[0x27]];
    else
        colorEntry = win_colors[obj[0x26]];
    if ((g_5A97 & 1) == 0)
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void _fastcall win_SetColorFromObjNum(int obj)
{
    win_LockWin(obj);
    win_SetColorFromObj(win_ObjAddr(obj));
    win_UnlockWin(obj);
}

void _fastcall win_RectFill(struct Rect far *rect)
{
    if (colorEntry[2] != colorEntry[3] && (g_5A97 & 1) == 0) {
        (*g_9128)(colorEntry[3] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
        (*g_9138)(rect->left, rect->top, rect->right, rect->bottom, 0);
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    } else
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
}

void _fastcall win_FillObjRect(int obj, int color)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    f_1CE2_046D(&r, color);
}

void _fastcall win_RectFillOutline(int width, struct Rect far *rect)
{
    win_RectFill(rect);
    f_1CE2_044D(rect, width);
}

void far win_RectOutline(struct Rect far *rect, int width)
{
    f_1CE2_044D(rect, width);
}

void far win_RectVOutline(struct Rect far *rect, int width)
{
    struct Sides sides;

    sides.left = 0;
    sides.right = 0;
    sides.top = 1;
    sides.bottom = 1;
    f_1CE2_09E2(rect, width, sides, g_3DE0, g_3DE0);
}

void far win_RectHOutline(struct Rect far *rect, int width)
{
    struct Sides sides;

    sides.left = 1;
    sides.right = 1;
    sides.top = 0;
    sides.bottom = 0;
    f_1CE2_09E2(rect, width, sides, g_3DE0, g_3DE0);
}

void _fastcall win_DrawButtonBorder(char far *obj)
{
    struct Rect far *rect;
    char far *entry;
    struct Sides sides;
    int i;

    rect = (struct Rect far *)obj;
    entry = win_colors[obj[0x26]];
    if ((obj[0x24] & 4) == 0) {
        for (i = 3; i > 0; i--) {
            sides.left = 1;
            sides.right = 1;
            sides.top = 0;
            sides.bottom = 0;
            f_1CE2_0278(rect, i, sides, entry[3] * 0x101);
            sides.left = 0;
            sides.right = 0;
            sides.top = 1;
            sides.bottom = 1;
            f_1CE2_09E2(rect, i, sides, entry[2] * 0x101, entry[3] * 0x101);
        }
    } else {
        (*g_9128)(entry[0] * 0x101, entry[0] * 0x101, entry[0] * 0x101);
        f_1CE2_044D(rect, 3);
        if ((g_5A97 & 1) == 0) {
            (*g_9128)(entry[3] * 0x101, entry[3] * 0x101, entry[1] * 0x101);
            f_1CE2_044D(rect, 2);
        }
    }
}

/* Unclaimed draft below (win_DrawObjectI): bytes exact, but the FIXUPP order inside the
 * f_1CE2_046D and f_24AB_02AD relocation groups differs (the original object had
 * LEDATA record breaks inside this function). */
struct WinObj {
    struct Rect rect;
    int origin[4];
    int ref[4];
    int mode[4];
    char unk20;
    char type;
    int size;
    int flags;
    int data[3];
};

void _fastcall win_DrawObjectI(struct WinObj far *obj)
{
    char far * far *h;
    char far *text;
    char far *p;
    struct Rect far *rect;

    rect = (struct Rect far *)obj;
    win_SetColorFromObj((char far *)obj);
    if (obj->flags & 0x200) {
        clip_Push();
        clip_SubInclude((char far *)obj);
    }
    switch (obj->type) {
    case 0:
        win_RectFillOutline(*(char far *)&obj->data[1], rect);
        break;
    case 2:
        win_RectFill(rect);
        break;
    case 4:
        f_23E6_0392((char far *)obj);
        break;
    case 5:
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
        win_DrawButtonBorder((char far *)obj);
        win_SetColorFromObj((char far *)obj);
    case 9:
    plainText:
        text = (char far *)obj + 0x2a;
        goto drawText;
    case 6:
        win_DrawBitMapAtObj(obj->data[1], (struct Rect far *)obj);
        break;
    case 7:
    case 8:
        f_23E6_066C((char far *)obj);
        break;
    case 12:
        win_RectFill(rect);
        (*g_9134)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto plainText;
    case 13:
        win_DrawBitMapAtObj(*(int far *)((char far *)obj->data + ((obj->flags & 4) ? 2 : 4)), (struct Rect far *)obj);
        break;
    case 15:
        win_RectOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 17:
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
        win_DrawButtonBorder((char far *)obj);
        win_SetColorFromObj((char far *)obj);
    case 16:
    formatText:
        f_24AB_02AD(*(char far *)&obj->data[1]);
        if (*(char far * far * far *)&obj->data[2] == 0) {
            text = (char far *)obj + 0x2e;
            if (g_6300 == 0 && _fstrchr(text, '%') != 0)
                goto doneText;
        drawText:
            f_24AB_02AD(*(char far *)&obj->data[1]);
            gr_JustifyStrInRect(((unsigned)obj->flags & 0x180) >> 7, rect, text);
        } else {
            h = *(char far * far * far *)&obj->data[2];
            p = f_171C_1B84(h);
            gr_JustifyStrInRect(((unsigned)obj->flags & 0x180) >> 7, rect, p);
            f_171C_1BBA(h);
        }
    doneText:
        f_24AB_02AD(0);
        break;
    case 18:
        win_RectFill(rect);
        (*g_9134)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto formatText;
    case 19:
        win_RectHOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 20:
        win_RectVOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 21:
        win_RectFill(rect);
        win_RectHOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 22:
        win_RectFill(rect);
        win_RectVOutline(rect, *(char far *)&obj->data[1]);
        break;
    }
    if (obj->flags & 4) {
        switch (obj->type) {
        case 1:
        case 6:
            f_1CE2_0430((struct Rect far *)obj);
            break;
        }
    }
    if (obj->flags & 0x200)
        clip_Pop();
}

void _fastcall win_DrawObject(struct WinObj far *obj)
{
    if (obj->flags & 1)
        win_DrawObjectI(obj);
}

void _fastcall win_DrawObjectNum(int objNum)
{
    win_LockWin(objNum);
    win_DrawObjectI((struct WinObj far *)win_ObjAddr(objNum));
    win_UnlockWin(objNum);
}

void _fastcall win_DrawWinIcons(char far *w)
{
    struct Rect rect;
    struct Pt size;
    int m;

    rect = *(struct Rect far *)w;
    m = (*(char far * far *)(w + 0x2c))[0x28];
    rect.bottom -= m;
    if (g_3DB2 == 0x140)
        m = m / 2;
    rect.left += m;
    rect.right -= m;
    rect.top += m;
    if (g_5A97 & 1)
        (*g_9128)(0, 0, 0x40);
    if (*(int far *)(w + 0x1c) & 4) {
        win_DrawBitMap(rect.left, rect.top, 0x64);
        f_208F_0419(&size, 0x64);
        rect.left += size.x;
    }
    if (*(int far *)(w + 0x1c) & 8) {
        f_208F_0419(&size, 0x70);
        win_DrawBitMap(rect.right - size.x, rect.bottom - size.y, 0x70);
    }
    if (*(int far *)(w + 0x1c) & 0x100) {
        if (*(int far *)(w + 0x1c) & 0x80) {
            f_208F_0419(&size, 0x66);
            rect.right -= size.x;
            win_DrawBitMap(rect.right, rect.top, 0x66);
        } else {
            f_208F_0419(&size, 0x67);
            rect.right -= size.x;
            win_DrawBitMap(rect.right, rect.top, 0x67);
        }
    }
    if (*(int far *)(w + 0x1c) & 0x10)
        win_DrawBitMap(rect.left, rect.top, 0x65);
    if (*(int far *)(w + 0x1c) & 0x400) {
        f_208F_0419(&size, 0x69);
        rect.right -= size.x;
        win_DrawBitMap(rect.right, rect.top, 0x69);
    }
}

/* Unclaimed draft: bytes exact; the original object breaks its LEDATA record between
 * 0A35 and 0A55 (sprintf relocation group order). */
void _fastcall win_DrawWindow(int win)
{
    char buf[40];
    char far *w;
    int n;
    int i;

    sprintf(buf, "!!W:%x", win);
    win_LockWinHigh(win);
    sprintf(buf, "QQW:%x", win);
    w = f_2505_0006(win);
    if ((*(int far *)(w + 0x1c) & 0x20) == 0) {
        if (g_5AAC == 0 || g_5AAC[1] != (int)0x8000) {
            sprintf(buf, "##W:%x", win);
            if (win_drawHooks[win >> 8])
                (*win_drawHooks[win >> 8])(1);
            sprintf(buf, "**W:%x", win);
            n = *(int far *)(w + 0xc);
            for (i = 0; i < n; i++) {
                sprintf(buf, "w:%x, i:%x", win, i);
                win_DrawObject(((struct WinObj far * far *)(w + 0x2c))[i]);
                if (i == 0)
                    *(struct Rect far *)w = *((struct Rect far * far *)(w + 0x2c))[0];
                sprintf(buf, "xxw:%x, i:%x", win, i);
            }
            sprintf(buf, "zzw:%x, i:%x", win, i);
            win_DrawWinIcons(w);
        }
        sprintf(buf, "ppw:%x, i:%x", win, i);
        if (win_drawHooks[win >> 8])
            (*win_drawHooks[win >> 8])(2);
    }
    sprintf(buf, "%%w:%x, i:%x", win, i);
    win_UnlockWin(win);
}

void _fastcall win_DrawTitle(int win)
{
    win_DrawObjectNum(win);
    win_LockWin(win);
    win_DrawWinIcons(f_2505_0006(win));
    win_UnlockWin(win);
}

void _fastcall f_21FA_0AD2(char far *p)
{
    int i;

    f_1E57_0296();
    f_1E57_0A9C(p);
    f_1FD2_05FD();
    for (i = 0; g_5702[i] != (int)0x8000; i++)
        ;
    while (--i >= 0) {
        clip_SetWin(g_5702[i]);
        f_1E57_0A9C(p);
        win_DrawWindow(g_5702[i]);
    }
    f_1E57_0362();
}

void _fastcall f_21FA_0B4B(char far *p)
{
    char buf[20];
    struct Rect r;
    int i;

    f_1E57_0296();
    f_1E57_0A9C(p);
    if (g_5702[0] != (int)0x8000) {
        win_GetObjRect(g_5702[0], &r);
        clip_SubExclude(&r);
    }
    f_1FD2_05FD();
    for (i = 0; g_5702[i] != (int)0x8000; i++)
        ;
    while (--i >= 1) {
        clip_SetWin(g_5702[i]);
        sprintf(buf, "i:%x", i);
        f_1E57_0A9C(p);
        sprintf(buf, "!!i:%x", i);
        clip_SubExclude(&r);
        sprintf(buf, "@@i:%x", i);
        win_DrawWindow(g_5702[i]);
    }
    if (g_5702[0] != (int)0x8000) {
        clip_SetWin(g_5702[0]);
        win_DrawWindow(g_5702[0]);
    }
    f_1E57_0362();
}
