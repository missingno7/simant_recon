/*
 * Displays fatal errors, alerts and confirmation questions. It also handles DOS critical errors
 * and timed waits for these dialogs.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1C62; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Loop structure and statement layout are inferred, not recovered or unique.
 */

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
extern void far gfx_printf_at(int x, int y, char far *format, ...);
extern void far app_cleanup_and_exit(char far *message, int code);

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
        gfx_printf_at(0, 0, text);
        app_cleanup_and_exit(text, 1);
    }
}

extern int far fd_55B3_6262;
extern void (far * near g_9178)(void);

void far f_1C62_0090(void)
{
    if (fd_55B3_6262)
        g_9178();
}

extern void far input_remove_hooks(void);
extern void far mouse_remove_absent_stub(void);

void far f_1C62_00A1(void)
{
    input_remove_hooks();
    mouse_remove_absent_stub();
}

/* Alert box.  STEERED (record order only): the key switch leaves the loop through
 * "continue; done: break;" at the end of the body.  A label after the loop compiles to the
 * same bytes but starts a /Zi record at 02CB that the original relocation order excludes;
 * how the original left the loop from its switch is unknown.
 * hit[] retains the original dead store of -1 ([bp-0Ch], never read). */
void far f_1C62_00D5(char far *msg, int timed);

void far ui_message_acknowledge(char far *msg)
{
    f_1C62_00D5(msg, 0);
}

void far ui_message_transient(char far *msg)
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
extern void far GRectFill(struct Rect far *r, int color);
extern void far GRectOutline(struct Rect far *r, int width);
void far f_1C62_0306(struct Rect far *r, int line, char far *text);
extern int far f_1F80_0177(struct Rect far *r, char far *text);
extern char near fontWidth;
extern void far o10_35F5_0000(int x, int y, char far *label, int id);
extern void far input_capture_screen(void);
extern void far input_noop_0510(void);
extern long far TickCount(void);
extern int far StillDown(void);
int far WaitedEnough(long far *timer, int delay);
extern int far kbd_poll_bios_key(void);
extern int far kbd_read_bios_char(void);
extern unsigned char near _ctype[];
extern int far input_event_count(void);
extern void far input_pop_event(struct Event far *ev);
extern void far input_remove_object_rect(int objNum);
extern void far input_release_screen_capture(void);
extern void far gfx_restore_and_free_rect(struct Rect far *r, char far *buf);
extern void far win_FlushEvents(void);
extern void far input_noop_050e(void);

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
    GRectFill(&pr, g_8CBE->fill);
    g_9128(g_8CBE->frame, g_8CBE->frame, 0x20);
    GRectOutline(&pr, 4);
    g_9128(0x404, g_8CBE->fill, 0);
    f_1C62_0306(&r, r.top, msg);
    x = f_1F80_0177(&pr, "Continue") / fontWidth;
    y = r.bottom - 2;
    g_9128(g_8CBE->frame, g_8CBE->text, 0xc0);
    o10_35F5_0000(x, y, "Continue", 0x900);
    g_9128(g_8CBE->frame, g_8CBE->text, 0);
    input_capture_screen();
    input_noop_0510();
    stamp = TickCount();
    down = StillDown();
    for (;;) {
        if (timed && WaitedEnough(&stamp, 0x21c))
            break;
        if (kbd_poll_bios_key()) {
            if ((c = kbd_read_bios_char()) == 0)
                kbd_read_bios_char();
            switch ((_ctype[c + 1] & 2) ? c - 0x20 : c) {
            case '\n':
            case '\r':
            case 'C':
                goto done;
            }
        }
        if (down)
            down = StillDown();
        else if (StillDown())
            break;
        if (input_event_count()) {
            input_pop_event(&ev);
            if ((ev.code >> 8) == 9)
                break;
        }
        continue;
done:
        break;
    }
    input_remove_object_rect(0x900);
    input_release_screen_capture();
    gfx_restore_and_free_rect(&pr, save);
    while (StillDown())
        ;
    win_FlushEvents();
    input_noop_050e();
}

extern int far font_FontHeight(void);
extern char far * far _fstrchr(char far *s, int c);
extern unsigned int far _fstrlen(char far *s);
extern char far * far _fstrncpy(char far *dst, char far *src, unsigned int n);
extern void far GPutStr(int x, int y, char far *text);

void far f_1C62_0306(struct Rect far *r, int line, char far *text)
{
    int n;
    char far *nl;
    int len;
    struct Rect pr;
    char buf[80];

    line *= font_FontHeight();
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
        line += font_FontHeight();
        GPutStr(f_1F80_0177(&pr, buf), line, buf);
        n++;
    }
}

int far ui_choice_prompt(char far *msg, int set);

int far f_1C62_03DA(char far *what)
{
    char buf[150];

    sprintf(buf, "%s: Are you sure?", what);
    return ui_choice_prompt(buf, 0) == 0;
}

static char far *g_5554[] = { "\rYes", "\033No" };
static char far *g_555C[] = { "\rYes", "\0No", "\033Cancel" };
static char far *g_5568[] = { "\rRetry", "\033Cancel" };
static char far * far *g_5570[] = { g_5554, g_555C, g_5568 };
static struct Rect g_557C = { 9, 30, 14, 50 };
static int g_5584[] = { 2, 3, 2 };

void far f_1C62_0737(void);
int far f_1C62_069E(void);
extern int far kbd_read_key_code(void);
extern void far o10_35F5_0A63(int key, int far *sel, int count, int id);


/* Declaration order is inferred (declaration numbers, docs/codegen-rules.md): these two
 * and the prototype of f_1C62_069E above come before ui_choice_prompt, sys_nerr after it.
 * Other placements change ui_choice_prompt or f_1C62_06A6. */
extern char far * near sys_errlist[];
extern char near g_8CCB;
/* Shows a message with a row of buttons and returns the index of the one chosen, by
 * its key or by the mouse. `v` first accumulates the minimum width of the button row
 * and later holds the buttons' vertical position, and `j` also indexes the key search:
 * the frame has one word for each and the zero stores match only this way. */
int far ui_choice_prompt(char far *msg, int set)
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
    v = h = j = 0;
    while (j < count) {
        widths[j] = _fstrlen(labels[j] + 1);
        h += widths[j];
        j++;
        v += 2;
    }
    if (width < v)
        width = v;
    f_1F80_01A8(&g_557C, width + 2, size.y + 4);
    pr = *f_1CE2_039B(&g_557C);
    save = GSaveRect(&pr);
    GRectFill(&pr, 0xf2f);
    g_9128(0x404, 0x404, 0x40);
    GRectOutline(&pr, 4);
    g_9128(0, 0, 0);
    GRectOutline(&pr, 1);
    g_9128(0x404, 0xf0f, 0xc0);
    f_1C62_0306(&g_557C, g_557C.top, msg);
    h = (width - h - 2) / 2 + g_557C.left;
    v = g_557C.bottom - 2;
    g_9128(0x404, 0xc0c, 0xc0);
    for (j = 0; j < count; j++) {
        o10_35F5_0000(h, v, labels[j] + 1, j + 0x900);
        h += widths[j] + 2;
    }
    input_capture_screen();
    for (;;) {
        if (kbd_poll_bios_key() && (c = kbd_read_key_code()) > 0) {
            if (_ctype[c + 1] & 2)
                c -= 0x20;
            for (j = 0; j < count; j++) {
                if (labels[j][0] == c || labels[j][1] == c) {
                    ev.code = j;
                    goto done;
                }
            }
            o10_35F5_0A63(c, &sel, count, 0x900);
        }
        if (input_event_count()) {
            input_pop_event(&ev);
            if ((ev.code >> 8) == 9)
                break;
        }
    }
done:
    for (i = 0; i < count; i++)
        input_remove_object_rect(i + 0x900);
    input_release_screen_capture();
    gfx_restore_and_free_rect(&pr, save);
    return (unsigned char)ev.code;
}

/* No reference to this function was found.  It calls f_1C62_0090 and returns 1; the
 * parameter list is a hypothesis (none is read). */
int far f_1C62_069E(void)
{
    f_1C62_0090();
    return 1;
}


extern int near sys_nerr;

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
    while (kbd_poll_bios_key())
        kbd_read_bios_char();
}

char far * far f_1C62_074E(struct Rect far *r, int width, int height, int timed)
{
    char far *save;

    f_1F80_01A8(r, width, height);
    *r = *f_1CE2_039B(r);
    save = GSaveRect(r);
    g_8CBE = &g_550C[timed];
    g_5AAC = 0;
    GRectFill(r, g_8CBE->fill);
    g_9128(g_8CBE->frame, g_8CBE->frame, 0x20);
    GRectOutline(r, 4);
    g_9128(0x404, g_8CBE->fill, 0);
    return save;
}
