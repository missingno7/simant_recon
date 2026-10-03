#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_slots.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Root module 1CE2: screen primitives (character-cell rectangles, frames, save/restore). */
char  *  f_1CE2_000C(void)
{
    return (char *)&g_5A9C;
}

void  f_1CE2_01F8(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width);

void  f_1CE2_0013(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width)
{
    g_9134(left, top, right, bottom, SIM_GRAPHICS_SOURCE_g_3DE2);
    f_1CE2_01F8(left, top, right, bottom, width);
}

extern void  f_1B4E_0110(int16_t x, int16_t y, int16_t c);

void  f_1CE2_0043(int16_t x, int16_t y, int16_t c, int16_t width)
{
    f_1B4E_0110(x, y, c);
    f_1CE2_01F8(x, y, SIM_GRAPHICS_SOURCE_g_3DDE + x, SIM_GRAPHICS_SOURCE_g_3DDC + y, width);
}

#define CELLY(v) (((v) & 0xff) * SIM_GRAPHICS_SOURCE_g_3DDC + (char)((v) >> 8) * SIM_GRAPHICS_SOURCE_g_3DDC / 14)

void  f_1CE2_0077(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t color)
{
    g_9134(left << 3, CELLY(top), right << 3, CELLY(bottom + 1), color);
}

void  f_1CE2_00D5(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width)
{
    f_1CE2_01F8(left << 3, SIM_GRAPHICS_SOURCE_g_3DDC * top, right << 3, SIM_GRAPHICS_SOURCE_g_3DDC * (bottom + 1), width);
}

extern void ( *  g_9174)(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t mode);

void  f_1CE2_0104(struct Rect  *r, int16_t mode)
{
    g_9174(r->left, r->top, r->right, r->bottom, mode);
}

extern void ( *  g_9138)(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t mode);

void  f_1CE2_0124(struct Rect  *r)
{
    g_9138(r->left, r->top, r->right, r->bottom, (char)((SIM_GRAPHICS_SOURCE_g_3DE0 >> 8) + 0x10) << 8 | 0x20);
}

void  f_1CE2_014B(int16_t left, int16_t top, int16_t right, int16_t bottom)
{
    g_9138(left, top, right, bottom, (char)((SIM_GRAPHICS_SOURCE_g_3DE0 >> 8) + 0x10) << 8 | 0x20);
}
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);

void  f_1CE2_016C(int16_t x, int16_t y, char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    char buf[200];

    dos_vsprintf(buf, format, _dos_va_args);
    f_24AB_038D((x & 0xff) << 3, CELLY(y), buf);

    va_end(_dos_va_args);
}

void  f_1CE2_01C3(int16_t x, int16_t y, char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    char buf[200];

    dos_vsprintf(buf, format, _dos_va_args);
    f_24AB_038D(x, y, buf);

    va_end(_dos_va_args);
}

void  f_1CE2_01F8(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width)
{
    if (width) {
        g_9134(left + width, top + width, right - width, top, SIM_GRAPHICS_SOURCE_g_3DE0);
        g_9134(left + width, bottom - width, right - width, bottom, SIM_GRAPHICS_SOURCE_g_3DE0);
        g_9134(left + width, top, left, bottom, SIM_GRAPHICS_SOURCE_g_3DE0);
        g_9134(right, top, right - width, bottom, SIM_GRAPHICS_SOURCE_g_3DE0);
    }
}

void  f_1CE2_0278(struct Rect  *r, int16_t width, char sides, int16_t color)
{
    if (width == 0)
        return;
    if (sides & 2)
        g_9134(r->left + width, r->top + width, r->right - width, r->top, color);
    if (sides & 8)
        g_9134(r->left + width, r->bottom - width, r->right - width, r->bottom, color);
    if (sides & 1)
        g_9134(r->left + width, r->top, r->left, r->bottom, color);
    if (sides & 4)
        g_9134(r->right, r->top, r->right - width, r->bottom, color);
}

extern void ( *  g_913C)(int16_t left, int16_t top, int16_t right, int16_t bottom);

void  f_1CE2_032B(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width)
{
    if (width) {
        g_913C(left + width, top + width, right - width, top);
        g_913C(left + width, bottom - width, right - width, bottom);
        g_913C(left + width, top, left, bottom);
        g_913C(right, top, right - width, bottom);
    }
}

static struct Rect g_8CCC;

struct Rect  *  f_1CE2_039B(struct Rect  *r)
{
    g_8CCC.left = (r->left & 0xff) * SIM_GRAPHICS_SOURCE_g_3DDE;
    g_8CCC.right = (r->right & 0xff) * SIM_GRAPHICS_SOURCE_g_3DDE;
    g_8CCC.top = CELLY(r->top);
    g_8CCC.bottom = CELLY(r->bottom);
    return &g_8CCC;
}

void  GRectInvOutline(struct Rect  *r, int16_t width)
{
    f_1CE2_032B(r->left, r->top, r->right, r->bottom, width);
}

void  f_1CE2_0430(struct Rect  *r)
{
    g_913C(r->left, r->top, r->right, r->bottom);
}

void  f_1CE2_044D(struct Rect  *r, int16_t width)
{
    f_1CE2_01F8(r->left, r->top, r->right, r->bottom, width);
}

void  f_1CE2_046D(struct Rect  *r, int16_t color)
{
    g_9134(r->left, r->top, r->right, r->bottom, color);
}

void  f_1CE2_048D(struct Rect  *r, int16_t width)
{
    g_9134(r->left, r->top, r->right, r->bottom, SIM_GRAPHICS_SOURCE_g_3DE2);
    f_1CE2_01F8(r->left, r->top, r->right, r->bottom, width);
}

extern char  g_21A4;
extern int16_t ( *  g_9140)(int16_t left, int16_t top, int16_t right, int16_t bottom);
extern char  *  f_171C_2190(int16_t size, char  *name);
extern void ( *  g_9148)(int16_t left, int16_t top, int16_t right, int16_t bottom, char  *buffer);

char  *  GSaveRect(struct Rect  *r)
{
    int16_t x;
    int32_t size;
    char  *p;

    g_21A4 = 1;
    x = r->left & ~7;
    size = g_9140(x, r->top, r->right, r->bottom);
    if (size > 0xffdc)
        return 0;
    p = f_171C_2190(size, "GSaveRect");
    if (p)
        g_9148(x, r->top, r->right, r->bottom, p);
    g_21A4 = 0;
    return p;
}

void  f_1CE2_0587(struct Rect  *r, char  *buf, int16_t release);

void  f_1CE2_0552(struct Rect  *r, char  *buf)
{
    f_1CE2_0587(r, buf, 0);
}

void  f_1CE2_056C(struct Rect  *r, char  *buf)
{
    f_1CE2_0587(r, buf, 1);
}

extern void  f_1B4E_003B(int16_t x, int16_t y, char  *image);
extern void  dos_free(char  *block);
extern void  f_21FA_0AD2(struct Rect  *rect);

void  f_1CE2_0587(struct Rect  *r, char  *buf, int16_t release)
{
    int16_t x;

    x = r->left & ~7;
    if (buf) {
        g_21A4 = 1;
        f_1B4E_003B(x, r->top, buf);
        g_21A4 = 0;
        if (release)
            dos_free(buf);
    } else
        f_21FA_0AD2(r);
}

void  f_1CE2_05DF(char  *buf)
{
    if (buf)
        dos_free(buf);
}

struct PackHdr {
    int16_t type;
    char depth;
    char pad3;
    int16_t x4;
    int16_t x6;
    int16_t width;
    int16_t height;
};

extern void  f_1B05_0008(char  *packed, int16_t length);
extern uint16_t  f_1B05_0046(char  *dest, uint16_t length);

extern void ( *  g_914C)();
extern int16_t ( *  g_9144)(int16_t, int16_t, int16_t, int16_t);
extern void  Punt(char  *format, ...);
extern char  *  *  f_171C_1A9E(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_171C_1BBA(char  *  *handle);
extern void  f_171C_1C0A(char  *  *handle);

void  GPutPacked(int16_t x, int16_t y, char  *pic)
{
    int16_t row;
    int16_t len;
    int16_t saveLen;
    int16_t ( *size)(int16_t left, int16_t top, int16_t right, int16_t bottom);
    int16_t rem;
    int16_t right;
    void ( *blit)();
    int16_t  *save;
    int16_t  *buf;
    char  *  *h;
    struct PackHdr hdr;

    f_1B05_0008(pic + 4, *(int16_t  *)(pic + 2));
    f_1B05_0046((char  *)&hdr, 12);
    rem = hdr.height & 7;
    hdr.height &= ~7;
    row = 0;
    if (hdr.depth != 4 && hdr.depth != 8) {
        blit = (g_5A97 & 1) ? g_914C : g_9154;
        size = g_9144;
    } else {
        if (g_5A97 & 1)
            Punt("Color picture in mono file");
        blit = g_914C;
        size = g_9140;
    }
    len = size(0, 0, hdr.width, 1) - 4;
    if (hdr.type == 3) {
        if (g_5A97 != 2)
            len = len / (uint8_t)hdr.depth * ((uint8_t)hdr.depth + 1);
        right = (hdr.width + x + 15) & ~7;
        saveLen = size(x, 0, right, 1) - 4;
        h = f_171C_1A9E(((int32_t)len << 3) + 4, 1, "PutPackedBuf");
        save = (int16_t  *)f_171C_2190((saveLen << 3) + 4, "GPutPacked");
        buf = (int16_t  *)f_171C_1B84(h);
        buf[0] = hdr.width;
        buf[1] = 8;
        save[0] = hdr.width;
        save[1] = 8;
    } else {
        h = f_171C_1A9E(((int32_t)len << 3) + 4, 1, "PutPackedBuf");
        buf = (int16_t  *)f_171C_1B84(h);
    }
    for (; row < hdr.height; y += 8, row += 8) {
        if (!f_1B05_0046((char  *)(buf + 2), len << 3))
            break;
        if (hdr.type == 0)
            blit(x, y, buf + 2, hdr.width, 8);
        else if (hdr.type == 3) {
            g_9148(x & ~7, y, right, y + 8, (char  *)save);
            fd_50F6_37EA(buf, save, x & 7, 0);
            blit(x & ~7, y, save + 2, save[0], save[1], 0);
        }
    }
    if (rem) {
        f_1B05_0046((char  *)(buf + 2), len * rem);
        if (hdr.type == 0)
            blit(x, y, buf + 2, hdr.width, rem);
        else if (hdr.type == 3) {
            buf[1] = rem;
            save[1] = rem;
            g_9148(x & ~7, y, right, rem + y, (char  *)save);
            fd_50F6_37EA(buf, save, x & 7, 0);
            blit(x & ~7, y, save + 2, save[0], save[1], 0);
            dos_free((char  *)save);
        }
    }
    f_171C_1BBA(h);
    f_171C_1C0A(h);
}


void  f_1CE2_0951(struct Rect  *r, int16_t fore, int16_t back)
{
    if (g_5A97 & 1) {
        if ((fore ^ back) & 0xf0) {
            g_9128(fore, back, 0x20);
            f_1CE2_0124(r);
        } else
            f_1CE2_046D(r, fore);
    } else if (back != fore) {
        g_9128(fore, back, 0x20);
        f_1CE2_0124(r);
    } else
        f_1CE2_046D(r, fore);
}

void  f_1CE2_099C(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t fore, int16_t back)
{
    if (fore != back) {
        g_9128(fore, back, 0x20);
        f_1CE2_014B(left, top, right, bottom);
        return;
    }
    g_9134(left, top, right, bottom, fore);
}

void  f_1CE2_09E2(struct Rect  *r, int16_t width, char sides, int16_t fore, int16_t back)
{
    if (width == 0)
        return;
    if (back == fore || (g_5A97 & 1)) {
        f_1CE2_0278(r, width, sides, fore);
        return;
    }
    g_9128(fore, back, 0x20);
    if (sides & 2)
        f_1CE2_014B(r->left + width, r->top + width, r->right - width, r->top);
    if (sides & 8)
        f_1CE2_014B(r->left + width, r->bottom - width, r->right - width, r->bottom);
    if (sides & 1)
        f_1CE2_014B(r->left + width, r->top, r->left, r->bottom);
    if (sides & 4)
        f_1CE2_014B(r->right, r->top, r->right - width, r->bottom);
}

#pragma pack(pop)
