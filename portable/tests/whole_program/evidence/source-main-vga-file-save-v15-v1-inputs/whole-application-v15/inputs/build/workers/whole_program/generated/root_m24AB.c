#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#include "portable/whole_program/types/fonts.h"
#pragma pack(push, 2)
/* Root module 24AB: current-font text output (Win16 unit font_SetFont,
 * font_InitFonts, font_PrintStr; GR segment). */

typedef char  *  *Handle;

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

struct Font *fd_55B3_65A4 = 0;

extern struct Bitmap  *  font_MakeImage(char  *s, int16_t x, void  *font);

extern Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(Handle h);
extern struct Bitmap  fd_50F6_392C;
extern void  f_24FA_0029(char  *dst, char  *src, int16_t width, int16_t height);
extern void  f_24FA_00A0(char  *bits, int16_t size);

extern Handle  f_171C_1BBA(Handle h);

Handle  f_24AB_0002(char  *text)
{
    Handle h;
    char  *p;
    int16_t bpr;
    int16_t size;
    int16_t i;
    char  *src;
    char  *dst;

    font_MakeImage(text, 0, fd_55B3_65A4);
    if ((g_5A97 & 1) == 0) {
        if (g_5A97 == 2) {
            h = f_171C_13CA((int32_t)((fd_50F6_392C.width + 1) / 2 * fd_50F6_392C.height + 12), 1, "fontBuf");
            p = f_171C_1B84(h);
            f_24FA_0029(p + 12, fd_50F6_392C.bits, fd_50F6_392C.width, fd_50F6_392C.height);
        } else {
            bpr = (fd_50F6_392C.width + 7) / 8;
            size = bpr * fd_50F6_392C.height * 4;
            h = f_171C_13CA((int32_t)(size + 12), 1, "fontBuf");
            p = f_171C_1B84(h);
            src = fd_50F6_392C.bits;
            dst = p + 12;
            if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
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
        h = f_171C_13CA((int32_t)(size + 12), 1, "fontBuf");
        p = f_171C_1B84(h);
        f_24FA_00A0(fd_50F6_392C.bits, size);
        _fmemcpy(p + 12, fd_50F6_392C.bits, size);
    }
    *(int16_t  *)p = 0;
    p[2] = (g_5A97 & 1) ? 1 : 4;
    ((int16_t  *)p)[4] = fd_50F6_392C.width;
    ((int16_t  *)p)[5] = fd_50F6_392C.height;
    f_171C_1BBA(h);
    return h;
}

extern void ( *  g_9130)(void);
extern void ( *  g_912C)(void);


void  f_24AB_02AD(int16_t font)
{
    switch (font) {
    case 0:
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
            (*g_912C)();
        else
            (*g_9130)();
        fd_55B3_65A4 = 0;
        break;
    case 1:
        if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320)
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

extern int16_t  _font_FontHeight(void  *font);

int16_t  f_24AB_030B(void)
{
    if (fd_55B3_65A4 == 0)
        return SIM_GRAPHICS_SOURCE_g_3DDC;
    return _font_FontHeight(fd_55B3_65A4);
}

extern int16_t  _font_StringWidth(char  *s, void  *font);

int16_t  f_24AB_0329(char  *s)
{
    if (fd_55B3_65A4 == 0)
        return _fstrlen(s) * SIM_GRAPHICS_SOURCE_g_3DDE;
    return _font_StringWidth(s, fd_55B3_65A4);
}

extern int16_t  _font_CharWidth(int16_t c, void  *font);

int16_t  f_24AB_0367(int16_t c)
{
    if (fd_55B3_65A4 == 0)
        return SIM_GRAPHICS_SOURCE_g_3DDE;
    return _font_CharWidth(c, fd_55B3_65A4);
}

extern void  f_1FBD_0000(int16_t x, int16_t y, char  *text);

void  f_24AB_038D(int16_t x, int16_t y, char  *text)
{
    if (*text == 0) {
        SIM_GRAPHICS_SOURCE_g_3DA0 = x;
        SIM_GRAPHICS_SOURCE_g_3DA2 = y;
        return;
    }
    if (fd_55B3_65A4 == 0) {
        f_1FBD_0000(x, y, text);
        return;
    }
    font_MakeImage(text, 0, fd_55B3_65A4);
    (*g_9154)(x, y, fd_50F6_392C.bits, fd_50F6_392C.width, fd_50F6_392C.height);
    SIM_GRAPHICS_SOURCE_g_3DA0 = fd_50F6_392C.width + x;
    SIM_GRAPHICS_SOURCE_g_3DA2 = y;
}

void  f_24AB_040C(char  *text)
{
    f_24AB_038D(SIM_GRAPHICS_SOURCE_g_3DA0, SIM_GRAPHICS_SOURCE_g_3DA2, text);
}


void  f_24AB_042B(struct Rect  *r, int16_t y, char  *text)
{
    int16_t x;
    int16_t right;

    f_24AB_038D(r->left, y, text);
    x = SIM_GRAPHICS_SOURCE_g_3DA0;
    if ((right = r->right) > x)
        (*g_9134)(x, y, right, f_24AB_030B() + y, SIM_GRAPHICS_SOURCE_g_3DE2);
}

extern char  g_5ABE[];
extern void  *  font_ReadFont(char  *name);

void  font_InitFonts(void)
{
    fd_50F6_392C.bits = g_5ABE;
    fd_50F6_4A1A[0] = font_ReadFont("font1");
    fd_50F6_4A1A[1] = font_ReadFont("font2");
    fd_50F6_4A1A[2] = font_ReadFont("font3");
    fd_50F6_4A1A[3] = font_ReadFont("font4");
}

#pragma pack(pop)
