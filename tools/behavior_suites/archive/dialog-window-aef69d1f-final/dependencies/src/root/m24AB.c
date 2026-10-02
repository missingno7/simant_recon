/* Root module 24AB: current-font text output (Win16 unit font_SetFont,
 * font_InitFonts, font_PrintStr; GR segment). */

typedef char far * far *Handle;

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Bitmap {
    int width;
    int height;
    char far *bits;
};

struct Pt {
    int x;
    int y;
};

void far *fd_55B3_65A4 = 0;

extern struct Bitmap far * far font_MakeImage(char far *s, int x, void far *font);
extern char near g_5A97;
extern Handle far f_171C_13CA(long size, int flags, char far *name);
extern char far * far f_171C_1B84(Handle h);
extern struct Bitmap far fd_50F6_392C;
extern void far f_24FA_0029(char far *dst, char far *src, int width, int height);
extern int near g_3DB2;
extern void far f_24FA_00A0(char far *bits, int size);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);
extern Handle far f_171C_1BBA(Handle h);

Handle far f_24AB_0002(char far *text)
{
    Handle h;
    char far *p;
    int bpr;
    int size;
    int i;
    char far *src;
    char far *dst;

    font_MakeImage(text, 0, fd_55B3_65A4);
    if ((g_5A97 & 1) == 0) {
        if (g_5A97 == 2) {
            h = f_171C_13CA((long)((fd_50F6_392C.width + 1) / 2 * fd_50F6_392C.height + 12), 1, "fontBuf");
            p = f_171C_1B84(h);
            f_24FA_0029(p + 12, fd_50F6_392C.bits, fd_50F6_392C.width, fd_50F6_392C.height);
        } else {
            bpr = (fd_50F6_392C.width + 7) / 8;
            size = bpr * fd_50F6_392C.height * 4;
            h = f_171C_13CA((long)(size + 12), 1, "fontBuf");
            p = f_171C_1B84(h);
            src = fd_50F6_392C.bits;
            dst = p + 12;
            if (g_3DB2 == 320)
                f_24FA_00A0(src, size);
            for (i = 0; i < fd_50F6_392C.height; i++) {
                _fmemcpy(dst, src, bpr);
                dst += bpr;
                _fmemcpy(dst, src, bpr);
                dst += bpr;
                _fmemcpy(dst, src, bpr);
                dst += bpr;
                _fmemcpy(dst, src, bpr);
                dst += bpr;
                src += bpr;
            }
        }
    } else {
        size = (fd_50F6_392C.width + 7) / 8 * fd_50F6_392C.height;
        h = f_171C_13CA((long)(size + 12), 1, "fontBuf");
        p = f_171C_1B84(h);
        f_24FA_00A0(fd_50F6_392C.bits, size);
        _fmemcpy(p + 12, fd_50F6_392C.bits, size);
    }
    *(int far *)p = 0;
    p[2] = (g_5A97 & 1) ? 1 : 4;
    ((int far *)p)[4] = fd_50F6_392C.width;
    ((int far *)p)[5] = fd_50F6_392C.height;
    f_171C_1BBA(h);
    return h;
}

extern void (far * near g_9130)(void);
extern void (far * near g_912C)(void);
extern void far *fd_50F6_4A1A[];

void far f_24AB_02AD(int font)
{
    switch (font) {
    case 0:
        if (g_3DB2 == 320)
            (*g_912C)();
        else
            (*g_9130)();
        fd_55B3_65A4 = 0;
        break;
    case 1:
        if (g_3DB2 == 320)
            (*g_9130)();
        else
            (*g_912C)();
        fd_55B3_65A4 = 0;
        break;
    default:
        if (font > 5 || font < 0)
            font = 2;
        fd_55B3_65A4 = fd_50F6_4A1A[font - 2];
        break;
    }
}

extern char near g_3DDC;
extern int far _font_FontHeight(void far *font);

int far f_24AB_030B(void)
{
    if (fd_55B3_65A4 == 0)
        return g_3DDC;
    return _font_FontHeight(fd_55B3_65A4);
}

extern unsigned far _fstrlen(char far *s);
extern char near g_3DDE;
extern int far _font_StringWidth(char far *s, void far *font);

int far f_24AB_0329(char far *s)
{
    if (fd_55B3_65A4 == 0)
        return _fstrlen(s) * g_3DDE;
    return _font_StringWidth(s, fd_55B3_65A4);
}

extern int far _font_CharWidth(int c, void far *font);

int far f_24AB_0367(int c)
{
    if (fd_55B3_65A4 == 0)
        return g_3DDE;
    return _font_CharWidth(c, fd_55B3_65A4);
}

extern struct Pt far g_3DA0;
extern void far f_1FBD_0000(int x, int y, char far *text);
extern void (far * near g_9154)(int x, int y, char far *bits, int width, int height);

void far f_24AB_038D(int x, int y, char far *text)
{
    if (*text == 0) {
        g_3DA0.x = x;
        g_3DA0.y = y;
        return;
    }
    if (fd_55B3_65A4 == 0) {
        f_1FBD_0000(x, y, text);
        return;
    }
    font_MakeImage(text, 0, fd_55B3_65A4);
    (*g_9154)(x, y, fd_50F6_392C.bits, fd_50F6_392C.width, fd_50F6_392C.height);
    g_3DA0.x = fd_50F6_392C.width + x;
    g_3DA0.y = y;
}

void far f_24AB_040C(char far *text)
{
    f_24AB_038D(g_3DA0.x, g_3DA0.y, text);
}

extern int near g_3DE2;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);

void far f_24AB_042B(struct Rect far *r, int y, char far *text)
{
    int x;
    int right;

    f_24AB_038D(r->left, y, text);
    x = g_3DA0.x;
    if ((right = r->right) > x)
        (*g_9134)(x, y, right, f_24AB_030B() + y, g_3DE2);
}

extern char far g_5ABE[];
extern void far * far font_ReadFont(char far *name);

void far font_InitFonts(void)
{
    fd_50F6_392C.bits = g_5ABE;
    fd_50F6_4A1A[0] = font_ReadFont("font1");
    fd_50F6_4A1A[1] = font_ReadFont("font2");
    fd_50F6_4A1A[2] = font_ReadFont("font3");
    fd_50F6_4A1A[3] = font_ReadFont("font4");
}
