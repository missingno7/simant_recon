/* Root module 2505: DOS window-object engine (partial). */

extern void far Punt(char far *format, ...);
extern int far WinPrintf(char far *format, ...);
extern unsigned int far _fstrlen(char far *s);
extern int _fastcall f_23AE_0051(int win);
extern void _fastcall f_23AE_0377(int win);
extern void _fastcall f_23AE_01DB(int win);

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

extern struct Pt _fastcall f_22BF_000A(char far *text);
extern void far f_208F_0419(struct Pt far *size, int id);

extern int g_6300;
extern int g_5702;
extern char far * far * near g_9230[];

char far * far f_2505_0006(int win)
{
    if (g_6300 == 0 && !f_23AE_0051(win))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO GETWINPTR!!", win);
    return *g_9230[win >> 8];
}

void _fastcall f_2505_0048(int win)
{
    char far *w;
    int n;
    int i;
    char far *p;

    w = f_2505_0006(win);
    n = *(int far *)(w + 0xc);
    p = w + n * 4 + 0x2c;
    for (i = 0; i < n; i++) {
        ((char far * far *)(w + 0x2c))[i] = p;
        p += *(int far *)(p + 0x22);
    }
}

int _fastcall f_2505_00DD(char far *obj)
{
    int size;

    size = 0x28;
    switch (obj[0x21]) {
    case 0:
    case 2:
    case 15:
    case 19:
    case 20:
    case 21:
    case 22:
        size = 0x29;
        break;
    case 4:
        size = 0x38;
        break;
    case 5:
    case 9:
    case 12:
        size = _fstrlen(obj + 0x2a) + 0x2d;
        break;
    case 6:
    case 7:
    case 8:
        size = 0x2a;
        break;
    case 13:
        size = 0x2c;
        break;
    case 16:
    case 17:
    case 18:
        size = _fstrlen(obj + 0x2e) + 0x31;
        break;
    }
    return size;
}

struct Pt _fastcall f_2505_0171(char far *obj)
{
    static struct Pt size;

    switch (obj[0x21]) {
    default:
        size.x = *(int far *)(obj + 4) - *(int far *)obj;
        size.y = *(int far *)(obj + 6) - *(int far *)(obj + 2);
        break;
    case 5:
    case 12:
        size = f_22BF_000A(obj + 0x28);
        size.x += 8;
        size.y += 8;
        break;
    case 6:
    case 13:
        f_208F_0419(&size, *(int far *)(obj + 0x28));
        break;
    case 9:
        size = f_22BF_000A(obj + 0x28);
        break;
    case 16:
    case 18:
        size = f_22BF_000A(obj + 0x2c);
        break;
    case 17:
        size = f_22BF_000A(obj + 0x2c);
        size.x += 8;
        size.y += 8;
        break;
    }
    return size;
}

char far * _fastcall f_2505_025F(int win)
{
    if (!f_23AE_0051(win))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO win_WinRectAddr!!", win);
    return f_2505_0006(win);
}

void _fastcall f_2505_0288(int obj, struct Rect far *rect)
{
    char far *w;

    f_23AE_0377(obj);
    w = f_2505_0006(obj);
    *rect = *((struct Rect far * far *)(w + 0x2c))[obj & 0xff];
    f_23AE_01DB(obj);
}

char far * _fastcall f_2505_02D7(int obj)
{
    if (!f_23AE_0051(obj))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO win_ObjAddr!!", obj);
    if (*(int far *)(f_2505_0006(obj) + 0xc) <= (unsigned char)obj)
        Punt("Attempt to get obj address outsize window");
    return ((char far * far *)(f_2505_0006(obj) + 0x2c))[obj & 0xff];
}

char far * _fastcall f_2505_0345(int win)
{
    if (!f_23AE_0051(win))
        WinPrintf("\nWINDOW %x NOT LOCKED DURING CALL TO win_WinAddr!!", win);
    return f_2505_0006(win);
}

int far f_2505_036E(void)
{
    if (g_5702 != (int)0x8000)
        return 1;
    return 0;
}

void _fastcall f_2505_0382(struct Pt far *center, struct Rect far *rect)
{
    center->x = (rect->right + rect->left) / 2;
    center->y = (rect->top + rect->bottom) / 2;
}
