/*
 * Selects the current font and prints strings with it. It initializes the display fonts and
 * manages their output buffer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 24AB; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

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

void far *curFontPtr = 0;

extern struct Bitmap far * far font_MakeImage(char far *s, int x, void far *font);
extern char near g_5A97;
extern Handle far Ralloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern struct Bitmap far out_buffer;
extern void far ConvertMonoToTandy(char far *dst, char far *src, int width, int height);
extern int near g_3DB2;
extern void far invert(char far *bits, int size);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);
extern Handle far mem_Unlock(Handle h);

Handle far font_make_display_bitmap(char far *text)
{
    Handle h;
    char far *p;
    int bpr;
    int size;
    int i;
    char far *src;
    char far *dst;

    font_MakeImage(text, 0, curFontPtr);
    if ((g_5A97 & 1) == 0) {
        if (g_5A97 == 2) {
            h = Ralloc((long)((out_buffer.width + 1) / 2 * out_buffer.height + 12), 1, "fontBuf");
            p = mem_Lock(h);
            ConvertMonoToTandy(p + 12, out_buffer.bits, out_buffer.width, out_buffer.height);
        } else {
            bpr = (out_buffer.width + 7) / 8;
            size = bpr * out_buffer.height * 4;
            h = Ralloc((long)(size + 12), 1, "fontBuf");
            p = mem_Lock(h);
            src = out_buffer.bits;
            dst = p + 12;
            if (g_3DB2 == 320)
                invert(src, size);
            for (i = 0; i < out_buffer.height; i++) {
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
        size = (out_buffer.width + 7) / 8 * out_buffer.height;
        h = Ralloc((long)(size + 12), 1, "fontBuf");
        p = mem_Lock(h);
        invert(out_buffer.bits, size);
        _fmemcpy(p + 12, out_buffer.bits, size);
    }
    *(int far *)p = 0;
    p[2] = (g_5A97 & 1) ? 1 : 4;
    ((int far *)p)[4] = out_buffer.width;
    ((int far *)p)[5] = out_buffer.height;
    mem_Unlock(h);
    return h;
}

extern void (far * near g_9130)(void);
extern void (far * near g_912C)(void);
extern void far *fd_50F6_4A1A[];

void far font_SetFont(int font)
{
    switch (font) {
    case 0:
        if (g_3DB2 == 320)
            (*g_912C)();
        else
            (*g_9130)();
        curFontPtr = 0;
        break;
    case 1:
        if (g_3DB2 == 320)
            (*g_9130)();
        else
            (*g_912C)();
        curFontPtr = 0;
        break;
    default:
        if (font > 5 || font < 0)
            font = 2;
        curFontPtr = fd_50F6_4A1A[font - 2];
        break;
    }
}

extern char near g_3DDC;
extern int far _font_FontHeight(void far *font);

int far font_FontHeight(void)
{
    if (curFontPtr == 0)
        return g_3DDC;
    return _font_FontHeight(curFontPtr);
}

extern unsigned far _fstrlen(char far *s);
extern char near fontWidth;
extern int far _font_StringWidth(char far *s, void far *font);

int far font_StringWidth(char far *s)
{
    if (curFontPtr == 0)
        return _fstrlen(s) * fontWidth;
    return _font_StringWidth(s, curFontPtr);
}

extern int far _font_CharWidth(int c, void far *font);

int far font_CharWidth(int c)
{
    if (curFontPtr == 0)
        return fontWidth;
    return _font_CharWidth(c, curFontPtr);
}

extern struct Pt far g_3DA0;
extern void far GPutStr(int x, int y, char far *text);
extern void (far * near g_9154)(int x, int y, char far *bits, int width, int height);

void far font_PrintStr(int x, int y, char far *text)
{
    if (*text == 0) {
        g_3DA0.x = x;
        g_3DA0.y = y;
        return;
    }
    if (curFontPtr == 0) {
        GPutStr(x, y, text);
        return;
    }
    font_MakeImage(text, 0, curFontPtr);
    (*g_9154)(x, y, out_buffer.bits, out_buffer.width, out_buffer.height);
    g_3DA0.x = out_buffer.width + x;
    g_3DA0.y = y;
}

void far font_print_at_pen(char far *text)
{
    font_PrintStr(g_3DA0.x, g_3DA0.y, text);
}

extern int near g_3DE2;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);

void far font_print_and_clear_row(struct Rect far *r, int y, char far *text)
{
    int x;
    int right;

    font_PrintStr(r->left, y, text);
    x = g_3DA0.x;
    if ((right = r->right) > x)
        (*g_9134)(x, y, right, font_FontHeight() + y, g_3DE2);
}

extern char far g_5ABE[];
extern void far * far font_ReadFont(char far *name);

void far font_InitFonts(void)
{
    out_buffer.bits = g_5ABE;
    fd_50F6_4A1A[0] = font_ReadFont("font1");
    fd_50F6_4A1A[1] = font_ReadFont("font2");
    fd_50F6_4A1A[2] = font_ReadFont("font3");
    fd_50F6_4A1A[3] = font_ReadFont("font4");
}
