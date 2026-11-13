/*
 * Constructs speech balloon images from text. It converts their monochrome masks into the colour
 * formats required by the display modes.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1629; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 */

typedef char far * far *Handle;

#include "picture.h"

unsigned char g_1D0A[16] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0f, 0x0f, 0x3f, 0x3f, 0x7f, 0x3f, 0x7f };
unsigned char g_1D1A[16] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xf0, 0xf0, 0xfc, 0xfc, 0xfe, 0xfc, 0xfe };
unsigned char g_1D2A[16] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff };
unsigned char g_1D3A[16] = { 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe };
unsigned char g_1D4A[16] = { 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f };
unsigned char g_1D5A[16] = { 0x3f, 0x7f, 0x3f, 0x7f, 0x0f, 0x3f, 0, 0x0f, 0, 0, 0, 0, 0, 0, 0, 0 };
unsigned char g_1D6A[16] = { 0xfc, 0xfe, 0xfc, 0xfe, 0xf0, 0xfc, 0, 0xf0, 0, 0, 0, 0, 0, 0, 0, 0 };
unsigned char g_1D7A[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0, 0xff, 0, 0, 0, 0, 0, 0, 0, 0 };
unsigned char g_1D8A[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff };
unsigned char g_1D9A[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x3e, 0xff, 0x0e, 0x1f, 0x06, 0x0f, 0x02, 0x07, 0, 0x02 };
unsigned char g_1DAA[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7c, 0xff, 0x70, 0xf8, 0x60, 0xf0, 0x40, 0xe0, 0, 0x40 };

extern char far * far f_171C_2208(unsigned size);
extern void far * far curFontPtr;
extern void far Punt(char far *format, ...);
extern char far * far _fstrcpy(char far *dest, char far *src);
extern int far font_StringWidth(char far *text, void far *font);
extern int far _font_FontHeight(void far *font);
extern Handle far Ralloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern void far ClearBuffer(char far *buf, int size);
extern void far CopyChar(unsigned char far *pattern, int x, int y, char far *dest);
extern void far CopyCharRep(unsigned char far *pattern, int dx, int y, char far *dest, int count);
extern char far * far font_MakeImage(char far *s, int x, void far *font);
extern void far MoveTextToBalloon(char far *image, char far *dest, int x, int y);
extern Handle far mem_Unlock(Handle h);
extern void far f_171C_2276(char far *p);
extern unsigned char near gfx_display_mode;
Handle far ConvertMonoMaskToTandy(Handle h);
Handle far ConvertMonoMaskToColor(Handle h);
extern void far exchange(char far *dest, char far *src, int n);

/* MakeBalloon.  lp is kept from the original's frame evidence: storing the first line through a
 * pointer to lines[] takes the array's address, so the loops reload lines[i] after every call
 * (address CSE temporaries, as in the original) and the 4-byte slot is accounted for.  The
 * variable names are byte-equivalent hypotheses. */
Handle far MakeBalloon(char far *text, int tail)
{
    char far *buf;
    char far *lines[10];
    int bottom;
    int n;
    int i;
    int widest;
    int height;
    int bytes;
    int cols;
    int rowBytes;
    Handle h;
    char far *p;
    char far *q;
    char far * *lp;

    buf = f_171C_2208(300);
    if (curFontPtr == 0)
        Punt("BAD font in MakeBaloon");
    _fstrcpy(buf, text);
    lp = lines;
    *lp = buf;
    for (n = i = 0; lines[0][i]; i++) {
        if (n >= 10)
            break;
        if (lines[0][i] == '\\' && lines[0][i + 1] == 'n') {
            lines[0][i] = 0;
            i++;
            lines[++n] = lines[0] + i + 1;
        }
    }
    widest = 0;
    for (i = 0; i <= n; i++)
        if (font_StringWidth(lines[i], curFontPtr) > widest)
            widest = font_StringWidth(lines[i], curFontPtr);
    height = _font_FontHeight(curFontPtr) * (n + 1) + 16;
    widest += 16;
    widest = (widest + 7) & ~7;
    bytes = (height + 1) * widest / 4;
    h = Ralloc((long)(bytes + 12), 1, "balloon");
    p = mem_Lock(h);
    ClearBuffer(p + 8, bytes);
    ((struct Pic far *)p)->width = widest;
    ((struct Pic far *)p)->height = height;
    bottom = height - 8;
    cols = (widest >> 3) - 2;
    CopyChar(g_1D0A, 0, 0, p + 8);
    CopyCharRep(g_1D2A, 1, 0, p + 8, cols);
    CopyChar(g_1D1A, cols + 1, 0, p + 8);
    for (i = 8; i < bottom; i += 8) {
        CopyCharRep(g_1D8A, 1, i, p + 8, cols);
        CopyChar(g_1D4A, 0, i, p + 8);
        CopyChar(g_1D3A, cols + 1, i, p + 8);
    }
    for (i = 0; i <= n; i++)
        MoveTextToBalloon(font_MakeImage(lines[i], (unsigned)(-font_StringWidth(lines[i], curFontPtr) & 6) >> 1,
                                   curFontPtr), p + 8, 1, _font_FontHeight(curFontPtr) * i + 6);
    bottom = _font_FontHeight(curFontPtr) * i + 6;
    CopyChar(g_1D6A, cols + 1, bottom, p + 8);
    CopyChar(g_1D5A, 0, bottom, p + 8);
    CopyCharRep(g_1D7A, 1, bottom, p + 8, cols);
    if (tail)
        CopyChar(g_1D9A, cols - 1, bottom, p + 8);
    else
        CopyChar(g_1DAA, 1, bottom, p + 8);
    (((struct Pic far *)p)->height)--;
    if (n < 1)
        (((struct Pic far *)p)->height)--;
    mem_Unlock(h);
    f_171C_2276(buf);
    rowBytes = ((struct Pic far *)p)->width / 8;
    if (gfx_display_mode == 2)
        return ConvertMonoMaskToTandy(h);
    if (!(gfx_display_mode & 1))
        return ConvertMonoMaskToColor(h);
    q = p + 12;
    for (i = 0; i < height; i++) {
        exchange(q, q + rowBytes, rowBytes);
        q += rowBytes;
        q += rowBytes;
    }
    *(int far *)p = 3;
    p[2] = 1;
    return h;
}

extern void far MaskMono2Tandy(char far *src, char far *dst);
extern void far mem_Free(Handle h);

Handle far ConvertMonoMaskToTandy(Handle h)
{
    struct Pic far *src;
    struct Pic far *dst;
    Handle nh;
    int width;
    int height;

    src = (struct Pic far *)mem_Lock(h);
    width = src->width;
    height = src->height;
    nh = Ralloc((long)(src->height * src->width / 2 + 12), 1, "tdyballoon");
    dst = (struct Pic far *)mem_Lock(nh);
    dst->width = width;
    dst->height = height;
    dst->type = 3;
    dst->mode = 4;
    MaskMono2Tandy((char far *)src + 8, (char far *)dst + 8);
    mem_Unlock(h);
    mem_Unlock(nh);
    mem_Free(h);
    return nh;
}

extern int far WinPrintf(char far *, ...);
extern void far * far _fmemcpy(void far *, void far *, unsigned);
extern int near gfx_screen_width_pixels;
extern void far invert(char far *, int);

Handle far ConvertMonoMaskToColor(Handle h)
{
    struct Pic far *src;
    struct Pic far *dst;
    Handle nh;
    int width;
    int height;
    int row;
    int rb;
    char far *s;
    char far *d;

    src = (struct Pic far *)mem_Lock(h);
    width = src->width;
    height = src->height;
    nh = Ralloc((long)(width / 8 * height * 5 + 12), 1, "clrbln");
    dst = (struct Pic far *)mem_Lock(nh);
    dst->width = width;
    dst->height = height;
    dst->mode = 4;
    dst->type = 3;
    s = (char far *)src + 12;
    d = (char far *)dst + 12;
    rb = width / 8;
    WinPrintf("\nBalloon Size=%d, %d", width, height);
    for (row = 0; row < height; row++) {
        _fmemcpy(d, s + rb, rb);
        d += rb;
        if (gfx_screen_width_pixels != 0x140)
            invert(s, rb);
        _fmemcpy(d, s, rb);
        d += rb;
        _fmemcpy(d, s, rb);
        d += rb;
        _fmemcpy(d, s, rb);
        d += rb;
        _fmemcpy(d, s, rb);
        d += rb;
        s += rb;
        s += rb;
    }
    mem_Unlock(h);
    mem_Unlock(nh);
    mem_Free(h);
    return nh;
}
