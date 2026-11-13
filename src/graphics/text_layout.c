/*
 * Measures and centres text blocks. It also includes delay and fatal text helpers in the same
 * module.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1F80; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs.
 */

#include "rect.h"

#include "pt.h"

struct Pt far gfx_measure_text_cells(char far *);
void far timer_wait_double_ticks(int);
char far * far gfx_left_pad_centered_text(char far *, int);
int far gfx_center_cell_x(int);
void far gfx_print_centered_cell_line(struct Rect far *, int, char far *);
int far gfx_center_fixed_text_x(struct Rect far *, char far *);
void far gfx_center_cell_rect(struct Rect far *, int, int);
void far gfx_place_cell_rect(struct Rect far *, int, int, int, int);
void far gfx_fatal_text_wait(char far *);

extern char far * far _fstrchr(char far *s, int c);
extern unsigned int far _fstrlen(char far *s);

static struct Pt size;

/*
 * Return maximum line length and line count in character cells.
 */
struct Pt far gfx_measure_text_cells(char far *text)
{
    int len;
    char far *nl;
    char far *p;

    p = text;
    size.y = size.x = 0;
    while (*p) {
        if ((nl = _fstrchr(p, '\n')) != 0) {
            len = nl - p;
            p++;
        } else
            len = _fstrlen(p);
        if (len > size.x)
            size.x = len;
        size.y++;
        p += len;
    }
    return size;
}

extern long far TickCount(void);

void far timer_wait_double_ticks(int ticks)
{
    long t;

    ticks <<= 1;
    while (ticks--) {
        t = TickCount();
        while (TickCount() == t)
            ;
    }
}

/* size: byte-equivalent hypothesis -- the segment ends before FAR_BSS 50F6, so 97..112 all give
   the same image (all zero, no callers of gfx_left_pad_centered_text fix a width) */
/*
 * Space-prefixed string returned by the text centering helper.
 */
static char far text_centering_buffer[100];
extern void far * far _fmemset(void far *dst, int c, unsigned int n);
extern char far * far _fstrcpy(char far *dst, char far *src);

/*
 * Return text with centering spaces in shared storage; the buffer capacity is unresolved.
 */
char far * far gfx_left_pad_centered_text(char far *text, int width)
{
    int pad;

    pad = (width - _fstrlen(text)) / 2;
    _fmemset(text_centering_buffer, ' ', pad);
    _fstrcpy(text_centering_buffer + pad, text);
    return text_centering_buffer;
}

extern char near fontWidth;
extern int near gfx_screen_width_pixels;

/*
 * Return the screen-centered column for a text-cell width.
 */
int far gfx_center_cell_x(int width)
{
    return (gfx_screen_width_pixels / fontWidth - width) / 2;
}

extern int far font_FontHeight(void);
extern void far GPutStr(int x, int y, char far *text);

/*
 * Print a line centered in cell bounds; line packs a row and signed pixel offset.
 */
void far gfx_print_centered_cell_line(struct Rect far *r, int line, char far *text)
{
    GPutStr(((r->right - _fstrlen(text) - r->left) / 2 + r->left) * fontWidth,
                font_FontHeight() * (line & 0xff) + (char)(line >> 8), text);
}

/*
 * Return the pixel x coordinate that centers fixed-width text in a rectangle.
 */
int far gfx_center_fixed_text_x(struct Rect far *r, char far *text)
{
    return (r->right - _fstrlen(text) * fontWidth - r->left) / 2 + r->left;
}

extern int near gfx_screen_height_pixels;

/*
 * Build a screen-centered rectangle in character-cell units.
 */
void far gfx_center_cell_rect(struct Rect far *r, int width, int height)
{
    r->left = (gfx_screen_width_pixels / fontWidth - width) / 2;
    r->right = r->left + width;
    r->top = (gfx_screen_height_pixels / font_FontHeight() - height) / 2;
    r->bottom = r->top + height;
}

/*
 * Place a text-cell rectangle with the routine's screen-margin adjustments.
 */
void far gfx_place_cell_rect(struct Rect far *r, int x, int y, int width, int height)
{
    if (x < 0)
        x = 0;
    else if (gfx_screen_width_pixels / fontWidth <= x + width)
        x = gfx_screen_width_pixels / fontWidth - width - 1;
    if (y < 1)
        y = 1;
    else if (gfx_screen_height_pixels / font_FontHeight() <= y + height)
        y = gfx_screen_height_pixels / font_FontHeight() - height - 1;
    r->left = x;
    r->right = x + width;
    r->top = y;
    r->bottom = y + height;
}

extern void far gfx_printf_cells(int x, int y, char far *format, ...);
extern int far kbd_read_bios_char(void);

/*
 * Print the fatal message on row 22 and wait for one BIOS character.
 */
void far gfx_fatal_text_wait(char far *msg)
{
    gfx_printf_cells(0, 0x16, "FATAL: %s", msg);
    kbd_read_bios_char();
}
