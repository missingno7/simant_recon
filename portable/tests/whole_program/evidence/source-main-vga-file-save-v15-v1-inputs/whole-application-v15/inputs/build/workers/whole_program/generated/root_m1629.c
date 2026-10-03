#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/conversions/pointer_globals.h"
#pragma pack(push, 2)
/* Root module 1629: speech balloons (Win16 unit MakeBalloon, ConvertMonoMaskToTandy,
 * ConvertMonoMaskToColor). */

typedef char  *  *Handle;

struct Mask {
    int16_t type;
    uint8_t flag;
    uint8_t pad[5];
    int16_t width;
    int16_t height;
};

uint8_t g_1D0A[16] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x0f, 0x0f, 0x3f, 0x3f, 0x7f, 0x3f, 0x7f };
uint8_t g_1D1A[16] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xf0, 0xf0, 0xfc, 0xfc, 0xfe, 0xfc, 0xfe };
uint8_t g_1D2A[16] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff };
uint8_t g_1D3A[16] = { 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe, 0xfc, 0xfe };
uint8_t g_1D4A[16] = { 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f, 0x3f, 0x7f };
uint8_t g_1D5A[16] = { 0x3f, 0x7f, 0x3f, 0x7f, 0x0f, 0x3f, 0, 0x0f, 0, 0, 0, 0, 0, 0, 0, 0 };
uint8_t g_1D6A[16] = { 0xfc, 0xfe, 0xfc, 0xfe, 0xf0, 0xfc, 0, 0xf0, 0, 0, 0, 0, 0, 0, 0, 0 };
uint8_t g_1D7A[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0, 0xff, 0, 0, 0, 0, 0, 0, 0, 0 };
uint8_t g_1D8A[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff };
uint8_t g_1D9A[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x3e, 0xff, 0x0e, 0x1f, 0x06, 0x0f, 0x02, 0x07, 0, 0x02 };
uint8_t g_1DAA[16] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7c, 0xff, 0x70, 0xf8, 0x60, 0xf0, 0x40, 0xe0, 0, 0x40 };

extern char  *  dos_malloc(uint16_t size);

extern void  Punt(char  *format, ...);

extern int16_t  f_24AB_0329(char  *text, void  *font);
extern int16_t  _font_FontHeight(void  *font);
extern Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(Handle h);
extern void  f_2650_0107(char  *buf, int16_t size);
extern void  f_1699_0000(uint8_t  *pattern, int16_t x, int16_t y, char  *dest);
extern void  f_1699_0050(uint8_t  *pattern, int16_t dx, int16_t y, char  *dest, int16_t count);
extern char  *  font_MakeImage(char  *s, int16_t x, void  *font);
extern void  f_1699_00A6(char  *image, char  *dest, int16_t x, int16_t y);
extern Handle  f_171C_1BBA(Handle h);
extern void  dos_free(char  *p);

Handle  ConvertMonoMaskToTandy(Handle h);
Handle  ConvertMonoMaskToColor(Handle h);
extern void  f_1699_01AA(char  *dest, char  *src, int16_t n);

/* MakeBalloon.  lp is kept from the original's frame evidence: storing the first line through a
 * pointer to lines[] takes the array's address, so the loops reload lines[i] after every call
 * (address CSE temporaries, as in the original) and the 4-byte slot is accounted for.  The
 * variable names are byte-equivalent hypotheses. */
Handle  MakeBalloon(char  *text, int16_t tail)
{
    char  *buf;
    char  *lines[10];
    int16_t bottom;
    int16_t n;
    int16_t i;
    int16_t widest;
    int16_t height;
    int16_t bytes;
    int16_t cols;
    int16_t rowBytes;
    Handle h;
    char  *p;
    char  *q;
    char  * *lp;

    buf = dos_malloc(300);
    if (fd_55B3_65A4 == 0)
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
        if (f_24AB_0329(lines[i], fd_55B3_65A4) > widest)
            widest = f_24AB_0329(lines[i], fd_55B3_65A4);
    height = _font_FontHeight(fd_55B3_65A4) * (n + 1) + 16;
    widest += 16;
    widest = (widest + 7) & ~7;
    bytes = (height + 1) * widest / 4;
    h = f_171C_13CA((int32_t)(bytes + 12), 1, "balloon");
    p = f_171C_1B84(h);
    f_2650_0107(p + 8, bytes);
    *(int16_t  *)(p + 8) = widest;
    *(int16_t  *)(p + 10) = height;
    bottom = height - 8;
    cols = (widest >> 3) - 2;
    f_1699_0000(g_1D0A, 0, 0, p + 8);
    f_1699_0050(g_1D2A, 1, 0, p + 8, cols);
    f_1699_0000(g_1D1A, cols + 1, 0, p + 8);
    for (i = 8; i < bottom; i += 8) {
        f_1699_0050(g_1D8A, 1, i, p + 8, cols);
        f_1699_0000(g_1D4A, 0, i, p + 8);
        f_1699_0000(g_1D3A, cols + 1, i, p + 8);
    }
    for (i = 0; i <= n; i++)
        f_1699_00A6(font_MakeImage(lines[i], (uint16_t)(-f_24AB_0329(lines[i], fd_55B3_65A4) & 6) >> 1,
                                   fd_55B3_65A4), p + 8, 1, _font_FontHeight(fd_55B3_65A4) * i + 6);
    bottom = _font_FontHeight(fd_55B3_65A4) * i + 6;
    f_1699_0000(g_1D6A, cols + 1, bottom, p + 8);
    f_1699_0000(g_1D5A, 0, bottom, p + 8);
    f_1699_0050(g_1D7A, 1, bottom, p + 8, cols);
    if (tail)
        f_1699_0000(g_1D9A, cols - 1, bottom, p + 8);
    else
        f_1699_0000(g_1DAA, 1, bottom, p + 8);
    (*(int16_t  *)(p + 10))--;
    if (n < 1)
        (*(int16_t  *)(p + 10))--;
    f_171C_1BBA(h);
    dos_free(buf);
    rowBytes = *(int16_t  *)(p + 8) / 8;
    if (((uint8_t)g_5A97) == 2)
        return ConvertMonoMaskToTandy(h);
    if (!(((uint8_t)g_5A97) & 1))
        return ConvertMonoMaskToColor(h);
    q = p + 12;
    for (i = 0; i < height; i++) {
        f_1699_01AA(q, q + rowBytes, rowBytes);
        q += rowBytes;
        q += rowBytes;
    }
    *(int16_t  *)p = 3;
    p[2] = 1;
    return h;
}

extern void  f_1699_0110(char  *src, char  *dst);
extern void  f_171C_1C0A(Handle h);

Handle  ConvertMonoMaskToTandy(Handle h)
{
    struct Mask  *src;
    struct Mask  *dst;
    Handle nh;
    int16_t width;
    int16_t height;

    src = (struct Mask  *)f_171C_1B84(h);
    width = src->width;
    height = src->height;
    nh = f_171C_13CA((int32_t)(src->height * src->width / 2 + 12), 1, "tdyballoon");
    dst = (struct Mask  *)f_171C_1B84(nh);
    dst->width = width;
    dst->height = height;
    dst->type = 3;
    dst->flag = 4;
    f_1699_0110((char  *)src + 8, (char  *)dst + 8);
    f_171C_1BBA(h);
    f_171C_1BBA(nh);
    f_171C_1C0A(h);
    return nh;
}

extern int16_t  WinPrintf(char  *, ...);

extern void  f_24FA_00A0(char  *, int16_t);

Handle  ConvertMonoMaskToColor(Handle h)
{
    struct Mask  *src;
    struct Mask  *dst;
    Handle nh;
    int16_t width;
    int16_t height;
    int16_t row;
    int16_t rb;
    char  *s;
    char  *d;

    src = (struct Mask  *)f_171C_1B84(h);
    width = src->width;
    height = src->height;
    nh = f_171C_13CA((int32_t)(width / 8 * height * 5 + 12), 1, "clrbln");
    dst = (struct Mask  *)f_171C_1B84(nh);
    dst->width = width;
    dst->height = height;
    dst->flag = 4;
    dst->type = 3;
    s = (char  *)src + 12;
    d = (char  *)dst + 12;
    rb = width / 8;
    WinPrintf("\nBalloon Size=%d, %d", width, height);
    for (row = 0; row < height; row++) {
        _fmemcpy(d, s + rb, rb);
        d += rb;
        if (SIM_GRAPHICS_SOURCE_g_3DB2 != 0x140)
            f_24FA_00A0(s, rb);
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
    f_171C_1BBA(h);
    f_171C_1BBA(nh);
    f_171C_1C0A(h);
    return nh;
}

#pragma pack(pop)
