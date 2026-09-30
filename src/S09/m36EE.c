/* Overlay section S09, code frame 36EE: text entry field helpers. */

extern char near g_3DDE;
extern char near g_3DDC;
extern void far f_1B4E_0110(int x, int y, int c);

char g_2970 = 0;

int far o09_36EE_0092(int x, int y, char far *text, int maxLen, int flags);

/* draws count blanks from (x, y) */
void far o09_36EE_000A(int x, int y, int count)
{
    while (count--) {
        f_1B4E_0110(x, y, ' ');
        x += g_3DDE;
    }
}

/* text-cell to pixel coordinates, then edit */
void far o09_36EE_003C(int col, int row, char far *text, int maxLen, int flags)
{
    o09_36EE_0092(col = (col >> 8) + g_3DDE * (col & 0xff),
                  row = g_3DDC * (row & 0xff) + (char)(row >> 8) * g_3DDC / 14,
                  text, maxLen, flags);
}

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

extern int g_5702;
extern char g_4366;
extern int _fastcall win_GetEvent(struct Event far *ev);
extern int far f_1FD2_0542(void);
extern void far f_1B73_0A40(void);
extern void far f_1C62_0737(void);
extern unsigned far _fstrlen(char far *s);
extern void far f_1FBD_0000(int x, int y, char far *text);
extern char far * far _fstrcpy(char far *d, char far *s);
extern int far f_1F58_0038(void);
extern int far win_Events(void);
extern long far TickCount(void);
extern int far f_1F58_005A(void);
extern char far * far _fstrchr(char far *s, int c);
extern void far * far _fmemmove(void far *dst, void far *src, unsigned n);
extern void far f_00DF_016C(void);
extern void far f_1B73_0A6C(void);

/* edits a text field at (x, y); returns the new length + 1, 0 when cancelled */
int far o09_36EE_0092(int x, int y, char far *text, int maxLen, int flags)
{
    char buf[100];
    struct Event ev;
    int editing;
    int cnt;
    int saved;
    int pos;
    int len;
    long lastTick;
    int key;
    char blink;
    char far *p;

    blink = 0;
    cnt = 0;
    saved = g_5702;
    while (win_GetEvent(&ev) || f_1FD2_0542())
        ;
    f_1B73_0A40();
    f_1C62_0737();
    if (g_5702 != saved)
        return 0;
    if (flags) {
        len = _fstrlen(text);
        f_1FBD_0000(x, y, text);
        _fstrcpy(buf, text);
    } else
        len = 0;
    if (maxLen <= 0)
        maxLen = 200;
    maxLen--;
    g_4366 = 1;
    pos = 0;
    editing = 1;
    while (editing) {
        if (len < pos)
            len = pos;
        buf[len] = 0;
        key = buf[pos];
        if (key == 0)
            key = ' ';
        for (;;) {
            if (f_1F58_0038() || g_2970 || win_Events()) {
                if (blink != 1)
                    break;
            } else {
                if (g_5702 != saved)
                    goto done;
                if (TickCount() != lastTick) {
                    lastTick = TickCount();
                    cnt++;
                }
                if (cnt <= 6)
                    continue;
            }
            blink = !blink;
            f_1B4E_0110(x, y, blink ? '_' : key);
            cnt = 0;
        }
        if (win_Events())
            goto done;
        if (g_2970 == 0) {
            if ((key = f_1F58_005A()) == 0)
                key = f_1F58_005A() + 0x800;
        } else {
            key = g_2970;
            g_2970 = 0;
        }
        switch (key) {
        case 2:
        case 0x847:
            x -= pos * g_3DDE;
            pos = 0;
            break;
        case 5:
        case 0x84F:
            x += _fstrlen(&buf[pos]) * g_3DDE;
            pos = len;
            break;
        case 8:
        case 0x84B:
            if (pos == 0)
                f_00DF_016C();
            else {
                pos--;
                x -= g_3DDE;
            }
            if (key != 8)
                break;
        case 4:
        case 0x853:
            if (len == 0 || len == pos) {
                f_00DF_016C();
                break;
            }
            _fmemmove(&buf[pos], &buf[pos + 1], len - pos + 1);
            f_1FBD_0000(x, y, &buf[pos]);
            f_1B4E_0110(x + (--len - pos) * g_3DDE, y, ' ');
            break;
        case 9:
        case 0x852:
            if (len >= maxLen - 1 || len == pos) {
                f_00DF_016C();
                break;
            }
            _fmemmove(&buf[pos + 1], &buf[pos], len + 1);
            buf[pos] = ' ';
            f_1FBD_0000(x, y, &buf[pos]);
            len++;
            break;
        case 10:
        case 13:
            editing = 0;
            break;
        case 11:
        case 0x893:
            if (len == 0)
                goto cancel;
            o09_36EE_000A(x, y, len - pos);
            len = pos;
            break;
        case 21:
        case 0x84D:
            if (len > pos) {
                x += g_3DDE;
                pos++;
            } else
                f_00DF_016C();
            break;
        case 27:
            if (len == 0)
                goto cancel;
            x -= pos * g_3DDE;
            o09_36EE_000A(x, y, len);
            pos = len = 0;
            break;
        default:
            if (maxLen == pos || _fstrchr(":;,.=+-_\\/*", key)) {
                f_00DF_016C();
                break;
            }
            if (key < ' ' || key > 0x7f)
                break;
            buf[pos] = key;
            f_1B4E_0110(x, y, key);
            x += g_3DDE;
            pos++;
            break;
        }
    }
done:
    for (p = buf; *p == ' '; p++)
        ;
    if (*p)
        _fmemmove(text, p, buf - p + len + 1);
    goto out;
cancel:
    len = -1;
out:
    g_4366 = 0;
    f_1B73_0A6C();
    g_2970 = 0;
    return len + 1;
}
