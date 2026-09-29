/* Root module 218D: window event dispatch. */

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};

long g_6364 = -1;
int g_6368 = -1;
static char g_8CEC;

extern void _fastcall f_23AE_0377(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern void _fastcall f_23E6_0A53(struct Event far *ev);
extern void _fastcall f_23E6_0B11(struct Event far *ev);
extern char far * _fastcall win_WinAddr(int win);
extern void _fastcall o26_39C7_040F(struct Event far *ev);
extern void far f_1E57_0DAA(void);
extern void far f_1E57_0351(void);
extern void _fastcall f_22BF_0375(int obj, int state);
extern void far f_208F_0530(int ticks);
extern void far f_1E57_0EB9(void);
extern struct Event far fd_50F6_49FA;
extern struct Event far fd_50F6_4A0A;
extern long far TickCount(void);
extern void _fastcall f_23AE_01DB(int win);

void _fastcall f_218D_000C(struct Event far *ev)
{
    char far *obj;

    f_23AE_0377(ev->code);
    obj = win_ObjAddr(ev->code);
    switch (obj[0x21]) {
    case 4:
        f_23E6_0A53(ev);
        goto check;
    case 7:
    case 8:
        f_23E6_0B11(ev);
        goto check;
    case 12:
    case 18:
        if (*(int far *)(win_WinAddr(ev->code) + 0x1c) & 2)
            o26_39C7_040F(ev);
        break;
    }
    if (*(int far *)(obj + 0x24) & 0x800) {
        f_1E57_0DAA();
        f_1E57_0351();
        if (*(int far *)(obj + 0x24) & 8) {
            if (!(*(int far *)(obj + 0x24) & 0x20) || !(*(int far *)(obj + 0x24) & 0x400) || !(*(int far *)(obj + 0x24) & 4))
                f_22BF_0375(ev->code, !(*(int far *)(obj + 0x24) & 4));
        } else if (*(int far *)(obj + 0x24) & 1) {
            f_22BF_0375(ev->code, !(*(int far *)(obj + 0x24) & 4));
            f_208F_0530(5);
            f_22BF_0375(ev->code, !(*(int far *)(obj + 0x24) & 4));
        }
        f_1E57_0EB9();
    }
check:
    if (fd_50F6_4A0A.code == fd_50F6_49FA.code && TickCount() - 10 < g_6364) {
        if (((fd_50F6_4A0A.modifiers ^ fd_50F6_49FA.modifiers) & 0x0a00) == 0) {
            fd_50F6_49FA.modifiers &= ~0x0a00;
            if (fd_50F6_4A0A.modifiers & 0x0800)
                fd_50F6_49FA.modifiers |= 0x4000;
            if (fd_50F6_4A0A.modifiers & 0x0200)
                fd_50F6_49FA.modifiers |= 0x2000;
            g_6364 = -1;
            goto done;
        }
    }
    g_6364 = TickCount();
    fd_50F6_4A0A = fd_50F6_49FA;
done:
    f_23AE_01DB(ev->code);
}

void far f_218D_01EB(void)
{
    g_6368 = -1;
}

int far f_218D_01F2(void)
{
    return g_6368;
}

extern void far f_1E57_0A9C(char far *p);
extern char g_5A9C[];
extern void _fastcall f_22BF_0271(int obj);

void _fastcall f_218D_01F6(int obj)
{
    f_1E57_0DAA();
    f_1E57_0A9C(g_5A9C);
    if (g_6368 != -1)
        f_22BF_0271(g_6368);
    if (obj != -1)
        f_22BF_0271(obj);
    g_6368 = obj;
    f_1E57_0EB9();
}

extern int g_5702[];
extern int far f_1B73_0BFF(void);

void _fastcall f_218D_023A(struct Event far *ev)
{
    int obj;

    if ((char)(g_5702[0] >> 8) == (unsigned char)ev->code) {
        f_23AE_0377(g_5702[0]);
        obj = f_1B73_0BFF();
        if (obj != 0 && (obj & 0xff00) == g_5702[0] && g_6368 != obj &&
            (*(int far *)(win_ObjAddr(obj) + 0x24) & 0x10))
            f_218D_01F6(obj);
        else if (g_6368 != -1 && !(*(int far *)(win_ObjAddr(g_6368) + 0x24) & 0x400) && obj != g_6368)
            f_218D_01F6(-1);
        f_23AE_01DB(g_5702[0]);
    }
}

extern void far f_1B28_0069(void);
extern void far f_0000_046F(void);
extern int far f_1B73_032A(void);
extern void far f_1B73_032E(struct Event far *ev);
void _fastcall f_218D_0451(struct Event far *ev);
extern void _fastcall f_20E8_0776(int win);
void far f_218D_042B(void);
extern void _fastcall f_20E8_0635(int win);
extern void _fastcall o26_39C7_0671(struct Event far *ev);
extern void _fastcall o26_39C7_0000(int win);
void _fastcall f_218D_0656(int dir);

void far f_218D_02D5(void)
{
    f_1B28_0069();
    f_0000_046F();
    if (g_8CEC != 0 || !f_1B73_032A())
        return;
    f_1B73_032E(&fd_50F6_49FA);
    if (fd_50F6_49FA.code == (int)0xff00) {
        f_218D_0451(&fd_50F6_49FA);
    } else if ((char)(fd_50F6_49FA.code >> 8) == (char)0xfb) {
        f_218D_023A(&fd_50F6_49FA);
    } else {
        if (g_5702[0] != (int)0x8000) {
            switch (fd_50F6_49FA.code) {
            case 0xf081:
                o26_39C7_040F(0L);
                break;
            case 0xf082:
                f_20E8_0776(g_5702[0]);
                f_218D_042B();
                return;
            case 0xf083:
                f_20E8_0635(g_5702[0]);
                f_218D_042B();
                return;
            case 0xf084:
                o26_39C7_0671(0L);
                return;
            case 0xf085:
                o26_39C7_0000(g_5702[0]);
                f_218D_042B();
                return;
            case 0xf086:
                if (g_5702[0] != (int)0x8000)
                    f_218D_0656(1);
                break;
            case 0xf087:
                if (g_5702[0] != (int)0x8000)
                    f_218D_0656(-1);
                break;
            default:
                if (!(fd_50F6_49FA.code & 0x8000)) {
                    if ((fd_50F6_49FA.code & 0xff00) != g_5702[0])
                        return;
                    f_218D_000C(&fd_50F6_49FA);
                }
                break;
            }
        }
    }
    g_8CEC = 1;
}

int far f_218D_03E8(void)
{
    f_218D_02D5();
    return g_8CEC;
}

int _fastcall f_218D_03F1(struct Event far *ev)
{
    f_218D_02D5();
    if (g_8CEC) {
        g_8CEC = 0;
        *ev = fd_50F6_49FA;
        f_218D_02D5();
        return 1;
    }
    return 0;
}

void far f_218D_042B(void)
{
    struct Event ev;

    while (f_1B73_032A())
        f_1B73_032E(&ev);
    g_8CEC = 0;
}

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far f_1FD2_04E5(int far *pt, struct Rect far *rect);
extern void _fastcall f_20E8_0725(int win);

void _fastcall f_218D_0451(struct Event far *ev)
{
    int top;
    int noClose;
    struct Rect r;
    int i;

    top = g_5702[0];
    if (top == (int)0x8000)
        return;
    win_GetObjRect(top, &r);
    f_23AE_0377(top);
    noClose = (*(unsigned far *)(win_WinAddr(top) + 0x1c) & 0x40) >> 6;
    if (!f_1FD2_04E5(&ev->h, &r) && (*(int far *)(win_WinAddr(top) + 0x1c) & 1))
        f_20E8_0635(top);
    f_23AE_01DB(top);
    if (noClose == 0) {
        for (i = 0; g_5702[i] != (int)0x8000; i++) {
            win_GetObjRect(g_5702[i], &r);
            if (f_1FD2_04E5(&ev->h, &r)) {
                f_20E8_0725(g_5702[i]);
                break;
            }
        }
    }
}

struct Pt {
    int x;
    int y;
};

extern char far * far f_2505_0006(int win);
extern void far f_1FD2_04D0(struct Pt far *pt);
extern void far f_1B73_0C80(int obj);

int far f_218D_052F(void)
{
    unsigned long d;
    unsigned long best;
    int top;
    int found;
    char far *obj;
    char far *w;
    struct Pt pt;
    int i;
    int dx;
    int dy;

    found = -1;
    top = g_5702[0];
    best = 0xffffffffL;
    f_23AE_0377(top);
    w = f_2505_0006(top);
    f_1FD2_04D0(&pt);
    for (i = 1; i < *(int far *)(w + 0xc); i++) {
        obj = ((char far * far *)(w + 0x2c))[i];
        if (*(int far *)(obj + 0x24) & 2) {
            if (f_1FD2_04E5((int far *)&pt, (struct Rect far *)obj)) {
                f_23AE_01DB(top);
                return top + i;
            }
            dy = pt.y - (((struct Rect far *)obj)->top + ((struct Rect far *)obj)->top) / 2;
            dx = pt.x - (((struct Rect far *)obj)->right + ((struct Rect far *)obj)->left) / 2;
            d = (long)dy * dy + (long)dx * dx;
            if (d < best) {
                best = d;
                found = top + i;
            }
        }
    }
    if (found != -1)
        f_1B73_0C80(found);
    f_23AE_01DB(top);
    return -1;
}

extern int _fastcall f_22BF_0AC5(int win);
extern int _fastcall f_22BF_0A97(int obj);

void _fastcall f_218D_0656(int dir)
{
    int start;
    int last;
    int cur;

    if (g_5702[0] == (int)0x8000)
        return;
    cur = start = f_218D_052F();
    last = g_5702[0] + f_22BF_0AC5(g_5702[0]);
    if (start == -1)
        return;
    do {
        cur += dir;
        if (g_5702[0] + 1 > cur)
            cur = last - 1;
        else if (last <= cur)
            cur = g_5702[0] + 1;
        if (f_22BF_0A97(cur)) {
            f_1B73_0C80(cur);
            return;
        }
    } while (start != cur);
}
