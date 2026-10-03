#include "portable/whole_program/platform/crt_abi.h"
/* Root module 1C62: fatal error, alert and question boxes. */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t x;
    int16_t y;
};

struct Point {
    int16_t v;
    int16_t h;
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};

struct AlertColors {
    int16_t fill;
    int16_t frame;
    int16_t text;
};

static int16_t g_54F8 = 0;

extern int16_t  vsprintf(char  *buffer, char  *format, char  *args);
extern int16_t  sprintf(char  *buffer, char  *format, ...);
extern int16_t  printf(char  *format, ...);
extern void ( *  g_9128)(int16_t fore, int16_t back, int16_t pattern);
extern void  f_1CE2_01C3(int16_t x, int16_t y, char  *format, ...);
extern void  o15_384C_0152(char  *message, int16_t code);

void  Punt(char  *format, ...)
{
    char text[140];
    char msg[90];

    if (g_54F8 == 0) {
        g_54F8 = 1;
        vsprintf(msg, format, (char  *)(&format + 1));
        sprintf(text, "FATAL ERROR: PROGRAM ABORTED\n%s", msg);
        printf("\n\n\n\n");
        g_9128(0, 15, 0);
        f_1CE2_01C3(0, 0, text);
        o15_384C_0152(text, 1);
    }
}

extern int16_t  fd_55B3_6262;
extern void ( *  g_9178)(void);

void  f_1C62_0090(void)
{
    if (fd_55B3_6262)
        g_9178();
}

extern void  f_1B73_02A9(void);
extern void  f_1B73_0025(void);

void  f_1C62_00A1(void)
{
    f_1B73_02A9();
    f_1B73_0025();
}

/* Alert box.  The only exit from the key switch is "goto done"; under /Zi that label would
 * start a LEDATA record (02CB) which the original FIXUPP order excludes (no break in
 * 02A7..02F0), so this module is built with /Zd like the window library (worker resB).
 * hit[] carries the original's dead store of -1 ([bp-0Ch], never read). */
void  f_1C62_00D5(char  *msg, int16_t timed);

void  f_1C62_00AC(char  *msg)
{
    f_1C62_00D5(msg, 0);
}

void  f_1C62_00C0(char  *msg)
{
    f_1C62_00D5(msg, 1);
}

static struct AlertColors g_550C[] = {
    { 0x0f0f, 0x0404, 0x0c0c },
    { 0x0f0f, 0x0909, 0x0b0b }
};

static struct AlertColors  *g_8CBE;
extern struct Rect  *  g_5AAC;
extern struct Pt  f_1F80_000C(char  *text);
extern void  f_1F80_01A8(struct Rect  *r, int16_t width, int16_t height);
extern struct Rect  *  f_1CE2_039B(struct Rect  *r);
extern char  *  GSaveRect(struct Rect  *r);
extern void  f_1CE2_046D(struct Rect  *r, int16_t color);
extern void  f_1CE2_044D(struct Rect  *r, int16_t width);
void  f_1C62_0306(struct Rect  *r, int16_t line, char  *text);
extern int16_t  f_1F80_0177(struct Rect  *r, char  *text);
extern char  g_3DDE;
extern void  o10_35F5_0000(int16_t x, int16_t y, char  *label, int16_t id);
extern void  f_1FD2_02FF(void);
extern void  f_1B73_0510(void);
extern int32_t  TickCount(void);
extern int16_t  f_1FD2_0542(void);
int16_t  WaitedEnough(int32_t  *timer, int16_t delay);
extern int16_t  f_1F58_0038(void);
extern int16_t  f_1F58_005A(void);

extern int16_t  f_1B73_032A(void);
extern void  f_1B73_032E(struct Event  *ev);
extern void  f_1FD2_0438(int16_t objNum);
extern void  f_1FD2_031A(void);
extern void  f_1CE2_056C(struct Rect  *r, char  *buf);
extern void  win_FlushEvents(void);
extern void  f_1B73_050E(void);

void  f_1C62_00D5(char  *msg, int16_t timed)
{
    int16_t x;
    int16_t y;
    int16_t down;
    int16_t hit[1];
    struct Pt size;
    int32_t stamp;
    char  *save;
    struct Rect r;
    struct Rect pr;
    struct Event ev;
    int16_t c;

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
            switch ((sim_msc_ctype_is_lower_ascii((uint8_t)c)) ? c - 0x20 : c) {
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

extern int16_t  f_24AB_030B(void);
extern char  *  _fstrchr(char  *s, int16_t c);
extern uint16_t  _fstrlen(char  *s);
extern char  *  _fstrncpy(char  *dst, char  *src, uint16_t n);
extern void  f_1FBD_0000(int16_t x, int16_t y, char  *text);

void  f_1C62_0306(struct Rect  *r, int16_t line, char  *text)
{
    int16_t n;
    char  *nl;
    int16_t len;
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

int16_t  f_1C62_0415(char  *msg, int16_t set);

int16_t  f_1C62_03DA(char  *what)
{
    char buf[150];

    sprintf(buf, "%s: Are you sure?", what);
    return f_1C62_0415(buf, 0) == 0;
}

static char  *g_5554[] = { "\rYes", "\033No" };
static char  *g_555C[] = { "\rYes", "\0No", "\033Cancel" };
static char  *g_5568[] = { "\rRetry", "\033Cancel" };
static char  *  *g_5570[] = { g_5554, g_555C, g_5568 };
static struct Rect g_557C = { 9, 30, 14, 50 };
static int16_t g_5584[] = { 2, 3, 2 };

void  f_1C62_0737(void);
extern int16_t  f_1F58_0090(void);
extern void  o10_35F5_0A63(int16_t key, int16_t  *sel, int16_t count, int16_t id);

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_1C62_0415 (button dialog): local slot layout and the kept dead
 * store y = 0 are not reproduced yet (3 bytes short). */
int16_t  f_1C62_0415(char  *msg, int16_t set)
{
    int16_t c;
    int16_t i;
    int16_t j;
    int16_t h;
    int16_t v;
    int16_t width;
    int16_t count;
    int16_t sel;
    char  *  *labels;
    struct Pt size;
    char  *save;
    struct Rect pr;
    int16_t widths[8];
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
            if (sim_msc_ctype_is_lower_ascii((uint8_t)c))
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
    return (uint8_t)ev.code;
}
/* SCAFFOLD END */

extern char  *  sim_sys_errlist[];
extern int16_t  sim_sys_nerr;
extern char  g_8CCB;

static char  *g_567A[] = {
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

static int16_t g_56B2 = 12;

char  *  f_1C62_06A6(int16_t err)
{
    if (err > sim_sys_nerr || err < 0)
        return g_567A[g_8CCB];
    return sim_sys_errlist[err];
}

int16_t  WaitedEnough(int32_t  *timer, int16_t delay)
{
    int16_t result;

    if (TickCount() < *timer || *timer + delay <= TickCount())
        result = 1;
    else
        result = 0;
    if (result)
        *timer = TickCount();
    return result;
}

void  f_1C62_0737(void)
{
    while (f_1F58_0038())
        f_1F58_005A();
}

char  *  f_1C62_074E(struct Rect  *r, int16_t width, int16_t height, int16_t timed)
{
    char  *save;

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
