/* Root module 23AE: window lock/unlock layer. */

extern void far Punt(char far *format, ...);

static int g_644C = 0;
static int g_644E = 0;
static unsigned char g_8DA6[45];
static char far *g_8CF2[45];

void far f_23AE_0004(void)
{
    int i;

    for (i = 0; i < 45; i++)
        if (g_8DA6[i])
            Punt("Window %d locked when it should not be!");
}

void far f_23AE_0022(void)
{
    _fmemset(g_8CF2, 0, sizeof g_8CF2);
    _fmemset(g_8DA6, 0, sizeof g_8DA6);
    g_644C = 1;
}

int _fastcall f_23AE_0051(int win)
{
    if (g_644C == 0)
        return 1;
    return g_8DA6[win >> 8];
}

extern char far * far * near g_9230[];
extern void far f_20E8_0001(int win);
extern int far f_171C_1AD4(char far * far *handle);
void far f_23AE_035D(void);
extern char far * far f_171C_1D40(char far * far *handle);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1C0A(char far * far *handle);
extern void far f_171C_1E86(char far * far *handle, int flag);
extern void _fastcall f_2505_0048(int win);
extern void _fastcall f_2505_0545(int win);

void _fastcall f_23AE_0069(int win, int high)
{
    int loaded = 0;
    int n;
    char far * far *h;
    char far *w;

    g_644E++;
    if (g_644C == 0)
        return;
    n = (char)(win >> 8);
    if (n > 40 || n < 0)
        Punt("Illegal win num %x at lock", n);
    if (g_9230[n] == 0) {
        f_20E8_0001(win);
        loaded = 1;
    }
    h = g_9230[n];
    if (g_8DA6[n] == 0) {
        g_8DA6[n]++;
        if (f_171C_1AD4(h)) {
            high = 0;
            f_23AE_035D();
        }
        if (high)
            w = f_171C_1D40(h);
        else
            w = f_171C_1B84(h);
        if (w == 0) {
            f_171C_1C0A(h);
            f_20E8_0001(win);
            h = g_9230[n];
            if (high)
                w = f_171C_1D40(h);
            else
                w = f_171C_1B84(h);
        }
        if (*(int far *)(w + 0x1c) & 0x800)
            f_171C_1E86(h, 1);
        if (g_8CF2[n] != w) {
            g_8CF2[n] = w;
            f_2505_0048(win);
        }
        if (loaded)
            f_2505_0545(win);
    } else if (g_8DA6[n]++ > 10) {
        Punt("win_Lock > 10 levels deep!!");
    }
    g_644E--;
}

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

/* SCAFFOLD BEGIN: f_23AE_01DB best draft (original position: after f_23AE_0069).
   Residue: the object pointer w->objs[i] is kept in es:bx and p computed as dx:ax
   (mov ax,bx; mov dx,es; add ax,34h); the original copies it to DI and uses
   lea bx,[di+34h]/[di+2Ah]; frame 20h vs 1Ch. */
struct Obj {
    char pad[0x21];
    char type;
    char pad22[0x2a - 0x22];
    char far * far *h2a;
    char pad2e[0x34 - 0x2e];
    char far * far *h34;
};

struct Win {
    struct Rect rect;
    char pad08[4];
    int count;
    char pad0E[0x1c - 0x0e];
    int flags;
    char pad1E[0x2c - 0x1e];
    struct Obj far *objs[1];
};

extern int far f_171C_1686(struct Win far * far *handle);
extern void far f_171C_13E4(char far * far *handle);
extern void far f_171C_2086(struct Win far * far *handle);
extern void far f_171C_20E2(struct Win far * far *handle);
extern struct Rect far fd_50F6_4892[];

void _fastcall f_23AE_01DB(int win)
{
    char far * far * far *p;
    int n;
    struct Win far * far *h;
    int i;
    struct Obj far *obj;
    struct Win far *w;

    if (g_644C) {
        n = win >> 8;
        h = (struct Win far * far *)g_9230[n];
        if (g_8DA6[n] == 0)
            Punt("Attemp to unlock when not locked!!");
        if (f_171C_1686(h) == 5)
            Punt("Attemp to unlock when discarded win %x", win);
        if (--g_8DA6[n] == 0) {
            if (!((*h)->flags & 0x200) && ((*h)->flags & 0x800) && g_644E == 0) {
                w = *h;
                for (i = 0; i < w->count; i++) {
                    obj = w->objs[i];
                    switch (obj->type) {
                    case 4:
                    case 10:
                        p = &obj->h34;
                        break;
                    case 16:
                    case 17:
                    case 18:
                        p = &obj->h2a;
                        break;
                    default:
                        continue;
                    }
                    if (*p) {
                        f_171C_13E4(*p);
                        *p = 0;
                    }
                }
                f_171C_2086(h);
                f_171C_20E2(h);
                g_9230[n] = 0;
                g_8CF2[n] = 0;
                fd_50F6_4892[n] = *(struct Rect far *)((char far *)w->objs[0] + 8);
            } else {
                f_171C_2086(h);
            }
        }
    }
}
/* SCAFFOLD END */

extern int far WinPrintf(char far *format, ...);
extern void far f_24FA_00B5(void);

void far f_23AE_035D(void)
{
    WinPrintf("WINLOCKERR!! ALREADY LOCKED!!");
    f_24FA_00B5();
}

void _fastcall f_23AE_036F(int win)
{
    f_23AE_0069(win, 1);
}

void _fastcall f_23AE_0377(int win)
{
    f_23AE_0069(win, 0);
}
