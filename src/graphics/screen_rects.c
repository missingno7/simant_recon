/*
 * Draws screen rectangles, outlines and frames using character cell coordinates. It saves and
 * restores rectangles and draws packed pictures.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1CE2; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

#include "rect.h"

extern char far gfx_screen_clip_list[];

/*
 * Return the shared screen rectangle.
 */
char far * far gfx_screen_rect(void)
{
    return gfx_screen_clip_list;
}

extern int near g_3DE2;
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);
void far GBoxOutline(int left, int top, int right, int bottom, int width);

void far GBoxFillOutline(int left, int top, int right, int bottom, int width)
{
    gfx_fill_rect_hook(left, top, right, bottom, g_3DE2);
    GBoxOutline(left, top, right, bottom, width);
}

extern void far gfx_put_fixed_font_char(int x, int y, int c);
extern char near gfx_font_height_pixels;
extern char near fontWidth;

/*
 * Draw one fixed-font character with an outline of the requested width.
 */
void far gfx_draw_outlined_char(int x, int y, int c, int width)
{
    gfx_put_fixed_font_char(x, y, c);
    GBoxOutline(x, y, fontWidth + x, gfx_font_height_pixels + y, width);
}

#define CELLY(v) (((v) & 0xff) * gfx_font_height_pixels + (char)((v) >> 8) * gfx_font_height_pixels / 14)

void far GTextBox(int left, int top, int right, int bottom, int color)
{
    gfx_fill_rect_hook(left << 3, CELLY(top), right << 3, CELLY(bottom + 1), color);
}

/*
 * Outline a box specified in eight-pixel columns and character rows; bottom row is
 * inclusive.
 */
void far gfx_outline_cell_box(int left, int top, int right, int bottom, int width)
{
    GBoxOutline(left << 3, gfx_font_height_pixels * top, right << 3, gfx_font_height_pixels * (bottom + 1), width);
}

extern void (far * near g_9174)(int left, int top, int right, int bottom, int mode);

/*
 * Draw the driver-specific color/pattern overlay over a rectangle.
 */
void far gfx_draw_rect_overlay(struct Rect far *r, int mode)
{
    g_9174(r->left, r->top, r->right, r->bottom, mode);
}

extern int near _foreColor;
extern void (far * near g_9138)(int left, int top, int right, int bottom, int mode);

void far GRectChecker(struct Rect far *r)
{
    g_9138(r->left, r->top, r->right, r->bottom, (char)((_foreColor >> 8) + 0x10) << 8 | 0x20);
}

void far GCheckerBox(int left, int top, int right, int bottom)
{
    g_9138(left, top, right, bottom, (char)((_foreColor >> 8) + 0x10) << 8 | 0x20);
}

extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern void far font_PrintStr(int x, int y, char far *text);

/*
 * Print formatted text at packed character-cell coordinates.
 */
void far gfx_printf_cells(int x, int y, char far *format, ...)
{
    char buf[200];

    vsprintf(buf, format, (char far *)(&format + 1));
    font_PrintStr((x & 0xff) << 3, CELLY(y), buf);
}

void far gfx_printf_at(int x, int y, char far *format, ...)
{
    char buf[200];

    vsprintf(buf, format, (char far *)(&format + 1));
    font_PrintStr(x, y, buf);
}

void far GBoxOutline(int left, int top, int right, int bottom, int width)
{
    if (width) {
        gfx_fill_rect_hook(left + width, top + width, right - width, top, _foreColor);
        gfx_fill_rect_hook(left + width, bottom - width, right - width, bottom, _foreColor);
        gfx_fill_rect_hook(left + width, top, left, bottom, _foreColor);
        gfx_fill_rect_hook(right, top, right - width, bottom, _foreColor);
    }
}

void far GRectPartialOutline(struct Rect far *r, int width, char sides, int color)
{
    if (width == 0)
        return;
    if (sides & 2)
        gfx_fill_rect_hook(r->left + width, r->top + width, r->right - width, r->top, color);
    if (sides & 8)
        gfx_fill_rect_hook(r->left + width, r->bottom - width, r->right - width, r->bottom, color);
    if (sides & 1)
        gfx_fill_rect_hook(r->left + width, r->top, r->left, r->bottom, color);
    if (sides & 4)
        gfx_fill_rect_hook(r->right, r->top, r->right - width, r->bottom, color);
}

extern void (far * near g_913C)(int left, int top, int right, int bottom);

void far GInvOutline(int left, int top, int right, int bottom, int width)
{
    if (width) {
        g_913C(left + width, top + width, right - width, top);
        g_913C(left + width, bottom - width, right - width, bottom);
        g_913C(left + width, top, left, bottom);
        g_913C(right, top, right - width, bottom);
    }
}

static struct Rect g_8CCC;

/*
 * Convert packed character-cell bounds to pixels in a shared result rectangle.
 */
struct Rect far * far gfx_cell_rect_to_pixels(struct Rect far *r)
{
    g_8CCC.left = (r->left & 0xff) * fontWidth;
    g_8CCC.right = (r->right & 0xff) * fontWidth;
    g_8CCC.top = CELLY(r->top);
    g_8CCC.bottom = CELLY(r->bottom);
    return &g_8CCC;
}

void far GRectInvOutline(struct Rect far *r, int width)
{
    GInvOutline(r->left, r->top, r->right, r->bottom, width);
}

void far GRectInv(struct Rect far *r)
{
    g_913C(r->left, r->top, r->right, r->bottom);
}

void far GRectOutline(struct Rect far *r, int width)
{
    GBoxOutline(r->left, r->top, r->right, r->bottom, width);
}

void far GRectFill(struct Rect far *r, int color)
{
    gfx_fill_rect_hook(r->left, r->top, r->right, r->bottom, color);
}

void far GRectFillOutline(struct Rect far *r, int width)
{
    gfx_fill_rect_hook(r->left, r->top, r->right, r->bottom, g_3DE2);
    GBoxOutline(r->left, r->top, r->right, r->bottom, width);
}

extern char near g_21A4;
extern int (far * near g_9140)(int left, int top, int right, int bottom);
extern char far * far mem_malloc(int size, char far *name);
extern void (far * near gfx_capture_rect_hook)(int left, int top, int right, int bottom, char far *buffer);

char far * far GSaveRect(struct Rect far *r)
{
    int x;
    long size;
    char far *p;

    g_21A4 = 1;
    x = r->left & ~7;
    size = g_9140(x, r->top, r->right, r->bottom);
    if (size > 0xffdc)
        return 0;
    p = mem_malloc(size, "GSaveRect");
    if (p)
        gfx_capture_rect_hook(x, r->top, r->right, r->bottom, p);
    g_21A4 = 0;
    return p;
}

void far gfx_restore_rect_with_release(struct Rect far *r, char far *buf, int release);

/*
 * Restore saved pixels without freeing the buffer; repaint if no buffer exists.
 */
void far gfx_restore_rect(struct Rect far *r, char far *buf)
{
    gfx_restore_rect_with_release(r, buf, 0);
}

void far gfx_restore_and_free_rect(struct Rect far *r, char far *buf)
{
    gfx_restore_rect_with_release(r, buf, 1);
}

extern void far GPutPic(int x, int y, char far *image);
extern void far free(char far *block);
extern void _fastcall win_redraw_rect(struct Rect far *rect);

/*
 * Restore saved pixels and optionally free them, or repaint the rectangle if no save
 * exists.
 */
void far gfx_restore_rect_with_release(struct Rect far *r, char far *buf, int release)
{
    int x;

    x = r->left & ~7;
    if (buf) {
        g_21A4 = 1;
        GPutPic(x, r->top, buf);
        g_21A4 = 0;
        if (release)
            free(buf);
    } else
        win_redraw_rect(r);
}

/*
 * Free a nonnull saved-rectangle buffer.
 */
void far gfx_free_saved_rect(char far *buf)
{
    if (buf)
        free(buf);
}

struct PackHdr {
    int type;
    char depth;
    char pad3;
    int x4;
    int x6;
    int width;
    int height;
};

extern void far UnpackInit(char far *packed, int length);
extern unsigned int far Unpack(char far *dest, unsigned int length);
extern char near gfx_display_mode;
extern void (far * near gfx_put_picture_hook)();
extern void (far * near gfx_put_image_hook)();
extern int (far * near g_9144)(int, int, int, int);
extern void far Punt(char far *format, ...);
extern char far * far * far mem_Alloc(long size, int flags, char far *name);
extern char far * far mem_Lock(char far * far *handle);
extern void (far * far gfx_mask_to_buffer_hook)();
extern void far mem_Unlock(char far * far *handle);
extern void far mem_Free(char far * far *handle);

void far GPutPacked(int x, int y, char far *pic)
{
    int row;
    int len;
    int saveLen;
    int (far *size)(int left, int top, int right, int bottom);
    int rem;
    int right;
    void (far *blit)();
    int far *save;
    int far *buf;
    char far * far *h;
    struct PackHdr hdr;

    UnpackInit(pic + 4, *(int far *)(pic + 2));
    Unpack((char far *)&hdr, 12);
    rem = hdr.height & 7;
    hdr.height &= ~7;
    row = 0;
    if (hdr.depth != 4 && hdr.depth != 8) {
        blit = (gfx_display_mode & 1) ? gfx_put_picture_hook : gfx_put_image_hook;
        size = g_9144;
    } else {
        if (gfx_display_mode & 1)
            Punt("Color picture in mono file");
        blit = gfx_put_picture_hook;
        size = g_9140;
    }
    len = size(0, 0, hdr.width, 1) - 4;
    if (hdr.type == 3) {
        if (gfx_display_mode != 2)
            len = len / (unsigned char)hdr.depth * ((unsigned char)hdr.depth + 1);
        right = (hdr.width + x + 15) & ~7;
        saveLen = size(x, 0, right, 1) - 4;
        h = mem_Alloc(((long)len << 3) + 4, 1, "PutPackedBuf");
        save = (int far *)mem_malloc((saveLen << 3) + 4, "GPutPacked");
        buf = (int far *)mem_Lock(h);
        buf[0] = hdr.width;
        buf[1] = 8;
        save[0] = hdr.width;
        save[1] = 8;
    } else {
        h = mem_Alloc(((long)len << 3) + 4, 1, "PutPackedBuf");
        buf = (int far *)mem_Lock(h);
    }
    for (; row < hdr.height; y += 8, row += 8) {
        if (!Unpack((char far *)(buf + 2), len << 3))
            break;
        if (hdr.type == 0)
            blit(x, y, buf + 2, hdr.width, 8);
        else if (hdr.type == 3) {
            gfx_capture_rect_hook(x & ~7, y, right, y + 8, (char far *)save);
            gfx_mask_to_buffer_hook(buf, save, x & 7, 0);
            blit(x & ~7, y, save + 2, save[0], save[1], 0);
        }
    }
    if (rem) {
        Unpack((char far *)(buf + 2), len * rem);
        if (hdr.type == 0)
            blit(x, y, buf + 2, hdr.width, rem);
        else if (hdr.type == 3) {
            buf[1] = rem;
            save[1] = rem;
            gfx_capture_rect_hook(x & ~7, y, right, rem + y, (char far *)save);
            gfx_mask_to_buffer_hook(buf, save, x & 7, 0);
            blit(x & ~7, y, save + 2, save[0], save[1], 0);
            free((char far *)save);
        }
    }
    mem_Unlock(h);
    mem_Free(h);
}

extern void (far * near gfx_set_attributes_hook)(int fore, int back, int pattern);

void far GMixedFill(struct Rect far *r, int fore, int back)
{
    if (gfx_display_mode & 1) {
        if ((fore ^ back) & 0xf0) {
            gfx_set_attributes_hook(fore, back, 0x20);
            GRectChecker(r);
        } else
            GRectFill(r, fore);
    } else if (back != fore) {
        gfx_set_attributes_hook(fore, back, 0x20);
        GRectChecker(r);
    } else
        GRectFill(r, fore);
}

void far GMixedFillBox(int left, int top, int right, int bottom, int fore, int back)
{
    if (fore != back) {
        gfx_set_attributes_hook(fore, back, 0x20);
        GCheckerBox(left, top, right, bottom);
        return;
    }
    gfx_fill_rect_hook(left, top, right, bottom, fore);
}

void far GRectPartialMixedOutline(struct Rect far *r, int width, char sides, int fore, int back)
{
    if (width == 0)
        return;
    if (back == fore || (gfx_display_mode & 1)) {
        GRectPartialOutline(r, width, sides, fore);
        return;
    }
    gfx_set_attributes_hook(fore, back, 0x20);
    if (sides & 2)
        GCheckerBox(r->left + width, r->top + width, r->right - width, r->top);
    if (sides & 8)
        GCheckerBox(r->left + width, r->bottom - width, r->right - width, r->bottom);
    if (sides & 1)
        GCheckerBox(r->left + width, r->top, r->left, r->bottom);
    if (sides & 4)
        GCheckerBox(r->right, r->top, r->right - width, r->bottom);
}
