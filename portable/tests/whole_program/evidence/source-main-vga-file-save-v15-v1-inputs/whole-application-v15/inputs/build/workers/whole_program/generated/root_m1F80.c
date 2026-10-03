#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module 1F80: text block measuring, centring and delay helpers. */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t x;
    int16_t y;
};

struct Pt  f_1F80_000C(char  *);
void  f_1F80_0081(int16_t);
char  *  f_1F80_00B8(char  *, int16_t);
int16_t  f_1F80_0109(int16_t);
void  f_1F80_0122(struct Rect  *, int16_t, char  *);
int16_t  f_1F80_0177(struct Rect  *, char  *);
void  f_1F80_01A8(struct Rect  *, int16_t, int16_t);
void  f_1F80_01F3(struct Rect  *, int16_t, int16_t, int16_t, int16_t);
void  f_1F80_0280(char  *);



static struct Pt size;

struct Pt  f_1F80_000C(char  *text)
{
    int16_t len;
    char  *nl;
    char  *p;

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

extern int32_t  TickCount(void);

void  f_1F80_0081(int16_t ticks)
{
    int32_t t;

    ticks <<= 1;
    while (ticks--) {
        t = TickCount();
        while (TickCount() == t)
            ;
    }
}

/* size: byte-equivalent hypothesis -- the segment ends before FAR_BSS 50F6, so 97..112 all give
   the same image (all zero, no callers of f_1F80_00B8 fix a width) */
static char  fd_50EF_0000[100];



char  *  f_1F80_00B8(char  *text, int16_t width)
{
    int16_t pad;

    pad = (width - _fstrlen(text)) / 2;
    _fmemset(fd_50EF_0000, ' ', pad);
    _fstrcpy(fd_50EF_0000 + pad, text);
    return fd_50EF_0000;
}


int16_t  f_1F80_0109(int16_t width)
{
    return (SIM_GRAPHICS_SOURCE_g_3DB2 / SIM_GRAPHICS_SOURCE_g_3DDE - width) / 2;
}

extern int16_t  f_24AB_030B(void);
extern void  f_1FBD_0000(int16_t x, int16_t y, char  *text);

void  f_1F80_0122(struct Rect  *r, int16_t line, char  *text)
{
    f_1FBD_0000(((r->right - _fstrlen(text) - r->left) / 2 + r->left) * SIM_GRAPHICS_SOURCE_g_3DDE,
                f_24AB_030B() * (line & 0xff) + (char)(line >> 8), text);
}

int16_t  f_1F80_0177(struct Rect  *r, char  *text)
{
    return (r->right - _fstrlen(text) * SIM_GRAPHICS_SOURCE_g_3DDE - r->left) / 2 + r->left;
}


void  f_1F80_01A8(struct Rect  *r, int16_t width, int16_t height)
{
    r->left = (SIM_GRAPHICS_SOURCE_g_3DB2 / SIM_GRAPHICS_SOURCE_g_3DDE - width) / 2;
    r->right = r->left + width;
    r->top = (SIM_GRAPHICS_SOURCE_g_3DB4 / f_24AB_030B() - height) / 2;
    r->bottom = r->top + height;
}

void  f_1F80_01F3(struct Rect  *r, int16_t x, int16_t y, int16_t width, int16_t height)
{
    if (x < 0)
        x = 0;
    else if (SIM_GRAPHICS_SOURCE_g_3DB2 / SIM_GRAPHICS_SOURCE_g_3DDE <= x + width)
        x = SIM_GRAPHICS_SOURCE_g_3DB2 / SIM_GRAPHICS_SOURCE_g_3DDE - width - 1;
    if (y < 1)
        y = 1;
    else if (SIM_GRAPHICS_SOURCE_g_3DB4 / f_24AB_030B() <= y + height)
        y = SIM_GRAPHICS_SOURCE_g_3DB4 / f_24AB_030B() - height - 1;
    r->left = x;
    r->right = x + width;
    r->top = y;
    r->bottom = y + height;
}

extern void  f_1CE2_016C(int16_t x, int16_t y, char  *format, ...);
extern int16_t  f_1F58_005A(void);

void  f_1F80_0280(char  *msg)
{
    f_1CE2_016C(0, 0x16, "FATAL: %s", msg);
    f_1F58_005A();
}

#pragma pack(pop)
