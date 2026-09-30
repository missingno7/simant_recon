/* Overlay section S10, code frame 35F5: pull-down menu bar. */

#include <stdio.h>
#include <string.h>
#include <ctype.h>

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

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

struct Pt {
    int x;
    int y;
};

static int curMenu = -1;

extern char near g_3DDE;
extern char near g_3DDC;
extern void far f_1CE2_044D(struct Rect far *r, int width);
extern int near g_3DE4;
extern int near g_3DE0;
extern int near g_3DE2;
extern void (far * near g_9128)(int a, int b, int c);
extern void far f_1FBD_0000(int x, int y, char far *s);
extern void far f_1FD2_03EB(struct Rect far *r, int v);

void far o10_35F5_0000(int x, int y, char far *s, int v)
{
    int len;
    struct Rect r;

    len = _fstrlen(s);
    r.left = x = (char)(x >> 8) + (x & 0xff) * g_3DDE;
    r.right = x + g_3DDE * len - 1;
    r.top = y = g_3DDC * (y & 0xff) + (char)(y >> 8) * g_3DDC / 14;
    r.bottom = y + g_3DDC - 1;
    f_1CE2_044D(&r, -3);
    (*g_9128)(g_3DE2, g_3DE0, g_3DE4);
    f_1CE2_044D(&r, -2);
    (*g_9128)(g_3DE2, g_3DE0, g_3DE4);
    f_1FBD_0000(x, y, s);
    f_1FD2_03EB(&r, v);
}

extern void far f_1B4E_0110(int x, int y, int c);

void far o10_35F5_00D7(int x, int y, char far *s, int v)
{
    int len;
    struct Rect r;

    len = _fstrlen(s);
    r.left = x = (char)(x >> 8) + (x & 0xff) * g_3DDE;
    r.right = x + g_3DDE - 1;
    r.top = y = g_3DDC * (y & 0xff) + (char)(y >> 8) * g_3DDC / 14;
    r.bottom = y + g_3DDC * len - 1;
    f_1CE2_044D(&r, -5);
    (*g_9128)(g_3DE2, g_3DE0, g_3DE4);
    f_1CE2_044D(&r, -2);
    (*g_9128)(g_3DE2, g_3DE0, g_3DE4);
    while (*s) {
        f_1B4E_0110(x, y, *s);
        s++;
        y += g_3DDC;
    }
    f_1FD2_03EB(&r, v);
}

extern void (far * near g_9130)(void);
extern char far * far * far * far fd_55B3_6054;
extern int far f_1FD2_0542(void);
extern int far fd_50F6_46A8[];
extern void far f_1FD2_0008(int x, int y, int mode, char far *s);
int far o10_35F5_0384(char far *sel, char far * far *items);
extern int far f_1F58_0038(void);
extern char far f_1F58_005A(void);
extern int far fd_55B3_604C;
extern void far f_1B73_09E9(int x, int y);
extern void far f_1F58_007F(int c);

int far o10_35F5_01C3(struct Event far *ev)
{
    int m;
    int prev;
    char sel;
    char c;

    (*g_9130)();
    m = ev->code & 0xff;
    if (fd_55B3_6054[0][m][0] & 0x80)
        return 0;
    if ((!f_1FD2_0542() && (char)(ev->modifiers >> 8)) || curMenu == m)
        return;
    if (curMenu != -1) {
again:
        f_1FD2_0008(fd_50F6_46A8[curMenu], 1, 1, fd_55B3_6054[0][curMenu]);
        curMenu = -1;
    }
    if (m >= 100)
        return;
    curMenu = m;
    f_1FD2_0008(fd_50F6_46A8[m], 1, 0, fd_55B3_6054[0][m]);
    if (!o10_35F5_0384(&sel, fd_55B3_6054[m + 1]))
        return;
    m = 0xff;
    if (!f_1F58_0038())
        goto again;
    if (f_1F58_005A())
        goto again;
    c = f_1F58_005A();
    prev = curMenu;
next:
    if (c == 0x4b) {
        if (prev)
            m = prev - 1;
        else
            m = fd_55B3_604C - 1;
    } else if (c == 0x4d) {
        m = (prev + 1) % fd_55B3_604C;
    } else {
        f_1F58_007F(c);
        f_1F58_007F(0);
        m = 0xff;
        goto again;
    }
    if (fd_55B3_6054[0][m][0] & 0x80) {
        prev = m;
        goto next;
    }
    f_1B73_09E9(fd_50F6_46A8[m] + g_3DDE * 3, g_3DDC / 2);
    goto again;
}

extern char far * far f_171C_2208(unsigned size);
extern char far * near g_5AAC;
extern void far f_1F80_0081(int a);
extern void far f_1B73_0A40(void);
extern void far f_1FD2_04D0(struct Pt far *pt);
extern int far fd_50F6_46BC[];
extern int far fd_55B3_5AA0[2];
extern char far * far f_1CE2_04C9(struct Rect far *r);
extern void far f_1FD2_02B1(int a);
extern void far Punt(char far *fmt, ...);
extern void far f_1FD2_02FF(void);
extern int far f_1B73_032A(void);
extern void far f_1B73_032E(struct Event far *ev);
extern int far f_1FD2_04E5(struct Pt far *pt, struct Rect far *r);
extern int far f_1F58_0090(void);
extern void far f_1B73_030F();
extern void far f_1FD2_031A(void);
extern void far f_1B73_0A6C(void);
extern void far f_1CE2_056C(struct Rect far *r, char far *buf);
extern void far f_171C_2276(char far *block);

/* SCAFFOLD BEGIN: o10_35F5_0384 (pull-down menu) best draft: logic and length close; block order of the key switch, local slot layout and the dead old=0 store differ */
int far o10_35F5_0384(char far *sel, char far * far *items)
{
    int j;
    int t;
    int key;
    int old;
    int cur;
    char far *p;
    int nItems;
    int maxLen;
    int x;
    int i;
    int len;
    int down;
    struct Pt last;
    struct Pt pt;
    struct Rect r;
    struct Rect saveR;
    int k;
    int d;
    int result;
    char fmt[10];
    struct Event ev;
    char far *saveBuf;
    char far *buf;
    char far *saved;
    int c;

    cur = -1;
    result = down = 0;
    if (items == 0 || *items == 0)
        goto none;
    buf = f_171C_2208(4000);
    saved = g_5AAC;
    g_5AAC = 0;
    last.x = last.y = -1;
    f_1F80_0081(1);
    f_1B73_0A40();
    t = curMenu == -1 ? 0 : 1;
    f_1FD2_04D0(&pt);
    old = maxLen = i = 0;
    for (; items[i] != 0; i++) {
        len = _fstrlen(items[i]);
        if (len > maxLen)
            maxLen = len;
    }
    maxLen += 1 - t;
    nItems = i;
    if (curMenu == -1) {
        r.left = (pt.x & ~7) + 16;
        r.top = g_3DDC * (1 - i) + pt.y - 3;
    } else {
        r.left = ((fd_50F6_46BC[curMenu] - maxLen) >> 1) * g_3DDE + fd_50F6_46A8[curMenu];
        if (r.left < 0)
            r.left = 0;
        r.top = g_3DDC + 1;
    }
    r.right = g_3DDE * maxLen + r.left + 16;
    if (r.right > fd_55B3_5AA0[0]) {
        d = r.right - fd_55B3_5AA0[0];
        r.right -= d;
        r.left -= d;
    }
    if (g_3DDC + 5 > r.top)
        r.top = g_3DDC + 5;
    r.bottom = g_3DDC * i + r.top + 6;
    if (r.bottom > fd_55B3_5AA0[1] - 5) {
        d = r.bottom - fd_55B3_5AA0[1] + 5;
        r.top -= d;
        r.bottom -= d;
    }
    saveBuf = f_1CE2_04C9(&r);
    saveR = r;
    r.left += g_3DDE;
    r.right -= g_3DDE;
    r.top += 3;
    r.bottom -= 3;
    f_1FD2_02B1(1);
    f_1CE2_044D(&r, -3);
    f_1FD2_02B1(0);
    f_1CE2_044D(&r, -1);
    f_1FD2_02B1(1);
    x = r.left;
    j = r.top;
    if (t)
        sprintf(fmt, "%%-%ds", maxLen);
    else
        sprintf(fmt, "%%c%%-%ds", maxLen - 1);
    p = buf;
    for (i = 0; i < nItems; i++, j += g_3DDC) {
        if (items[i][1] == '-') {
            _fmemset(p + 1, '-', maxLen - 2);
            p[maxLen] = 0;
            p[maxLen - 1] = ' ';
            p[0] = ' ';
        } else if (t)
            sprintf(p, fmt, items[i]);
        else
            sprintf(p, fmt, i == *sel - 1 ? 16 : ' ', items[i]);
        f_1FD2_0008(x, j, 1, p);
        p[maxLen] = 0;
        p += maxLen + 1;
        if (p > buf + 4000)
            Punt("Menu data too long");
    }
    f_1FD2_02FF();
    if (!f_1FD2_0542())
        down = 0;
    k = -1;
    for (;;) {
        if (down && !f_1FD2_0542())
            goto done;
        if (f_1FD2_0542() && !down)
            down = 1;
        if (f_1B73_032A()) {
            f_1B73_032E(&ev);
            if ((char)(ev.code >> 8) == -2 && (ev.code & 0xff) != curMenu)
                goto other;
        }
        if (down) {
            f_1FD2_04D0(&pt);
            if (_fmemcmp(&pt, &last, 4) == 0)
                continue;
            last = pt;
            if (f_1FD2_04E5(&pt, &r)) {
                k = (pt.y - r.top) / g_3DDC;
                if (k >= 0 && k < nItems &&
                    items[k][1] != '-' && !(items[k][0] & 0x80))
                    goto moved;
            }
            k = -1;
        } else if (f_1F58_0038()) {
            key = f_1F58_0090();
            if (!(key & 0x800) && islower(key))
                key -= 0x20;
            old = cur;
            j = 0;
            k = cur;
retry:
            switch (key) {
            case 10:
            case 13:
            case ' ':
            case 0x852:
            case 0x853:
                goto done;
            case 27:
                goto escape;
            default:
                old = k;
                if (key & 0x800)
                    goto flush;
                j = t = cur;
                if (!isalpha(key))
                    goto restore;
                k = t;
nextc:
                if (++k < nItems)
                    goto trych;
                k = -1;
                goto testc;
            case '+':
            case 0x850:
                k = (k + 1) % nItems;
                goto check;
            case '-':
            case 0x848:
                k = (k > 0 ? k : nItems) - 1;
check:
                if (items[k][1] != '-' && !(items[k][0] & 0x80))
                    goto warp;
                if (j <= 16) {
                    j++;
                    goto retry;
                }
                k = cur;
                break;
trych:
                c = items[k][1];
                if (islower(c))
                    c -= 0x20;
                if (c == key)
                    goto found;
testc:
                if (t != k)
                    goto nextc;
restore:
                k = old;
            }
        }
moved:
        if (cur == k)
            continue;
        if (cur != -1) {
            f_1FD2_0008(x, g_3DDC * cur + r.top, 1, buf + (maxLen + 1) * cur);
            cur = -1;
        }
        if (k == -1)
            continue;
        cur = k;
        f_1FD2_02B1(0);
        f_1FD2_0008(x, g_3DDC * k + r.top, 0, buf + (maxLen + 1) * k);
    }
found:
    old = k;
warp:
    f_1B73_09E9(g_3DDE * 4 + x, g_3DDC / 2 + g_3DDC * k + r.top);
    goto moved;
flush:
    f_1F58_007F(key & 0xff);
    f_1F58_007F(0);
escape:
    cur = -1;
done:
    if (!f_1FD2_0542() && curMenu != -1) {
        if (cur != -1)
            f_1B73_030F((curMenu << 4) + cur - 0x2ff, 0, 0, 0);
        result = 1;
    }
    if (cur != -1)
        *sel = cur + 1;
    f_1FD2_031A();
    f_1B73_0A6C();
    f_1CE2_056C(&saveR, saveBuf);
    g_5AAC = saved;
    f_171C_2276(buf);
    return result;
other:
    f_1B73_030F(ev.code, ev.xE, ev.h, ev.v, 0);
    goto done;
none:
    if (curMenu != -1)
        f_1B73_030F((curMenu - 0x30) << 4, 0, 0, 0);
    *sel = 0;
    return 1;
}
/* SCAFFOLD END */

extern void far f_1B73_0C80(int item);

int far o10_35F5_0A63(int key, int far *sel, int count, int base)
{
    int i;

    i = *sel;
    if (key == '+') {
        if (++i >= count)
            i = 0;
    } else if (key == '-') {
        if (--i < 0)
            i = count - 1;
    } else
        return 0;
    f_1B73_0C80(i + base);
    *sel = i;
    return 1;
}
