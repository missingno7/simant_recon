/* Overlay section S17, code frame 384C: menu bar start-up (menu data fix-up, item
 * rectangles, menu colours). */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern void far f_1B28_006A(int a);
extern void far f_1B73_0046(void);
extern void far f_1B73_0235(void);
extern void far f_1B73_0AA3(void);
extern void far f_1B73_0218(int a, int b);
extern struct Rect far g_5A9C;
extern void far f_1FD2_03EB(struct Rect far *r, int ticks);

void far o17_384C_0000(void)
{
    f_1B28_006A(0);
    f_1B73_0046();
    f_1B73_0235();
    f_1B73_0AA3();
    f_1B73_0218(0x10, 0x10);
    f_1FD2_03EB(&g_5A9C, 0xff00);
}

extern long far * far * far db_LoadObject(int object, int kind);
extern long far * far fd_55B3_6054;
extern void far db_UnhookObject(int object, int kind);
extern void far f_1FD2_0663(int a);
extern int far fd_50F6_46BC[];
extern int far fd_50F6_46A8[];
void far o17_384C_0184(int x, int len, int id);

int far o17_384C_0039(int id)
{
    long far * far *h;
    long far *p;
    long far *q;
    long far *r;
    int i;

    h = db_LoadObject(id, 6);
    if (h == 0L)
        return 0;
    fd_55B3_6054 = *h;
    db_UnhookObject(id, 6);
    i = 0;
    for (p = fd_55B3_6054; ((unsigned)i >= 0) && *p; p++) {
        *p += (long)fd_55B3_6054;
        for (q = *(long far * far *)p; *q; q++)
            *q += (long)fd_55B3_6054;
    }
    f_1FD2_0663(0);
    for (i = 0, r = (long far *)*fd_55B3_6054; *r; i++, r++)
        o17_384C_0184(fd_50F6_46A8[i], fd_50F6_46BC[i], i - 0x200);
    return 1;
}

extern int far g_5FEA;
extern int far g_5FEC;
extern int far g_5FEE;

void far o17_384C_0143(int a, int b, int c)
{
    g_5FEA = a;
    g_5FEC = b;
    g_5FEE = c;
}

extern int far g_5FE6;
extern int far g_5FE8;

void far o17_384C_0169(int a, int b)
{
    g_5FE6 = a;
    g_5FE8 = b;
}

extern char near g_3DDC;
extern char near g_3DDE;

void far o17_384C_0184(int x, int len, int id)
{
    struct Rect r;

    r.top = 1;
    r.bottom = g_3DDC + 1;
    r.left = x;
    r.right = g_3DDE * len + x;
    f_1FD2_03EB(&r, id);
}
