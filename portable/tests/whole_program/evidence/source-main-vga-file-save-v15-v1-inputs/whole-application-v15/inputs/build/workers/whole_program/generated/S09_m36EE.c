#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Overlay section S09, code frame 36EE: text entry field helpers. */

extern void  f_1B4E_0110(int16_t x, int16_t y, int16_t c);

char g_2970 = 0;

int16_t  o09_36EE_0092(int16_t x, int16_t y, char  *text, int16_t maxLen, int16_t flags);

/* draws count blanks from (x, y) */
void  o09_36EE_000A(int16_t x, int16_t y, int16_t count)
{
    while (count--) {
        f_1B4E_0110(x, y, ' ');
        x += SIM_GRAPHICS_SOURCE_g_3DDE;
    }
}

/* text-cell to pixel coordinates, then edit */
void  o09_36EE_003C(int16_t col, int16_t row, char  *text, int16_t maxLen, int16_t flags)
{
    o09_36EE_0092(col = (col >> 8) + SIM_GRAPHICS_SOURCE_g_3DDE * (col & 0xff),
                  row = SIM_GRAPHICS_SOURCE_g_3DDC * (row & 0xff) + (char)(row >> 8) * SIM_GRAPHICS_SOURCE_g_3DDC / 14,
                  text, maxLen, flags);
}

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

extern int16_t g_5702;
extern char g_4366;
extern int16_t  win_GetEvent(struct Event  *ev);
extern int16_t  StillDown(void);
extern void  f_1B73_0A40(void);
extern void  f_1C62_0737(void);

extern void  f_1FBD_0000(int16_t x, int16_t y, char  *text);

extern int16_t  f_1F58_0038(void);
extern int16_t  win_Events(void);
extern int32_t  TickCount(void);
extern int16_t  f_1F58_005A(void);


extern void  f_00DF_016C(void);
extern void  f_1B73_0A6C(void);

/* edits a text field at (x, y); returns the new length + 1, 0 when cancelled */
int16_t  o09_36EE_0092(int16_t x, int16_t y, char  *text, int16_t maxLen, int16_t flags)
{
    char buf[100];
    struct Event ev;
    int16_t editing;
    int16_t cnt;
    int16_t saved;
    int16_t pos;
    int16_t len;
    int32_t lastTick;
    int16_t key;
    char blink;
    char  *p;

    blink = 0;
    cnt = 0;
    saved = g_5702;
    while (win_GetEvent(&ev) || StillDown())
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
            x -= pos * SIM_GRAPHICS_SOURCE_g_3DDE;
            pos = 0;
            break;
        case 5:
        case 0x84F:
            x += _fstrlen(&buf[pos]) * SIM_GRAPHICS_SOURCE_g_3DDE;
            pos = len;
            break;
        case 8:
        case 0x84B:
            if (pos == 0)
                f_00DF_016C();
            else {
                pos--;
                x -= SIM_GRAPHICS_SOURCE_g_3DDE;
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
            f_1B4E_0110(x + (--len - pos) * SIM_GRAPHICS_SOURCE_g_3DDE, y, ' ');
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
                x += SIM_GRAPHICS_SOURCE_g_3DDE;
                pos++;
            } else
                f_00DF_016C();
            break;
        case 27:
            if (len == 0)
                goto cancel;
            x -= pos * SIM_GRAPHICS_SOURCE_g_3DDE;
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
            x += SIM_GRAPHICS_SOURCE_g_3DDE;
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

#pragma pack(pop)
