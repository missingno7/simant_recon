/* Root module 208F: window-object text and bitmap helpers, resource loading, delays.
   Built without /Zi: the cross-function relocation order forbids per-function record
   breaks (e.g. none between 0x0074 and 0x0245); /Zd is equally consistent. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

typedef struct {
    int x;
    int y;
} Point;

int g_62BE = 0xa000;
int g_62C0 = 5;

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far GRectInv(struct Rect far *rect);

void far f_208F_0008(int obj)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    GRectInv(&r);
}

extern char near fontWidth;
extern Point far g_3DA0;

void far f_208F_002B(int obj, int col)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    g_3DA0.x = fontWidth * col + r.left;
    g_3DA0.y = r.top;
}

extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far font_PrintStr(int x, int y, char far *text);

void far f_208F_005B(int obj, char far *text, int dx, int dy)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    win_SetColorFromObjNum(obj);
    font_PrintStr(r.left + dx, r.top + dy, text);
}

extern int far font_StringWidth(char far *text);
extern int far font_FontHeight(void);

void far gr_CenterStrInRect(struct Rect far *rect, char far *text)
{
    struct Rect r;
    int w;
    int x;

    r = *rect;
    w = font_StringWidth(text);
    x = (r.right - w + r.left) / 2;
    if (x < r.left)
        x = r.left;
    r.left = x;
    r.right = x + w;
    r.top += (r.bottom - font_FontHeight() - r.top) / 2;
    r.bottom = font_FontHeight() + r.top;
    font_PrintStr(r.left, r.top, text);
}

extern int near g_3DE2;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);

void far gr_CenterStrInRectClear(struct Rect far *rect, char far *text)
{
    struct Rect r;
    int w;
    int x;

    r = *rect;
    w = font_StringWidth(text);
    x = (r.right - w + r.left) / 2;
    if (x < r.left)
        x = r.left;
    r.left = x;
    r.right = x + w;
    r.top += (r.bottom - font_FontHeight() - r.top) / 2;
    r.bottom = font_FontHeight() + r.top;
    font_PrintStr(r.left, r.top, text);
    if (rect->left < r.left)
        g_9134(rect->left, r.top, r.left, r.bottom, g_3DE2);
    if (rect->right > r.right)
        g_9134(r.right, r.top, rect->right, r.bottom, g_3DE2);
}

void far f_208F_01ED(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    gr_CenterStrInRect(&r, text);
}

void far f_208F_021B(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    font_PrintStr(r.left, r.top, text);
}

extern void (far * near g_9128)(int a, int b, int c);
extern void far GRectOutline(struct Rect far *rect, int width);

void far f_208F_024B(int obj, int color, int width)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    g_9128(color, color, color);
    GRectOutline(&r, width);
}

extern unsigned char near g_5A97;
extern void (far * near g_917C)(int x, int y, int offset);
extern char far * far * far fd_50F6_46D2;
extern void (far * near g_914C)(int x, int y, char far *p, int w, int h);

void far f_208F_027F(int obj, int n)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    if (!(g_5A97 & 1)) {
        if (g_5A97 & 2)
            g_914C(r.left, r.top, *fd_50F6_46D2 + (n << 5), 8, 8);
        else
            g_917C(r.left, r.top, (n << g_62C0) + g_62BE);
    } else
        g_914C(r.left, r.top, *fd_50F6_46D2 + (n << 5), 16, 16);
}

/* Two separate mode tests with identical calls: the 8x8 call of mode 6 is laid out inline
   and cross-jumped into the 16x16 tail; `==6 || ==2` places the shared block last. */
void far f_208F_02F0(int x, int y, int n)
{
    if (!(g_5A97 & 1)) {
        if (g_5A97 == 6)
            g_914C(x, y, *fd_50F6_46D2 + (n << 5), 8, 8);
        else if (g_5A97 == 2)
            g_914C(x, y, *fd_50F6_46D2 + (n << 5), 8, 8);
        else
            g_917C(x, y, (n << g_62C0) + g_62BE);
    } else
        g_914C(x, y, *fd_50F6_46D2 + (n << 5), 16, 16);
}

extern char far * far db_LoadObject(int object, int kind);
extern void far Punt(char far *format, ...);

char far * far f_208F_0357(int kind, int object)
{
    char far *p;

    p = db_LoadObject(object, kind);
    if (p == 0)
        Punt("\aCouldn't load resource %x,%x", object, kind);
    return p;
}

extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern void far f_24AB_040C(char far *text);

void far f_208F_038E(char far *format, ...)
{
    char buf[100];

    vsprintf(buf, format, (char far *)(&format + 1));
    f_24AB_040C(buf);
}

void far f_208F_03BC(int obj, char far *format, ...)
{
    struct Rect r;
    char buf[100];

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    vsprintf(buf, format, (char far *)(&format + 1));
    font_PrintStr(r.left, r.top, buf);
}

void far f_208F_0403(void)
{
}

void far f_208F_0404(void)
{
}

extern void far db_PurgeHandle(char far *handle);

void far f_208F_0405(char far *handle)
{
    db_PurgeHandle(handle);
}

extern char far * far mem_Lock(char far *h);
extern void far UnpackInit(char far *packed, int length);
extern unsigned int far Unpack(char far *dest, unsigned int length);
extern void far mem_Unlock(char far *h);
extern void far db_ReleaseObject(unsigned int object, int kind);

int far gr_BitMapSize(Point far *size, int object)
{
    char far *h;
    int far *p;
    int hdr[6];

    h = db_LoadObject(object, 2);
    if (h == 0) {
        size->x = size->y = 1;
        return 0;
    }
    p = (int far *)mem_Lock(h);
    if (p[0] == -1) {
        UnpackInit((char far *)(p + 2), p[1]);
        Unpack((char far *)hdr, 12);
        size->x = hdr[4];
        size->y = hdr[5];
    } else {
        size->x = p[4];
        size->y = p[5];
    }
    mem_Unlock(h);
    db_ReleaseObject(object, 2);
    return 1;
}

static long g_8CE8;
extern int far fd_50F6_46D0;
extern unsigned long far TickCount(void);

void far f_208F_04D0(int delay)
{
    g_8CE8 = TickCount();
    fd_50F6_46D0 = delay;
}

extern int far f_1F58_0038(void);
extern int far f_1F58_0090(void);
extern int far WaitedEnough(long far *timer, int delay);

int far f_208F_04EE(void)
{
    int key;

    if ((key = f_1F58_0038()) != 0) {
        key = f_1F58_0090();
        if (key != 13 && key != 27)
            key = 0;
    }
    return WaitedEnough(&g_8CE8, fd_50F6_46D0) || key;
}

extern int far fd_1B73_0006;

void far f_208F_0530(int ticks)
{
    fd_1B73_0006 = ticks;
    while (fd_1B73_0006 != 0)
        ;
}

void far f_208F_054B(int ticks)
{
    fd_1B73_0006 = ticks;
}

int far f_208F_055B(void)
{
    return !fd_1B73_0006;
}

int far f_208F_056A(void)
{
    while (f_1F58_0038())
        if (f_1F58_0090() == 0x1b)
            return 1;
    return 0;
}

int far f_208F_058B(void)
{
    return 3;
}
