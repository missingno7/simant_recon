/* Root module 1629: speech balloons (Win16 unit MakeBalloon, ConvertMonoMaskToTandy,
 * ConvertMonoMaskToColor). */

typedef char far * far *Handle;

struct Mask {
    int type;
    unsigned char flag;
    unsigned char pad[5];
    int width;
    int height;
};

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
extern void far * far fd_55B3_65A4;
extern void far Punt(char far *format, ...);
extern char far * far _fstrcpy(char far *dest, char far *src);
extern int far f_24AB_0329(char far *text, void far *font);
extern int far _font_FontHeight(void far *font);
extern Handle far f_171C_13CA(long size, int flags, char far *name);
extern char far * far f_171C_1B84(Handle h);
extern void far f_2650_0107(char far *buf, int size);
extern void far f_1699_0000(unsigned char far *pattern, int x, int y, char far *dest);
extern void far f_1699_0050(unsigned char far *pattern, int dx, int y, char far *dest, int count);
extern char far * far font_MakeImage(char far *s, int x, void far *font);
extern void far f_1699_00A6(char far *image, char far *dest, int x, int y);
extern Handle far f_171C_1BBA(Handle h);
extern void far f_171C_2276(char far *p);
extern unsigned char near g_5A97;
Handle far ConvertMonoMaskToTandy(Handle h);
Handle far ConvertMonoMaskToColor(Handle h);
extern void far f_1699_01AA(char far *dest, char far *src, int n);

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
    h = f_171C_13CA((long)(bytes + 12), 1, "balloon");
    p = f_171C_1B84(h);
    f_2650_0107(p + 8, bytes);
    *(int far *)(p + 8) = widest;
    *(int far *)(p + 10) = height;
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
        f_1699_00A6(font_MakeImage(lines[i], (unsigned)(-f_24AB_0329(lines[i], fd_55B3_65A4) & 6) >> 1,
                                   fd_55B3_65A4), p + 8, 1, _font_FontHeight(fd_55B3_65A4) * i + 6);
    bottom = _font_FontHeight(fd_55B3_65A4) * i + 6;
    f_1699_0000(g_1D6A, cols + 1, bottom, p + 8);
    f_1699_0000(g_1D5A, 0, bottom, p + 8);
    f_1699_0050(g_1D7A, 1, bottom, p + 8, cols);
    if (tail)
        f_1699_0000(g_1D9A, cols - 1, bottom, p + 8);
    else
        f_1699_0000(g_1DAA, 1, bottom, p + 8);
    (*(int far *)(p + 10))--;
    if (n < 1)
        (*(int far *)(p + 10))--;
    f_171C_1BBA(h);
    f_171C_2276(buf);
    rowBytes = *(int far *)(p + 8) / 8;
    if (g_5A97 == 2)
        return ConvertMonoMaskToTandy(h);
    if (!(g_5A97 & 1))
        return ConvertMonoMaskToColor(h);
    q = p + 12;
    for (i = 0; i < height; i++) {
        f_1699_01AA(q, q + rowBytes, rowBytes);
        q += rowBytes;
        q += rowBytes;
    }
    *(int far *)p = 3;
    p[2] = 1;
    return h;
}

extern void far f_1699_0110(char far *src, char far *dst);
extern void far f_171C_1C0A(Handle h);

Handle far ConvertMonoMaskToTandy(Handle h)
{
    struct Mask far *src;
    struct Mask far *dst;
    Handle nh;
    int width;
    int height;

    src = (struct Mask far *)f_171C_1B84(h);
    width = src->width;
    height = src->height;
    nh = f_171C_13CA((long)(src->height * src->width / 2 + 12), 1, "tdyballoon");
    dst = (struct Mask far *)f_171C_1B84(nh);
    dst->width = width;
    dst->height = height;
    dst->type = 3;
    dst->flag = 4;
    f_1699_0110((char far *)src + 8, (char far *)dst + 8);
    f_171C_1BBA(h);
    f_171C_1BBA(nh);
    f_171C_1C0A(h);
    return nh;
}

extern int far WinPrintf(char far *, ...);
extern void far * far _fmemcpy(void far *, void far *, unsigned);
extern int near g_3DB2;
extern void far f_24FA_00A0(char far *, int);

Handle far ConvertMonoMaskToColor(Handle h)
{
    struct Mask far *src;
    struct Mask far *dst;
    Handle nh;
    int width;
    int height;
    int row;
    int rb;
    char far *s;
    char far *d;

    src = (struct Mask far *)f_171C_1B84(h);
    width = src->width;
    height = src->height;
    nh = f_171C_13CA((long)(width / 8 * height * 5 + 12), 1, "clrbln");
    dst = (struct Mask far *)f_171C_1B84(nh);
    dst->width = width;
    dst->height = height;
    dst->flag = 4;
    dst->type = 3;
    s = (char far *)src + 12;
    d = (char far *)dst + 12;
    rb = width / 8;
    WinPrintf("\nBalloon Size=%d, %d", width, height);
    for (row = 0; row < height; row++) {
        _fmemcpy(d, s + rb, rb);
        d += rb;
        if (g_3DB2 != 0x140)
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
