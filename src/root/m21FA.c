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
extern void _fastcall f_23AE_0377(int win);
extern void _fastcall f_23AE_01DB(int win);
extern char far * _fastcall f_2505_02D7(int obj);
extern void _fastcall f_2505_0288(int obj, struct Rect far *rect);
extern void far f_1E57_0DAA(void);
extern void far f_1E57_0773(char far *obj);
extern void far f_1E57_0EB9(void);
extern void _fastcall f_23E6_0392(char far *obj);
extern void _fastcall f_23E6_066C(char far *obj);
extern void _fastcall f_259D_02A5(int id, struct Rect far *rect);
extern char far * far _fstrchr(char far *s, int c);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_208F_0419(struct Pt far *size, int id);
extern int _fastcall f_259D_000E(int x, int y, int id);
extern void _fastcall f_23AE_036F(int win);
extern char far * far f_2505_0006(int win);
extern int far sprintf(char far *buffer, char far *format, ...);
extern void far f_1E57_0296(void);
extern void far f_1E57_0A9C(char far *p);
extern void far f_1E57_0174(int win);
extern void far f_1E57_0362(void);
extern void far f_1E57_0AAF(struct Rect far *rect);
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
extern void (far * far fd_50F6_47DE[])(int phase);
extern char far fd_50F6_46E2[][6];
extern void (far * near g_9128)(int fore, int back, int pattern);
extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern void (far * near g_9138)(int left, int top, int right, int bottom, int mode);

static char far *colorEntry;

void _fastcall f_21FA_0002(int mode, struct Rect far *rect, char far *text)
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

void _fastcall f_21FA_00EE(int color)
{
    colorEntry = fd_50F6_46E2[color];
    if ((g_5A97 & 1) == 0)
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void _fastcall f_21FA_0144(char far *obj)
{
    if (obj[0x24] & 4)
        colorEntry = fd_50F6_46E2[obj[0x27]];
    else
        colorEntry = fd_50F6_46E2[obj[0x26]];
    if ((g_5A97 & 1) == 0)
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void _fastcall f_21FA_01AD(int obj)
{
    f_23AE_0377(obj);
    f_21FA_0144(f_2505_02D7(obj));
    f_23AE_01DB(obj);
}

void _fastcall f_21FA_01D0(struct Rect far *rect)
{
    if (colorEntry[2] != colorEntry[3] && (g_5A97 & 1) == 0) {
        (*g_9128)(colorEntry[3] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
        (*g_9138)(rect->left, rect->top, rect->right, rect->bottom, 0);
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    } else
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
}

void _fastcall f_21FA_0260(int obj, int color)
{
    struct Rect r;

    f_2505_0288(obj, &r);
    f_1CE2_046D(&r, color);
}

void _fastcall f_21FA_0286(int width, struct Rect far *rect)
{
    f_21FA_01D0(rect);
    f_1CE2_044D(rect, width);
}

void far f_21FA_02A8(struct Rect far *rect, int width)
{
    f_1CE2_044D(rect, width);
}

void far f_21FA_02BD(struct Rect far *rect, int width)
{
    struct Sides sides;

    sides.left = 0;
    sides.right = 0;
    sides.top = 1;
    sides.bottom = 1;
    f_1CE2_09E2(rect, width, sides, g_3DE0, g_3DE0);
}

void far f_21FA_02E9(struct Rect far *rect, int width)
{
    struct Sides sides;

    sides.left = 1;
    sides.right = 1;
    sides.top = 0;
    sides.bottom = 0;
    f_1CE2_09E2(rect, width, sides, g_3DE0, g_3DE0);
}

void _fastcall f_21FA_0315(char far *obj)
{
    struct Rect far *rect;
    char far *entry;
    struct Sides sides;
    int i;

    rect = (struct Rect far *)obj;
    entry = fd_50F6_46E2[obj[0x26]];
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

/* Unclaimed draft below (f_21FA_0413): bytes exact, but the FIXUPP order inside the
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

void _fastcall f_21FA_0413(struct WinObj far *obj)
{
    char far * far *h;
    char far *text;
    char far *p;
    struct Rect far *rect;

    rect = (struct Rect far *)obj;
    f_21FA_0144((char far *)obj);
    if (obj->flags & 0x200) {
        f_1E57_0DAA();
        f_1E57_0773((char far *)obj);
    }
    switch (obj->type) {
    case 0:
        f_21FA_0286(*(char far *)&obj->data[1], rect);
        break;
    case 2:
        f_21FA_01D0(rect);
        break;
    case 4:
        f_23E6_0392((char far *)obj);
        break;
    case 5:
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
        f_21FA_0315((char far *)obj);
        f_21FA_0144((char far *)obj);
    case 9:
    plainText:
        text = (char far *)obj + 0x2a;
        goto drawText;
    case 6:
        f_259D_02A5(obj->data[1], (struct Rect far *)obj);
        break;
    case 7:
    case 8:
        f_23E6_066C((char far *)obj);
        break;
    case 12:
        f_21FA_01D0(rect);
        (*g_9134)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto plainText;
    case 13:
        f_259D_02A5(*(int far *)((char far *)obj->data + ((obj->flags & 4) ? 2 : 4)), (struct Rect far *)obj);
        break;
    case 15:
        f_21FA_02A8(rect, *(char far *)&obj->data[1]);
        break;
    case 17:
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
        f_21FA_0315((char far *)obj);
        f_21FA_0144((char far *)obj);
    case 16:
    formatText:
        f_24AB_02AD(*(char far *)&obj->data[1]);
        if (*(char far * far * far *)&obj->data[2] == 0) {
            text = (char far *)obj + 0x2e;
            if (g_6300 == 0 && _fstrchr(text, '%') != 0)
                goto doneText;
        drawText:
            f_24AB_02AD(*(char far *)&obj->data[1]);
            f_21FA_0002(((unsigned)obj->flags & 0x180) >> 7, rect, text);
        } else {
            h = *(char far * far * far *)&obj->data[2];
            p = f_171C_1B84(h);
            f_21FA_0002(((unsigned)obj->flags & 0x180) >> 7, rect, p);
            f_171C_1BBA(h);
        }
    doneText:
        f_24AB_02AD(0);
        break;
    case 18:
        f_21FA_01D0(rect);
        (*g_9134)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto formatText;
    case 19:
        f_21FA_02E9(rect, *(char far *)&obj->data[1]);
        break;
    case 20:
        f_21FA_02BD(rect, *(char far *)&obj->data[1]);
        break;
    case 21:
        f_21FA_01D0(rect);
        f_21FA_02E9(rect, *(char far *)&obj->data[1]);
        break;
    case 22:
        f_21FA_01D0(rect);
        f_21FA_02BD(rect, *(char far *)&obj->data[1]);
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
        f_1E57_0EB9();
}

void _fastcall f_21FA_0741(struct WinObj far *obj)
{
    if (obj->flags & 1)
        f_21FA_0413(obj);
}

void _fastcall f_21FA_075A(int objNum)
{
    f_23AE_0377(objNum);
    f_21FA_0413((struct WinObj far *)f_2505_02D7(objNum));
    f_23AE_01DB(objNum);
}

void _fastcall f_21FA_077D(char far *w)
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
        f_259D_000E(rect.left, rect.top, 0x64);
        f_208F_0419(&size, 0x64);
        rect.left += size.x;
    }
    if (*(int far *)(w + 0x1c) & 8) {
        f_208F_0419(&size, 0x70);
        f_259D_000E(rect.right - size.x, rect.bottom - size.y, 0x70);
    }
    if (*(int far *)(w + 0x1c) & 0x100) {
        if (*(int far *)(w + 0x1c) & 0x80) {
            f_208F_0419(&size, 0x66);
            rect.right -= size.x;
            f_259D_000E(rect.right, rect.top, 0x66);
        } else {
            f_208F_0419(&size, 0x67);
            rect.right -= size.x;
            f_259D_000E(rect.right, rect.top, 0x67);
        }
    }
    if (*(int far *)(w + 0x1c) & 0x10)
        f_259D_000E(rect.left, rect.top, 0x65);
    if (*(int far *)(w + 0x1c) & 0x400) {
        f_208F_0419(&size, 0x69);
        rect.right -= size.x;
        f_259D_000E(rect.right, rect.top, 0x69);
    }
}

/* Unclaimed draft: bytes exact; the original object breaks its LEDATA record between
 * 0A35 and 0A55 (sprintf relocation group order). */
void _fastcall f_21FA_08E2(int win)
{
    char buf[40];
    char far *w;
    int n;
    int i;

    sprintf(buf, "!!W:%x", win);
    f_23AE_036F(win);
    sprintf(buf, "QQW:%x", win);
    w = f_2505_0006(win);
    if ((*(int far *)(w + 0x1c) & 0x20) == 0) {
        if (g_5AAC == 0 || g_5AAC[1] != (int)0x8000) {
            sprintf(buf, "##W:%x", win);
            if (fd_50F6_47DE[win >> 8])
                (*fd_50F6_47DE[win >> 8])(1);
            sprintf(buf, "**W:%x", win);
            n = *(int far *)(w + 0xc);
            for (i = 0; i < n; i++) {
                sprintf(buf, "w:%x, i:%x", win, i);
                f_21FA_0741(((struct WinObj far * far *)(w + 0x2c))[i]);
                if (i == 0)
                    *(struct Rect far *)w = *((struct Rect far * far *)(w + 0x2c))[0];
                sprintf(buf, "xxw:%x, i:%x", win, i);
            }
            sprintf(buf, "zzw:%x, i:%x", win, i);
            f_21FA_077D(w);
        }
        sprintf(buf, "ppw:%x, i:%x", win, i);
        if (fd_50F6_47DE[win >> 8])
            (*fd_50F6_47DE[win >> 8])(2);
    }
    sprintf(buf, "%%w:%x, i:%x", win, i);
    f_23AE_01DB(win);
}

void _fastcall f_21FA_0AA7(int win)
{
    f_21FA_075A(win);
    f_23AE_0377(win);
    f_21FA_077D(f_2505_0006(win));
    f_23AE_01DB(win);
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
        f_1E57_0174(g_5702[i]);
        f_1E57_0A9C(p);
        f_21FA_08E2(g_5702[i]);
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
        f_2505_0288(g_5702[0], &r);
        f_1E57_0AAF(&r);
    }
    f_1FD2_05FD();
    for (i = 0; g_5702[i] != (int)0x8000; i++)
        ;
    while (--i >= 1) {
        f_1E57_0174(g_5702[i]);
        sprintf(buf, "i:%x", i);
        f_1E57_0A9C(p);
        sprintf(buf, "!!i:%x", i);
        f_1E57_0AAF(&r);
        sprintf(buf, "@@i:%x", i);
        f_21FA_08E2(g_5702[i]);
    }
    if (g_5702[0] != (int)0x8000) {
        f_1E57_0174(g_5702[0]);
        f_21FA_08E2(g_5702[0]);
    }
    f_1E57_0362();
}
