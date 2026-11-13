/*
 * Draws and edits a text entry field. It converts character cell positions into pixels and
 * handles acceptance or cancellation.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 9 (S09); segment 36EE; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 */

#include "events_ids.h"

extern char near fontWidth;
extern char near gfx_font_height_pixels;
extern void far gfx_put_fixed_font_char(int x, int y, int c);

/*
 * Injected key consumed before reading a new BIOS key in text entry.
 */
char text_entry_pending_key = 0;

int far ui_edit_text_field(int x, int y, char far *text, int maxLen, int flags);

/* draws count blanks from (x, y) */
/*
 * Erase a count of fixed-font cells beginning at pixel x/y.
 */
void far ui_clear_text_cells(int x, int y, int count)
{
    while (count--) {
        gfx_put_fixed_font_char(x, y, ' ');
        x += fontWidth;
    }
}

/* text-cell to pixel coordinates, then edit */
/*
 * Edit text at packed cell coordinates, forwarding the buffer limit and editing flags.
 */
void far ui_edit_text_at_cells(int col, int row, char far *text, int maxLen, int flags)
{
    ui_edit_text_field(col = (col >> 8) + fontWidth * (col & 0xff),
                  row = gfx_font_height_pixels * (row & 0xff) + (char)(row >> 8) * gfx_font_height_pixels / 14,
                  text, maxLen, flags);
}

#include "event.h"

extern int clip_window_z_order;
extern char g_4366;
extern int _fastcall win_GetEvent(struct Event far *ev);
extern int far f_1FD2_0542(void);
extern void far kbd_disable_mouse_emulation(void);
extern void far kbd_drain_bios_chars(void);
extern unsigned far _fstrlen(char far *s);
extern void far GPutStr(int x, int y, char far *text);
extern char far * far _fstrcpy(char far *d, char far *s);
extern int far kbd_poll_bios_key(void);
extern int far win_Events(void);
extern long far TickCount(void);
extern int far kbd_read_bios_char(void);
extern char far * far _fstrchr(char far *s, int c);
extern void far * far _fmemmove(void far *dst, void far *src, unsigned n);
extern void far snd_start_effect_one_if_music(void);
extern void far kbd_enable_mouse_emulation(void);

/* edits a text field at (x, y); returns the new length + 1, 0 when cancelled */
int far ui_edit_text_field(int x, int y, char far *text, int maxLen, int flags)
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
    saved = clip_window_z_order;
    while (win_GetEvent(&ev) || f_1FD2_0542())
        ;
    kbd_disable_mouse_emulation();
    kbd_drain_bios_chars();
    if (clip_window_z_order != saved)
        return 0;
    if (flags) {
        len = _fstrlen(text);
        GPutStr(x, y, text);
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
            if (kbd_poll_bios_key() || text_entry_pending_key || win_Events()) {
                if (blink != 1)
                    break;
            } else {
                if (clip_window_z_order != saved)
                    goto done;
                if (TickCount() != lastTick) {
                    lastTick = TickCount();
                    cnt++;
                }
                if (cnt <= 6)
                    continue;
            }
            blink = !blink;
            gfx_put_fixed_font_char(x, y, blink ? '_' : key);
            cnt = 0;
        }
        if (win_Events())
            goto done;
        if (text_entry_pending_key == 0) {
            if ((key = kbd_read_bios_char()) == 0)
                key = kbd_read_bios_char() + KEY_EXTENDED_BIT;
        } else {
            key = text_entry_pending_key;
            text_entry_pending_key = 0;
        }
        switch (key) {
        case 2:
        case KEY_EXT_HOME:
            x -= pos * fontWidth;
            pos = 0;
            break;
        case 5:
        case KEY_EXT_END:
            x += _fstrlen(&buf[pos]) * fontWidth;
            pos = len;
            break;
        case 8:
        case KEY_EXT_LEFT:
            if (pos == 0)
                snd_start_effect_one_if_music();
            else {
                pos--;
                x -= fontWidth;
            }
            if (key != 8)
                break;
        case 4:
        case KEY_EXT_DELETE:
            if (len == 0 || len == pos) {
                snd_start_effect_one_if_music();
                break;
            }
            _fmemmove(&buf[pos], &buf[pos + 1], len - pos + 1);
            GPutStr(x, y, &buf[pos]);
            gfx_put_fixed_font_char(x + (--len - pos) * fontWidth, y, ' ');
            break;
        case 9:
        case KEY_EXT_INSERT:
            if (len >= maxLen - 1 || len == pos) {
                snd_start_effect_one_if_music();
                break;
            }
            _fmemmove(&buf[pos + 1], &buf[pos], len + 1);
            buf[pos] = ' ';
            GPutStr(x, y, &buf[pos]);
            len++;
            break;
        case 10:
        case 13:
            editing = 0;
            break;
        case 11:
        case KEY_EXT_CLEAR_TO_END:
            if (len == 0)
                goto cancel;
            ui_clear_text_cells(x, y, len - pos);
            len = pos;
            break;
        case 21:
        case KEY_EXT_RIGHT:
            if (len > pos) {
                x += fontWidth;
                pos++;
            } else
                snd_start_effect_one_if_music();
            break;
        case 27:
            if (len == 0)
                goto cancel;
            x -= pos * fontWidth;
            ui_clear_text_cells(x, y, len);
            pos = len = 0;
            break;
        default:
            if (maxLen == pos || _fstrchr(":;,.=+-_\\/*", key)) {
                snd_start_effect_one_if_music();
                break;
            }
            if (key < ' ' || key > 0x7f)
                break;
            buf[pos] = key;
            gfx_put_fixed_font_char(x, y, key);
            x += fontWidth;
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
    kbd_enable_mouse_emulation();
    text_entry_pending_key = 0;
    return len + 1;
}
