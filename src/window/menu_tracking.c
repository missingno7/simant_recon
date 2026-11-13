/*
 * Draws and tracks pull down menus. It formats menu text and dispatches selection while checking
 * the menu data length.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 10 (S10); segment 35F5; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Og /Oe /Gs /Zi.
 */

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

extern char near fontWidth;
extern char near gfx_font_height_pixels;
extern void far GRectOutline(struct Rect far *r, int width);
extern int near g_3DE4;
extern int near _foreColor;
extern int near g_3DE2;
extern void (far * near gfx_set_attributes_hook)(int a, int b, int c);
extern void far GPutStr(int x, int y, char far *s);
extern void far input_register_object_rect(struct Rect far *r, int v);

void far ui_draw_horizontal_button(int x, int y, char far *s, int v)
{
    int len;
    struct Rect r;

    len = _fstrlen(s);
    r.left = x = (char)(x >> 8) + (x & 0xff) * fontWidth;
    r.right = x + fontWidth * len - 1;
    r.top = y = gfx_font_height_pixels * (y & 0xff) + (char)(y >> 8) * gfx_font_height_pixels / 14;
    r.bottom = y + gfx_font_height_pixels - 1;
    GRectOutline(&r, -3);
    (*gfx_set_attributes_hook)(g_3DE2, _foreColor, g_3DE4);
    GRectOutline(&r, -2);
    (*gfx_set_attributes_hook)(g_3DE2, _foreColor, g_3DE4);
    GPutStr(x, y, s);
    input_register_object_rect(&r, v);
}

extern void far gfx_put_fixed_font_char(int x, int y, int c);

void far ui_draw_vertical_button(int x, int y, char far *s, int v)
{
    int len;
    struct Rect r;

    len = _fstrlen(s);
    r.left = x = (char)(x >> 8) + (x & 0xff) * fontWidth;
    r.right = x + fontWidth - 1;
    r.top = y = gfx_font_height_pixels * (y & 0xff) + (char)(y >> 8) * gfx_font_height_pixels / 14;
    r.bottom = y + gfx_font_height_pixels * len - 1;
    GRectOutline(&r, -5);
    (*gfx_set_attributes_hook)(g_3DE2, _foreColor, g_3DE4);
    GRectOutline(&r, -2);
    (*gfx_set_attributes_hook)(g_3DE2, _foreColor, g_3DE4);
    while (*s) {
        gfx_put_fixed_font_char(x, y, *s);
        s++;
        y += gfx_font_height_pixels;
    }
    input_register_object_rect(&r, v);
}

extern void (far * near g_9130)(void);
extern char far * far * far * far menu_resource_tables;
extern int far StillDown(void);
extern int far menu_title_x_pixels[];
extern void far menu_printf_label(int x, int y, int mode, char far *s);
int far menu_track_popup(char far *sel, char far * far *items);
extern int far kbd_poll_bios_key(void);
extern char far kbd_read_bios_char(void);
extern int far menu_bar_title_count;
extern void far mouse_set_position(int x, int y);
extern void far kbd_unread_char(int c);

int far menu_track_bar_selection(struct Event far *ev)
{
    int m;
    int prev;
    char sel;
    char c;

    (*g_9130)();
    m = ev->code & 0xff;
    if (menu_resource_tables[0][m][0] & 0x80)
        return 0;
    if ((!StillDown() && (char)(ev->modifiers >> 8)) || curMenu == m)
        return;
    if (curMenu != -1) {
again:
        menu_printf_label(menu_title_x_pixels[curMenu], 1, 1, menu_resource_tables[0][curMenu]);
        curMenu = -1;
    }
    if (m >= 100)
        return;
    curMenu = m;
    menu_printf_label(menu_title_x_pixels[m], 1, 0, menu_resource_tables[0][m]);
    if (!menu_track_popup(&sel, menu_resource_tables[m + 1]))
        return;
    m = 0xff;
    if (!kbd_poll_bios_key())
        goto again;
    if (kbd_read_bios_char())
        goto again;
    c = kbd_read_bios_char();
    prev = curMenu;
next:
    if (c == 0x4b) {
        if (prev)
            m = prev - 1;
        else
            m = menu_bar_title_count - 1;
    } else if (c == 0x4d) {
        m = (prev + 1) % menu_bar_title_count;
    } else {
        kbd_unread_char(c);
        kbd_unread_char(0);
        m = 0xff;
        goto again;
    }
    if (menu_resource_tables[0][m][0] & 0x80) {
        prev = m;
        goto next;
    }
    mouse_set_position(menu_title_x_pixels[m] + fontWidth * 3, gfx_font_height_pixels / 2);
    goto again;
}

extern char far * far malloc(unsigned size);
extern char far * near clip_active_list_offset;
extern void far timer_wait_double_ticks(int a);
extern void far kbd_disable_mouse_emulation(void);
extern void far GetMousePos(struct Pt far *pt);
extern int far menu_title_char_counts[];
extern int far fd_55B3_5AA0[2];
extern char far * far GSaveRect(struct Rect far *r);
extern void far menu_set_draw_colours(int a);
extern void far Punt(char far *fmt, ...);
extern void far input_capture_screen(void);
extern int far input_event_count(void);
extern void far input_pop_event(struct Event far *ev);
extern int far PointInRect(struct Pt far *pt, struct Rect far *r);
extern int far kbd_read_key_code(void);
extern void far input_enqueue_event_args();
extern void far input_release_screen_capture(void);
extern void far kbd_enable_mouse_emulation(void);
extern void far gfx_restore_and_free_rect(struct Rect far *r, char far *buf);
extern void far free(char far *block);


extern void far hotbox_center_pointer(int item);
int far menu_track_popup(char far *sel, char far * far *items)
{
    int j;
    int t;
    int mode;
    int key;
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
    int d;
    int result;
    char fmt[10];
    struct Event ev;
    char far *saveBuf;
    char far *buf;
    char far *saved;
    int c;

    cur = -1; down = result = 0;
    if (items != 0 && *items != 0) {
    buf = malloc(4000); saved = clip_active_list_offset;
    clip_active_list_offset = 0; last.x = last.y = -1;
    timer_wait_double_ticks(1); kbd_disable_mouse_emulation();
    mode = curMenu == -1 ? 0 : 1;
    GetMousePos(&pt);
    maxLen = i = 0;
    for (; items[i] != 0; i++) {
        len = _fstrlen(items[i]);
        if (len > maxLen)
            maxLen = len;
    }
    maxLen += 1 - mode;
    nItems = i;
    if (curMenu == -1) {
        r.left = (pt.x & ~7) + 16;
        r.top = gfx_font_height_pixels * (1 - i) + pt.y - 3;
    } else {
        r.left = ((menu_title_char_counts[curMenu] - maxLen) >> 1) * fontWidth + menu_title_x_pixels[curMenu];
        if (r.left < 0)
            r.left = 0;
        r.top = gfx_font_height_pixels + 1;
    }
    r.right = fontWidth * maxLen + r.left + 16;
    if (r.right > fd_55B3_5AA0[0]) {
        d = r.right - fd_55B3_5AA0[0];
        r.right -= d;
        r.left -= d;
    }
    if (gfx_font_height_pixels + 5 > r.top)
        r.top = gfx_font_height_pixels + 5;
    r.bottom = gfx_font_height_pixels * i + r.top + 6;
    if (r.bottom > fd_55B3_5AA0[1] - 5) {
        d = r.bottom - fd_55B3_5AA0[1] + 5;
        r.top -= d;
        r.bottom -= d;
    }
    saveBuf = GSaveRect(&r);
    saveR = r;
    r.left += fontWidth;
    r.right -= fontWidth;
    r.top += 3;
    r.bottom -= 3;
    menu_set_draw_colours(1);
    GRectOutline(&r, -3);
    menu_set_draw_colours(0);
    GRectOutline(&r, -1);
    menu_set_draw_colours(1);
    x = r.left;
    j = r.top;
    if (mode)
        sprintf(fmt, "%%-%ds", maxLen);
    else
        sprintf(fmt, "%%c%%-%ds", maxLen - 1);
    p = buf;
    for (i = 0; i < nItems; i++, j += gfx_font_height_pixels) {
        if (items[i][1] == '-') {
            _fmemset(p + 1, '-', maxLen - 2);
            p[maxLen] = 0;
            p[maxLen - 1] = ' ';
            p[0] = ' ';
        } else if (mode)
            sprintf(p, fmt, items[i]);
        else
            sprintf(p, fmt, i == *sel - 1 ? 16 : ' ', items[i]);
        menu_printf_label(x, j, 1, p);
        p[maxLen] = 0;
        p += maxLen + 1;
        if (p > buf + 4000)
            Punt("Menu data too long");
    }
    input_capture_screen();
    if (!StillDown())
        down = 0;
    i = -1;
    for (;;) {
        if (down && !StillDown())
            goto done;
        if (StillDown() && !down)
            down = 1;
        if (input_event_count()) {
            input_pop_event(&ev);
            if ((char)(ev.code >> 8) == -2 && (ev.code & 0xff) != curMenu)
                goto other;
        }
        if (down) {
            GetMousePos(&pt);
            if (_fmemcmp(&pt, &last, 4) == 0)
                continue;
            last = pt;
            if (PointInRect(&pt, &r)) {
                i = (pt.y - r.top) / gfx_font_height_pixels;
                if (i >= 0 && i < nItems &&
                    items[i][1] != '-' && !(items[i][0] & 0x80))
                    goto moved;
            }
            i = -1;
        } else if (kbd_poll_bios_key()) {
            key = kbd_read_key_code();
            if (!(key & 0x800) && islower(key))
                key -= 0x20;
            i = cur;
            j = 0;
retry:
            switch (key) {
            case 10:
            case 13:
            case ' ':
            case 0x852:
            case 0x853:
                goto done;
            case 27:
                cur = -1;
                goto done;
            default:
                ;
                if (key & 0x800)
                    goto flush;
                j = t = cur;
                if (!isalpha(key))
                    goto restore;
                do {
                    if (++j >= nItems)
                        j = -1;
                    else {
                        c = items[j][1];
                        if (islower(c))
                            c -= 0x20;
                        if (c == key)
                            goto found;
                    }
                } while (t != j);
                goto restore;
            case '+':
            case 0x850:
                i = (i + 1) % nItems;
                goto check;
            case '-':
            case 0x848:
                i = (i > 0 ? i : nItems) - 1;
check:
                if (items[i][1] != '-' && !(items[i][0] & 0x80))
                    goto warp;
                if (j > 16) {
                    i = cur;
                    goto moved;
                }
                j++;
                goto retry;
restore:
                ;
            }
        }
moved:
        if (cur == i)
            continue;
        if (cur != -1) {
            menu_printf_label(x, gfx_font_height_pixels * cur + r.top, 1, buf + (maxLen + 1) * cur);
            cur = -1;
        }
        if (i == -1)
            continue;
        cur = i;
        menu_set_draw_colours(0);
        menu_printf_label(x, gfx_font_height_pixels * i + r.top, 0, buf + (maxLen + 1) * i);
    }
found:
    i = j;
warp:
    mouse_set_position(fontWidth * 4 + x, gfx_font_height_pixels / 2 + gfx_font_height_pixels * i + r.top);
    goto moved;
flush:
    kbd_unread_char(key & 0xff);
    kbd_unread_char(0);
escape:
    cur = -1;
done:
    if (!StillDown() && curMenu != -1) {
        if (cur != -1)
            input_enqueue_event_args((curMenu << 4) + cur - 0x2ff, 0, 0, 0);
        result = 1;
    }
    if (cur != -1)
        *sel = cur + 1;
    input_release_screen_capture();
    kbd_enable_mouse_emulation();
    gfx_restore_and_free_rect(&saveR, saveBuf);
    clip_active_list_offset = saved;
    free(buf);
    return result;
other:
    input_enqueue_event_args(ev.code, ev.xE, ev.h, ev.v, 0);
    goto done;
    }
    if (curMenu != -1)
        input_enqueue_event_args((curMenu - 0x30) << 4, 0, 0, 0);
    *sel = 0;
    return 1;
}



int far ui_step_button_focus(int key, int far *sel, int count, int base)
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
    hotbox_center_pointer(i + base);
    *sel = i;
    return 1;
}
