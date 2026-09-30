/* Root module 1CE2: screen primitives (character-cell rectangles, frames, save/restore). */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern char far g_5A9C[];

char far * far f_1CE2_000C(void)
{
    return g_5A9C;
}

extern int near g_3DE2;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);
void far f_1CE2_01F8(int left, int top, int right, int bottom, int width);

void far f_1CE2_0013(int left, int top, int right, int bottom, int width)
{
    g_9134(left, top, right, bottom, g_3DE2);
    f_1CE2_01F8(left, top, right, bottom, width);
}

extern void far f_1B4E_0110(int x, int y, int c);
extern char near g_3DDC;
extern char near g_3DDE;

void far f_1CE2_0043(int x, int y, int c, int width)
{
    f_1B4E_0110(x, y, c);
    f_1CE2_01F8(x, y, g_3DDE + x, g_3DDC + y, width);
}

#define CELLY(v) (((v) & 0xff) * g_3DDC + (char)((v) >> 8) * g_3DDC / 14)

void far f_1CE2_0077(int left, int top, int right, int bottom, int color)
{
    g_9134(left << 3, CELLY(top), right << 3, CELLY(bottom + 1), color);
}

void far f_1CE2_00D5(int left, int top, int right, int bottom, int width)
{
    f_1CE2_01F8(left << 3, g_3DDC * top, right << 3, g_3DDC * (bottom + 1), width);
}

extern void (far * near g_9174)(int left, int top, int right, int bottom, int mode);

void far f_1CE2_0104(struct Rect far *r, int mode)
{
    g_9174(r->left, r->top, r->right, r->bottom, mode);
}

extern int near g_3DE0;
extern void (far * near g_9138)(int left, int top, int right, int bottom, int mode);

void far f_1CE2_0124(struct Rect far *r)
{
    g_9138(r->left, r->top, r->right, r->bottom, (char)((g_3DE0 >> 8) + 0x10) << 8 | 0x20);
}

void far f_1CE2_014B(int left, int top, int right, int bottom)
{
    g_9138(left, top, right, bottom, (char)((g_3DE0 >> 8) + 0x10) << 8 | 0x20);
}

extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern void far f_24AB_038D(int x, int y, char far *text);

void far f_1CE2_016C(int x, int y, char far *format, ...)
{
    char buf[200];

    vsprintf(buf, format, (char far *)(&format + 1));
    f_24AB_038D((x & 0xff) << 3, CELLY(y), buf);
}

void far f_1CE2_01C3(int x, int y, char far *format, ...)
{
    char buf[200];

    vsprintf(buf, format, (char far *)(&format + 1));
    f_24AB_038D(x, y, buf);
}

void far f_1CE2_01F8(int left, int top, int right, int bottom, int width)
{
    if (width) {
        g_9134(left + width, top + width, right - width, top, g_3DE0);
        g_9134(left + width, bottom - width, right - width, bottom, g_3DE0);
        g_9134(left + width, top, left, bottom, g_3DE0);
        g_9134(right, top, right - width, bottom, g_3DE0);
    }
}

void far f_1CE2_0278(struct Rect far *r, int width, char sides, int color)
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

extern void (far * near g_913C)(int left, int top, int right, int bottom);

void far f_1CE2_032B(int left, int top, int right, int bottom, int width)
{
    if (width) {
        g_913C(left + width, top + width, right - width, top);
        g_913C(left + width, bottom - width, right - width, bottom);
        g_913C(left + width, top, left, bottom);
        g_913C(right, top, right - width, bottom);
    }
}

static struct Rect g_8CCC;

struct Rect far * far f_1CE2_039B(struct Rect far *r)
{
    g_8CCC.left = (r->left & 0xff) * g_3DDE;
    g_8CCC.right = (r->right & 0xff) * g_3DDE;
    g_8CCC.top = CELLY(r->top);
    g_8CCC.bottom = CELLY(r->bottom);
    return &g_8CCC;
}

void far f_1CE2_0410(struct Rect far *r, int width)
{
    f_1CE2_032B(r->left, r->top, r->right, r->bottom, width);
}

void far f_1CE2_0430(struct Rect far *r)
{
    g_913C(r->left, r->top, r->right, r->bottom);
}

void far f_1CE2_044D(struct Rect far *r, int width)
{
    f_1CE2_01F8(r->left, r->top, r->right, r->bottom, width);
}

void far f_1CE2_046D(struct Rect far *r, int color)
{
    g_9134(r->left, r->top, r->right, r->bottom, color);
}

void far f_1CE2_048D(struct Rect far *r, int width)
{
    g_9134(r->left, r->top, r->right, r->bottom, g_3DE2);
    f_1CE2_01F8(r->left, r->top, r->right, r->bottom, width);
}

extern char near g_21A4;
extern int (far * near g_9140)(int left, int top, int right, int bottom);
extern char far * far f_171C_2190(int size, char far *name);
extern void (far * near g_9148)(int left, int top, int right, int bottom, char far *buffer);

char far * far f_1CE2_04C9(struct Rect far *r)
{
    int x;
    long size;
    char far *p;

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

void far f_1CE2_0587(struct Rect far *r, char far *buf, int release);

void far f_1CE2_0552(struct Rect far *r, char far *buf)
{
    f_1CE2_0587(r, buf, 0);
}

void far f_1CE2_056C(struct Rect far *r, char far *buf)
{
    f_1CE2_0587(r, buf, 1);
}

extern void far f_1B4E_003B(int x, int y, char far *image);
extern void far f_171C_2276(char far *block);
extern void _fastcall f_21FA_0AD2(struct Rect far *rect);

void far f_1CE2_0587(struct Rect far *r, char far *buf, int release)
{
    int x;

    x = r->left & ~7;
    if (buf) {
        g_21A4 = 1;
        f_1B4E_003B(x, r->top, buf);
        g_21A4 = 0;
        if (release)
            f_171C_2276(buf);
    } else
        f_21FA_0AD2(r);
}

void far f_1CE2_05DF(char far *buf)
{
    if (buf)
        f_171C_2276(buf);
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

extern void far f_1B05_0008(char far *packed, int length);
extern unsigned int far f_1B05_0046(char far *dest, unsigned int length);
extern char near g_5A97;
extern void (far * near g_914C)();
extern void (far * near g_9154)();
extern int (far * near g_9144)(int, int, int, int);
extern void far Punt(char far *format, ...);
extern char far * far * far f_171C_1A9E(long size, int flags, char far *name);
extern char far * far f_171C_1B84(char far * far *handle);
extern void (far * far fd_50F6_37EA)();
extern void far f_171C_1BBA(char far * far *handle);
extern void far f_171C_1C0A(char far * far *handle);

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

    f_1B05_0008(pic + 4, *(int far *)(pic + 2));
    f_1B05_0046((char far *)&hdr, 12);
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
            len = len / (unsigned char)hdr.depth * ((unsigned char)hdr.depth + 1);
        right = (hdr.width + x + 15) & ~7;
        saveLen = size(x, 0, right, 1) - 4;
        h = f_171C_1A9E(((long)len << 3) + 4, 1, "PutPackedBuf");
        save = (int far *)f_171C_2190((saveLen << 3) + 4, "GPutPacked");
        buf = (int far *)f_171C_1B84(h);
        buf[0] = hdr.width;
        buf[1] = 8;
        save[0] = hdr.width;
        save[1] = 8;
    } else {
        h = f_171C_1A9E(((long)len << 3) + 4, 1, "PutPackedBuf");
        buf = (int far *)f_171C_1B84(h);
    }
    for (; row < hdr.height; y += 8, row += 8) {
        if (!f_1B05_0046((char far *)(buf + 2), len << 3))
            break;
        if (hdr.type == 0)
            blit(x, y, buf + 2, hdr.width, 8);
        else if (hdr.type == 3) {
            g_9148(x & ~7, y, right, y + 8, (char far *)save);
            fd_50F6_37EA(buf, save, x & 7, 0);
            blit(x & ~7, y, save + 2, save[0], save[1], 0);
        }
    }
    if (rem) {
        f_1B05_0046((char far *)(buf + 2), len * rem);
        if (hdr.type == 0)
            blit(x, y, buf + 2, hdr.width, rem);
        else if (hdr.type == 3) {
            buf[1] = rem;
            save[1] = rem;
            g_9148(x & ~7, y, right, rem + y, (char far *)save);
            fd_50F6_37EA(buf, save, x & 7, 0);
            blit(x & ~7, y, save + 2, save[0], save[1], 0);
            f_171C_2276((char far *)save);
        }
    }
    f_171C_1BBA(h);
    f_171C_1C0A(h);
}

extern void (far * near g_9128)(int fore, int back, int pattern);

void far f_1CE2_0951(struct Rect far *r, int fore, int back)
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

void far f_1CE2_099C(int left, int top, int right, int bottom, int fore, int back)
{
    if (fore != back) {
        g_9128(fore, back, 0x20);
        f_1CE2_014B(left, top, right, bottom);
        return;
    }
    g_9134(left, top, right, bottom, fore);
}

void far f_1CE2_09E2(struct Rect far *r, int width, char sides, int fore, int back)
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
