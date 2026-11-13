/*
 * Selects the current font and prints strings with it. It initializes the display fonts and
 * manages their output buffer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 24AB; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

typedef char far * far *Handle;

#include "rect.h"

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
extern char near gfx_display_mode;
extern Handle far Ralloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern struct Bitmap far out_buffer;
extern void far ConvertMonoToTandy(char far *dst, char far *src, int width, int height);
extern int near gfx_screen_width_pixels;
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
    if ((gfx_display_mode & 1) == 0) {
        if (gfx_display_mode == 2) {
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
            if (gfx_screen_width_pixels == 320)
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
    p[2] = (gfx_display_mode & 1) ? 1 : 4;
    ((int far *)p)[4] = out_buffer.width;
    ((int far *)p)[5] = out_buffer.height;
    mem_Unlock(h);
    return h;
}

extern void (far * near g_9130)(void);
extern void (far * near g_912C)(void);
extern void far *font_loaded_font_pointers[];

void far font_SetFont(int font)
{
    switch (font) {
    case 0:
        if (gfx_screen_width_pixels == 320)
            (*g_912C)();
        else
            (*g_9130)();
        curFontPtr = 0;
        break;
    case 1:
        if (gfx_screen_width_pixels == 320)
            (*g_9130)();
        else
            (*g_912C)();
        curFontPtr = 0;
        break;
    default:
        if (font > 5 || font < 0)
            font = 2;
        curFontPtr = font_loaded_font_pointers[font - 2];
        break;
    }
}

extern char near gfx_font_height_pixels;
extern int far _font_FontHeight(void far *font);

int far font_FontHeight(void)
{
    if (curFontPtr == 0)
        return gfx_font_height_pixels;
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

extern struct Pt far gfx_text_pen_x;
extern void far GPutStr(int x, int y, char far *text);
extern void (far * near gfx_put_image_hook)(int x, int y, char far *bits, int width, int height);

void far font_PrintStr(int x, int y, char far *text)
{
    if (*text == 0) {
        gfx_text_pen_x.x = x;
        gfx_text_pen_x.y = y;
        return;
    }
    if (curFontPtr == 0) {
        GPutStr(x, y, text);
        return;
    }
    font_MakeImage(text, 0, curFontPtr);
    (*gfx_put_image_hook)(x, y, out_buffer.bits, out_buffer.width, out_buffer.height);
    gfx_text_pen_x.x = out_buffer.width + x;
    gfx_text_pen_x.y = y;
}

/*
 * Print at the current text pen position.
 */
void far font_print_at_pen(char far *text)
{
    font_PrintStr(gfx_text_pen_x.x, gfx_text_pen_x.y, text);
}

extern int near g_3DE2;
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);

void far font_print_and_clear_row(struct Rect far *r, int y, char far *text)
{
    int x;
    int right;

    font_PrintStr(r->left, y, text);
    x = gfx_text_pen_x.x;
    if ((right = r->right) > x)
        (*gfx_fill_rect_hook)(x, y, right, font_FontHeight() + y, g_3DE2);
}

extern char far text_bitmap_pixels[];
extern void far * far font_ReadFont(char far *name);

void far font_InitFonts(void)
{
    out_buffer.bits = text_bitmap_pixels;
    font_loaded_font_pointers[0] = font_ReadFont("font1");
    font_loaded_font_pointers[1] = font_ReadFont("font2");
    font_loaded_font_pointers[2] = font_ReadFont("font3");
    font_loaded_font_pointers[3] = font_ReadFont("font4");
}
