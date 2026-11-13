/*
 * Provides menu bar and menu item state helpers. It also contains timers, mouse position and
 * button tracking functions used by the interface.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1FD2; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory. Some pairs are HIGH
 * confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

typedef struct {
    int x;
    int y;
} Point;

struct Timer {
    struct Rect r;
    void (far *fn)();
    int ticks;
    char a;
    char b;
    char c;
    char d;
};

struct MenuData {
    char far * far *titles;
    char far * far *items[16];
};

struct Event {
    int what;
    int message;
    int x4;
    char modLo;
    char modHi;
    int h;
    int v;
    int code;
    int xE;
};

extern void far input_enqueue_event_args();
extern void far mouse_default_cursor_thunk();

int desktop_fill_colour_a = 0x707;
int desktop_fill_colour_b = 0x707;
int menu_normal_background_colour = 0x101;
int menu_normal_text_colour = 0xb0b;
int menu_disabled_text_colour = 0xf0f;
struct Event near input_queue[7];
int g_5FF0 = 7;
struct Timer g_5FF2 = { { 0, 0, 0, 0xff }, 0, (int)(struct Event near *)input_queue, 5, 0, 10, 0 };
struct Timer g_6004 = { { 0, 0, 100, 100 }, input_enqueue_event_args, 1, 1, 1, 0, 10 };
struct Timer g_6016 = { { 0, 0, 100, 100 }, mouse_default_cursor_thunk, 1, 1, 1, 0, -1 };
struct Timer g_6028 = { { 0, 0, 100, 100 }, mouse_default_cursor_thunk, 1, 1, 1, 0, -1 };
struct Timer g_603A = { { 0, 0, 0x27f, 0x10 }, input_enqueue_event_args, 0, 0, 0, 0, 0x1f };
int g_604C = 0;
int g_604E = 0x100;
int g_6050 = 0;
int g_6052 = 0;
struct MenuData far *g_6054 = 0;

extern int far vsprintf(char far *buffer, char far *format, char far *args);
void far menu_set_draw_colours(int mode);
extern void far GPutStr(int x, int y, char far *text);

void far menu_printf_label(int x, int y, int color, char far *format, ...)
{
    char buf[32];

    vsprintf(buf, format, (char far *)(&format + 1));
    if (buf[0] & 0x80) {
        menu_set_draw_colours(color + 2);
        buf[0] &= 0x7f;
    } else {
        menu_set_draw_colours(color);
    }
    GPutStr(x, y, buf);
}

void far menu_enable(int id);
void far menu_disable(int id);

void far menu_set_enabled(int id, int on)
{
    if (on)
        menu_enable(id);
    else
        menu_disable(id);
}

void far f_1FD2_0077(int id)
{
    char far *p;

    if (!(id & 15))
        p = g_6054->titles[id >> 4];
    else
        p = g_6054->items[id >> 4][(id - 1) & 15];
    *p = (*p & 0x80) + 0x10;
}

void far f_1FD2_00D6(int id)
{
    char far *p;

    if (!(id & 15))
        p = g_6054->titles[id >> 4];
    else
        p = g_6054->items[id >> 4][(id - 1) & 15];
    *p = (*p & 0x80) + 0x20;
}

extern char far * far _fstrcpy(char far *dest, char far *src);

void far SetMenuOptionText(int id, char far *text)
{
    char far *p;

    if (!(id & 15))
        p = g_6054->titles[id >> 4];
    else
        p = g_6054->items[id >> 4][(id - 1) & 15];
    _fstrcpy(p, text);
}

extern int far menu_title_x_pixels[];

void far menu_enable(int id)
{
    char far *p;
    int menu;

    if (!(id & 15)) {
        menu = id >> 4;
        p = g_6054->titles[menu];
        *p &= 0x7f;
        menu_printf_label(menu_title_x_pixels[menu], 1, 1, p);
    } else {
        p = g_6054->items[id >> 4][(id - 1) & 15];
        *p &= 0x7f;
    }
}

void far menu_disable(int id)
{
    char far *p;
    int menu;

    if (!(id & 15)) {
        menu = id >> 4;
        p = g_6054->titles[menu];
        *p = (*p & 0x7f) + 0x80;
        menu_printf_label(menu_title_x_pixels[menu], 1, 1, p);
    } else {
        p = g_6054->items[id >> 4][(id - 1) & 15];
        *p = (*p & 0x7f) + 0x80;
    }
}

extern void (far * near gfx_set_attributes_hook)(int a, int b, int c);

void far menu_set_draw_colours(int mode)
{
    switch (mode) {
    case 0:
        gfx_set_attributes_hook(menu_normal_text_colour, menu_normal_background_colour, 0);
        break;
    case 1:
        gfx_set_attributes_hook(menu_normal_background_colour, menu_normal_text_colour, 0xc0);
        break;
    case 2:
        gfx_set_attributes_hook(menu_disabled_text_colour, menu_normal_background_colour, 0x30);
        break;
    case 3:
        gfx_set_attributes_hook(menu_disabled_text_colour, menu_normal_text_colour, 0x30);
        break;
    }
}

extern struct Rect far * far gfx_screen_rect(void);
void far input_prepend_cursor_region(struct Rect far *r, void (far *fn)(), int ticks);

void far input_capture_screen(void)
{
    input_prepend_cursor_region(gfx_screen_rect(), mouse_default_cursor_thunk, 100);
}

extern char far fd_5071_0728[];
extern void far hotbox_remove_id(int ticks, char far *slot);

void far input_release_screen_capture(void)
{
    hotbox_remove_id(100, fd_5071_0728);
}

extern void far hotbox_prepend(struct Timer far *t, char far *slot);

void far input_prepend_cursor_region(struct Rect far *r, void (far *fn)(), int ticks)
{
    g_6016.r.left = r->left;
    g_6016.r.top = r->top;
    g_6016.r.right = r->right;
    g_6016.r.bottom = r->bottom;
    g_6016.ticks = ticks;
    g_6016.fn = fn;
    hotbox_prepend(&g_6016, fd_5071_0728);
}

void far input_remove_cursor_region(int ticks)
{
    hotbox_remove_id(ticks, fd_5071_0728);
}

extern void far hotbox_append(struct Timer far *t, char far *slot);

void far input_append_cursor_region(struct Rect far *r, void (far *fn)(), int ticks)
{
    g_6016.r.left = r->left;
    g_6016.r.top = r->top;
    g_6016.r.right = r->right;
    g_6016.r.bottom = r->bottom;
    g_6016.ticks = ticks;
    g_6016.fn = fn;
    hotbox_remove_id(ticks, fd_5071_0728);
    hotbox_append(&g_6016, fd_5071_0728);
}

extern char far fd_5071_03C4[];

void far input_register_object_rect(struct Rect far *r, int ticks)
{
    g_6004.r.left = r->left;
    g_6004.r.top = r->top;
    g_6004.r.right = r->right;
    g_6004.r.bottom = r->bottom;
    g_6004.ticks = ticks;
    hotbox_remove_id(ticks, fd_5071_03C4);
    hotbox_prepend(&g_6004, fd_5071_03C4);
}

void far input_remove_object_rect(int ticks)
{
    hotbox_remove_id(ticks, fd_5071_03C4);
}

extern char far fd_5071_0060[];

void far input_register_proximity_rect(struct Rect far *r, int ticks)
{
    g_603A.r.left = r->left;
    g_603A.r.top = r->top;
    g_603A.r.right = r->right;
    g_603A.r.bottom = r->bottom;
    g_603A.ticks = ticks;
    hotbox_remove_id(ticks, fd_5071_0060);
    hotbox_prepend(&g_603A, fd_5071_0060);
}

void far input_remove_proximity_rect(int ticks)
{
    hotbox_remove_id(ticks, fd_5071_0060);
}

extern int far hotbox_get_rect(int id, char far *slot, struct Rect far *out);

int far input_get_object_hit_rect(int id, struct Rect far *out)
{
    return hotbox_get_rect(id, fd_5071_03C4, out);
}

extern int near mouse_x_pixels;
extern int near mouse_y_pixels;

void far GetMousePos(Point far *pt)
{
    pt->x = mouse_x_pixels;
    pt->y = mouse_y_pixels;
}

int far PointInRect(Point far *pt, struct Rect far *r)
{
    if (r->right > pt->x && r->left <= pt->x && r->top <= pt->y && pt->y < r->bottom)
        return 1;
    return 0;
}

extern void far hotbox_contains_pointer(int ticks, char far *slot);

void far input_probe_object_hit_rect(int ticks)
{
    hotbox_contains_pointer(ticks, fd_5071_03C4);
}

extern unsigned char near mouse_button_state;
extern int far kbd_scan_state(int key);

int far StillDown(void)
{
    int mods;

    mods = mouse_button_state & 3;
    if (kbd_scan_state(0x52) || kbd_scan_state(0x39))
        mods |= 1;
    if (kbd_scan_state(0x53))
        mods |= 2;
    return mods;
}

static long lastTick;
static int shiftHeld;
static int countdown;
extern unsigned long far TickCount(void);

void far ButtonHeldInit(void)
{
    lastTick = TickCount();
    countdown = 2;
    shiftHeld = 0;
}

int far ButtonHeld(void)
{
    if (countdown) {
        if (TickCount() != lastTick) {
            countdown--;
            lastTick = TickCount();
        }
    } else {
        if (shiftHeld || StillDown())
            shiftHeld = 1;
        else
            shiftHeld = 0;
        if (shiftHeld && !StillDown())
            return 0;
    }
    return 1;
}

extern void far win_FlushEvents(void);

void far ButtonHeldEnd(void)
{
    while (StillDown())
        ;
    win_FlushEvents();
}

extern void far GMixedFill(struct Rect far *r, int fore, int back);
int far menu_layout_bar(int draw);

void far win_redraw_desktop_menu(void)
{
    GMixedFill(gfx_screen_rect(), desktop_fill_colour_a, desktop_fill_colour_b);
    menu_layout_bar(1);
}

extern void far Punt(char far *format, ...);

void far SetMenuItemState(int id, char state)
{
    if (!g_6054)
        Punt("Attempt to SetMenuItemState with no menu loaded!");
    *g_6054->items[id >> 4][id & 15] = state;
}

extern void (far * near g_9130)(void);
extern struct Rect far menu_bar_rect;
extern char near gfx_font_height_pixels;
extern int near g_3DE4;
extern int near g_3DE2;
extern void far GRectFill(struct Rect far *rect, int color);
extern unsigned far _fstrlen(char far *s);
extern int far menu_title_char_counts[];
extern char near fontWidth;
extern int near gfx_screen_width_pixels;

int far menu_layout_bar(int draw)
{
    int i;
    int total;
    int x;
    char far * far *t;

    if (!g_6054)
        return 0;
    g_9130();
    menu_bar_rect = *gfx_screen_rect();
    menu_bar_rect.bottom = gfx_font_height_pixels + menu_bar_rect.top + 3;
    menu_set_draw_colours(1);
    if (draw)
        GRectFill(&menu_bar_rect, g_3DE2 | g_3DE4);
    i = 0;
    total = 0;
    for (t = g_6054->titles; *t; t++) {
        menu_title_char_counts[i] = _fstrlen(*t);
        total += menu_title_char_counts[i];
        i++;
    }
    g_604C = i;
    if (i > 1) {
        g_6050 = (gfx_screen_width_pixels / fontWidth - total) / (i - 1);
        if (g_6050 > 3)
            g_6050 = 3;
        else if (g_6050 < 1)
            g_6050 = 1;
        i = x = 0;
        for (t = g_6054->titles; *t; t++, i++) {
            menu_title_x_pixels[i] = x;
            if (draw)
                menu_printf_label(x, 1, 1, *t);
            x += (menu_title_char_counts[i] + g_6050) * fontWidth;
        }
    }
    return 1;
}

extern void far mouse_set_position(int x, int y);
extern int far menu_track_bar_selection(struct Event far *ev);

void far menu_open_by_index(int menu)
{
    struct Event ev;
    int x;

    x = fontWidth * 4 + menu_title_x_pixels[menu];
    ev.code = menu;
    ev.modHi = 0;
    mouse_set_position(x, 1);
    menu_track_bar_selection(&ev);
}

extern int far input_event_count(void);
extern void far input_pop_event(struct Event far *ev);

void far input_discard_queued_events(void)
{
    struct Event ev;

    while (input_event_count())
        input_pop_event(&ev);
}

extern int far kbd_poll_bios_key(void);
extern int far kbd_read_key_code(void);

int far kbd_poll_return_key(void)
{
    while (kbd_poll_bios_key())
        if (kbd_read_key_code() == 13)
            return 1;
    return 0;
}

extern int _fastcall win_GetEvent(struct Event far *ev);

int far win_wait_event_or_escape(struct Event far *ev)
{
    while (!win_GetEvent(ev))
        if (kbd_poll_bios_key() && kbd_read_key_code() == 0x1b)
            return 0;
    ButtonHeldEnd();
    return 1;
}

extern int far gr_BitMapSize(Point far *size, int object);

void far input_set_bitmap_hit_rect(int x, int y, int object, int ticks, int show)
{
    Point size;
    struct Rect r;

    if (show) {
        gr_BitMapSize(&size, object);
        r.left = x;
        r.right = x + size.x;
        r.top = y;
        r.bottom = y + size.y;
        input_register_object_rect(&r, ticks);
    } else {
        input_remove_object_rect(ticks);
    }
}
