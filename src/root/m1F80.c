/* Root module 1F80: text block measuring, centring and delay helpers. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pt {
    int x;
    int y;
};

extern char far * far _fstrchr(char far *s, int c);
extern unsigned int far _fstrlen(char far *s);

static struct Pt size;

struct Pt far f_1F80_000C(char far *text)
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

void far f_1F80_0081(int ticks)
{
    long t;

    ticks <<= 1;
    while (ticks--) {
        t = TickCount();
        while (TickCount() == t)
            ;
    }
}

extern char far fd_50EF_0000[];
extern void far * far _fmemset(void far *dst, int c, unsigned int n);
extern char far * far _fstrcpy(char far *dst, char far *src);

char far * far f_1F80_00B8(char far *text, int width)
{
    int pad;

    pad = (width - _fstrlen(text)) / 2;
    _fmemset(fd_50EF_0000, ' ', pad);
    _fstrcpy(fd_50EF_0000 + pad, text);
    return fd_50EF_0000;
}

extern char near g_3DDE;
extern int near g_3DB2;

int far f_1F80_0109(int width)
{
    return (g_3DB2 / g_3DDE - width) / 2;
}

extern int far f_24AB_030B(void);
extern void far f_1FBD_0000(int x, int y, char far *text);

void far f_1F80_0122(struct Rect far *r, int line, char far *text)
{
    f_1FBD_0000(((r->right - _fstrlen(text) - r->left) / 2 + r->left) * g_3DDE,
                f_24AB_030B() * (line & 0xff) + (char)(line >> 8), text);
}

int far f_1F80_0177(struct Rect far *r, char far *text)
{
    return (r->right - _fstrlen(text) * g_3DDE - r->left) / 2 + r->left;
}

extern int near g_3DB4;

void far f_1F80_01A8(struct Rect far *r, int width, int height)
{
    r->left = (g_3DB2 / g_3DDE - width) / 2;
    r->right = r->left + width;
    r->top = (g_3DB4 / f_24AB_030B() - height) / 2;
    r->bottom = r->top + height;
}

void far f_1F80_01F3(struct Rect far *r, int x, int y, int width, int height)
{
    if (x < 0)
        x = 0;
    else if (g_3DB2 / g_3DDE <= x + width)
        x = g_3DB2 / g_3DDE - width - 1;
    if (y < 1)
        y = 1;
    else if (g_3DB4 / f_24AB_030B() <= y + height)
        y = g_3DB4 / f_24AB_030B() - height - 1;
    r->left = x;
    r->right = x + width;
    r->top = y;
    r->bottom = y + height;
}

extern void far f_1CE2_016C(int x, int y, char far *format, ...);
extern int far f_1F58_005A(void);

void far f_1F80_0280(char far *msg)
{
    f_1CE2_016C(0, 0x16, "FATAL: %s", msg);
    f_1F58_005A();
}
