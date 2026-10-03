/* Root module 1FAA: fill a quadrilateral scanline by scanline (16.16 fixed-point edges).
 * The local copy `p = q` is what makes /Og load the far pointer with a split
 * `mov di,[bp+6]; mov es,[bp+8]` (and spill it to a temp) instead of `les di,[bp+6]`;
 * `top` doubles as the scanline counter (no separate y: frame 0x22). */

struct Pt {
    int x;
    int y;
};

extern char near g_5A97;
extern void (far * near g_9128)(int a, int b, int c);
extern void (far * near g_913C)(int left, int top, int right, int bottom);
extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern void (far * near g_9138)(int x0, int y0, int x1, int y1, int color);

void far f_1FAA_0006(struct Pt far *q, int fore, int back)
{
    int top;
    int x0;
    int x1;
    int bottom;
    long dy;
    long sl;
    long sr;
    long fl;
    long fr;
    struct Pt far *p;

    p = q;
    top = p[0].y;
    bottom = p[2].y;
    x0 = p[0].x;
    x1 = p[1].x;
    dy = bottom - top;
    sl = ((long)(x0 - p[3].x) << 16) / dy;
    sr = ((long)(x1 - p[2].x) << 16) / dy;
    fl = (long)x0 << 16;
    fr = (long)x1 << 16;
    if (g_5A97 & 1)
        fore = back;
    (*g_9128)(fore, back, fore);
    for (; top < bottom; top++) {
        if (fore == -1)
            (*g_913C)(x0, top, x1, top + 1);
        else if (back == fore)
            (*g_9134)(x0, top, x1, top + 1, fore);
        else
            (*g_9138)(x0, top, x1, top + 1, 0x20);
        fl -= sl;
        x0 = fl >> 16;
        fr -= sr;
        x1 = fr >> 16;
    }
}
