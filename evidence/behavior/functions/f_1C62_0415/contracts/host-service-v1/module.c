/* Root module 1C62: fatal error, alert and question boxes. */

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

struct Point {
    int v;
    int h;
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

struct AlertColors {
    int fill;
    int frame;
    int text;
};

static int g_54F8 = 0;

extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern int far sprintf(char far *buffer, char far *format, ...);
extern int far printf(char far *format, ...);
extern void (far * near g_9128)(int fore, int back, int pattern);
extern void far f_1CE2_01C3(int x, int y, char far *format, ...);
extern void far o15_384C_0152(char far *message, int code);

void far Punt(char far *format, ...)
{
    char text[140];
    char msg[90];

    if (g_54F8 == 0) {
        g_54F8 = 1;
        vsprintf(msg, format, (char far *)(&format + 1));
        sprintf(text, "FATAL ERROR: PROGRAM ABORTED\n%s", msg);
        printf("\n\n\n\n");
        g_9128(0, 15, 0);
        f_1CE2_01C3(0, 0, text);
        o15_384C_0152(text, 1);
    }
}

extern int far fd_55B3_6262;
extern void (far * near g_9178)(void);

void far f_1C62_0090(void)
{
    if (fd_55B3_6262)
        g_9178();
}

extern void far f_1B73_02A9(void);
extern void far f_1B73_0025(void);

void far f_1C62_00A1(void)
{
    f_1B73_02A9();
    f_1B73_0025();
}

/* Alert box.  The only exit from the key switch is "goto done"; under /Zi that label would
 * start a LEDATA record (02CB) which the original FIXUPP order excludes (no break in
 * 02A7..02F0), so this module is built with /Zd like the window library (worker resB).
 * hit[] carries the original's dead store of -1 ([bp-0Ch], never read). */
void far f_1C62_00D5(char far *msg, int timed);

void far f_1C62_00AC(char far *msg)
{
    f_1C62_00D5(msg, 0);
}

void far f_1C62_00C0(char far *msg)
{
    f_1C62_00D5(msg, 1);
}

static struct AlertColors g_550C[] = {
    { 0x0f0f, 0x0404, 0x0c0c },
    { 0x0f0f, 0x0909, 0x0b0b }
};

static struct AlertColors far *g_8CBE;
extern struct Rect far * near g_5AAC;
extern struct Pt far f_1F80_000C(char far *text);
extern void far f_1F80_01A8(struct Rect far *r, int width, int height);
extern struct Rect far * far f_1CE2_039B(struct Rect far *r);
extern char far * far GSaveRect(struct Rect far *r);
extern void far f_1CE2_046D(struct Rect far *r, int color);
extern void far f_1CE2_044D(struct Rect far *r, int width);
void far f_1C62_0306(struct Rect far *r, int line, char far *text);
extern int far f_1F80_0177(struct Rect far *r, char far *text);
extern char near g_3DDE;
extern void far o10_35F5_0000(int x, int y, char far *label, int id);
extern void far f_1FD2_02FF(void);
extern void far f_1B73_0510(void);
extern long far TickCount(void);
extern int far f_1FD2_0542(void);
int far WaitedEnough(long far *timer, int delay);
extern int far f_1F58_0038(void);
extern int far f_1F58_005A(void);
extern unsigned char near _ctype[];
extern int far f_1B73_032A(void);
extern void far f_1B73_032E(struct Event far *ev);
extern void far f_1FD2_0438(int objNum);
extern void far f_1FD2_031A(void);
extern void far f_1CE2_056C(struct Rect far *r, char far *buf);
extern void far win_FlushEvents(void);
extern void far f_1B73_050E(void);

void far f_1C62_00D5(char far *msg, int timed)
{
    int x;
    int y;
    int down;
    int hit[1];
    struct Pt size;
    long stamp;
    char far *save;
    struct Rect r;
    struct Rect pr;
    struct Event ev;
    int c;

    hit[0] = -1;
    g_8CBE = &g_550C[timed];
    g_5AAC = 0;
    size = f_1F80_000C(msg);
    f_1F80_01A8(&r, size.x + 2, size.y + 4);
    pr = *f_1CE2_039B(&r);
    save = GSaveRect(&pr);
    f_1CE2_046D(&pr, g_8CBE->fill);
    g_9128(g_8CBE->frame, g_8CBE->frame, 0x20);
    f_1CE2_044D(&pr, 4);
    g_9128(0x404, g_8CBE->fill, 0);
    f_1C62_0306(&r, r.top, msg);
    x = f_1F80_0177(&pr, "Continue") / g_3DDE;
    y = r.bottom - 2;
    g_9128(g_8CBE->frame, g_8CBE->text, 0xc0);
    o10_35F5_0000(x, y, "Continue", 0x900);
    g_9128(g_8CBE->frame, g_8CBE->text, 0);
    f_1FD2_02FF();
    f_1B73_0510();
    stamp = TickCount();
    down = f_1FD2_0542();
    for (;;) {
        if (timed && WaitedEnough(&stamp, 0x21c))
            break;
        if (f_1F58_0038()) {
            if ((c = f_1F58_005A()) == 0)
                f_1F58_005A();
            switch ((_ctype[c + 1] & 2) ? c - 0x20 : c) {
            case '\n':
            case '\r':
            case 'C':
                goto done;
            }
        }
        if (down)
            down = f_1FD2_0542();
        else if (f_1FD2_0542())
            break;
        if (f_1B73_032A()) {
            f_1B73_032E(&ev);
            if ((ev.code >> 8) == 9)
                break;
        }
    }
done:
    f_1FD2_0438(0x900);
    f_1FD2_031A();
    f_1CE2_056C(&pr, save);
    while (f_1FD2_0542())
        ;
    win_FlushEvents();
    f_1B73_050E();
}

extern int far f_24AB_030B(void);
extern char far * far _fstrchr(char far *s, int c);
extern unsigned int far _fstrlen(char far *s);
extern char far * far _fstrncpy(char far *dst, char far *src, unsigned int n);
extern void far f_1FBD_0000(int x, int y, char far *text);

void far f_1C62_0306(struct Rect far *r, int line, char far *text)
{
    int n;
    char far *nl;
    int len;
    struct Rect pr;
    char buf[80];

    line *= f_24AB_030B();
    pr = *f_1CE2_039B(r);
    n = 0;
    while (*text) {
        if ((nl = _fstrchr(text, '\n')) == 0) {
            len = _fstrlen(text);
            nl = text + len - 1;
        } else
            len = nl - text;
        _fstrncpy(buf, text, len);
        buf[len] = 0;
        text = nl + 1;
        line += f_24AB_030B();
        f_1FBD_0000(f_1F80_0177(&pr, buf), line, buf);
        n++;
    }
}

int far f_1C62_0415(char far *msg, int set);

int far f_1C62_03DA(char far *what)
{
    char buf[150];

    sprintf(buf, "%s: Are you sure?", what);
    return f_1C62_0415(buf, 0) == 0;
}

static char far *g_5554[] = { "\rYes", "\033No" };
static char far *g_555C[] = { "\rYes", "\0No", "\033Cancel" };
static char far *g_5568[] = { "\rRetry", "\033Cancel" };
static char far * far *g_5570[] = { g_5554, g_555C, g_5568 };
static struct Rect g_557C = { 9, 30, 14, 50 };
static int g_5584[] = { 2, 3, 2 };

void far f_1C62_0737(void);
extern int far f_1F58_0090(void);
extern void far o10_35F5_0A63(int key, int far *sel, int count, int id);

int far f_1C62_0415(char far *msg, int set)
{
    int c;
    int i;
    int j;
    int h;
    int v;
    int width;
    int count;
    int sel;
    char far * far *labels;
    struct Pt size;
    char far *save;
    struct Rect pr;
    int widths[8];
    struct Event ev;

    sel = -1;
    f_1C62_0737();
    labels = g_5570[set];
    size = f_1F80_000C(msg);
    width = size.x;
    count = g_5584[set];
    c = v = h = j = 0;
    for (; j < count;) {
        widths[j] = _fstrlen(labels[j] + 1);
        h += widths[j];
        j++;
        c += 2;
    }
    if (width < c)
        width = c;
    f_1F80_01A8(&g_557C, width + 2, size.y + 4);
    pr = *f_1CE2_039B(&g_557C);
    save = GSaveRect(&pr);
    f_1CE2_046D(&pr, 0xf2f);
    g_9128(0x404, 0x404, 0x40);
    f_1CE2_044D(&pr, 4);
    g_9128(0, 0, 0);
    f_1CE2_044D(&pr, 1);
    g_9128(0x404, 0xf0f, 0xc0);
    f_1C62_0306(&g_557C, g_557C.top, msg);
    h = (width - h - 2) / 2 + g_557C.left;
    v = g_557C.bottom - 2;
    g_9128(0x404, 0xc0c, 0xc0);
    for (j = 0; j < count; j++) {
        o10_35F5_0000(h, v, labels[j] + 1, j + 0x900);
        h += widths[j] + 2;
    }
    f_1FD2_02FF();
    for (;;) {
        if (f_1F58_0038() && (c = f_1F58_0090()) > 0) {
            if (_ctype[c + 1] & 2)
                c -= 0x20;
            for (i = 0; i < count; i++) {
                if (labels[i][0] == c || labels[i][1] == c) {
                    ev.code = i;
                    goto done;
                }
            }
            o10_35F5_0A63(c, &sel, count, 0x900);
        }
        if (f_1B73_032A()) {
            f_1B73_032E(&ev);
            if ((ev.code >> 8) == 9)
                break;
        }
    }
done:
    for (i = 0; i < count; i++)
        f_1FD2_0438(i + 0x900);
    f_1FD2_031A();
    f_1CE2_056C(&pr, save);
    return (unsigned char)ev.code;
}

extern char far * near sys_errlist[];
extern int near sys_nerr;
extern char near g_8CCB;

static char far *g_567A[] = {
    "Write-protection error",
    "Unknown unit",
    "Drive not ready",
    "Unknown command",
    "Data error (bad CRC)",
    "Bad request structure length",
    "seek error",
    "unknown media type",
    "sector not found",
    "printer out of paper",
    "write fault",
    "read fault",
    "general failure",
    "abort request"
};

static int g_56B2 = 12;

char far * far f_1C62_06A6(int err)
{
    if (err > sys_nerr || err < 0)
        return g_567A[g_8CCB];
    return sys_errlist[err];
}

int far WaitedEnough(long far *timer, int delay)
{
    int result;

    if (TickCount() < *timer || *timer + delay <= TickCount())
        result = 1;
    else
        result = 0;
    if (result)
        *timer = TickCount();
    return result;
}

void far f_1C62_0737(void)
{
    while (f_1F58_0038())
        f_1F58_005A();
}

char far * far f_1C62_074E(struct Rect far *r, int width, int height, int timed)
{
    char far *save;

    f_1F80_01A8(r, width, height);
    *r = *f_1CE2_039B(r);
    save = GSaveRect(r);
    g_8CBE = &g_550C[timed];
    g_5AAC = 0;
    f_1CE2_046D(r, g_8CBE->fill);
    g_9128(g_8CBE->frame, g_8CBE->frame, 0x20);
    f_1CE2_044D(r, 4);
    g_9128(0x404, g_8CBE->fill, 0);
    return save;
}
