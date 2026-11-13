/*
 * Provides window object text and bitmap helpers and resource loading. The file also includes
 * delays and display format sizing helpers.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 208F; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs.
 *
 * Built without /Zi: the cross-function relocation order forbids per-function record
 *    breaks (e.g. none between 0x0074 and 0x0245); /Zd is equally consistent.
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

int g_62BE = 0xa000;
int g_62C0 = 5;

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far GRectInv(struct Rect far *rect);

void far win_invert_obj_rect(int obj)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    GRectInv(&r);
}

extern char near fontWidth;
extern Point far gfx_text_pen_x;

void far win_set_obj_text_pen(int obj, int col)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    gfx_text_pen_x.x = fontWidth * col + r.left;
    gfx_text_pen_x.y = r.top;
}

extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far font_PrintStr(int x, int y, char far *text);

void far win_print_text_at_obj_offset(int obj, char far *text, int dx, int dy)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    win_SetColorFromObjNum(obj);
    font_PrintStr(r.left + dx, r.top + dy, text);
}

extern int far font_StringWidth(char far *text);
extern int far font_FontHeight(void);

void far gr_CenterStrInRect(struct Rect far *rect, char far *text)
{
    struct Rect r;
    int w;
    int x;

    r = *rect;
    w = font_StringWidth(text);
    x = (r.right - w + r.left) / 2;
    if (x < r.left)
        x = r.left;
    r.left = x;
    r.right = x + w;
    r.top += (r.bottom - font_FontHeight() - r.top) / 2;
    r.bottom = font_FontHeight() + r.top;
    font_PrintStr(r.left, r.top, text);
}

extern int near g_3DE2;
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);

void far gr_CenterStrInRectClear(struct Rect far *rect, char far *text)
{
    struct Rect r;
    int w;
    int x;

    r = *rect;
    w = font_StringWidth(text);
    x = (r.right - w + r.left) / 2;
    if (x < r.left)
        x = r.left;
    r.left = x;
    r.right = x + w;
    r.top += (r.bottom - font_FontHeight() - r.top) / 2;
    r.bottom = font_FontHeight() + r.top;
    font_PrintStr(r.left, r.top, text);
    if (rect->left < r.left)
        gfx_fill_rect_hook(rect->left, r.top, r.left, r.bottom, g_3DE2);
    if (rect->right > r.right)
        gfx_fill_rect_hook(r.right, r.top, rect->right, r.bottom, g_3DE2);
}

void far win_center_text_unclipped(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    gr_CenterStrInRect(&r, text);
}

void far win_print_obj_text(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    font_PrintStr(r.left, r.top, text);
}

extern void (far * near gfx_set_attributes_hook)(int a, int b, int c);
extern void far GRectOutline(struct Rect far *rect, int width);

void far win_outline_obj_rect(int obj, int color, int width)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    gfx_set_attributes_hook(color, color, color);
    GRectOutline(&r, width);
}

extern unsigned char near gfx_display_mode;
extern void (far * near g_917C)(int x, int y, int offset);
extern char far * far * far ui_icon_bitmap_handle;
extern void (far * near gfx_put_picture_hook)(int x, int y, char far *p, int w, int h);

void far gfx_draw_tile_at_obj(int obj, int n)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    if (!(gfx_display_mode & 1)) {
        if (gfx_display_mode & 2)
            gfx_put_picture_hook(r.left, r.top, *ui_icon_bitmap_handle + (n << 5), 8, 8);
        else
            g_917C(r.left, r.top, (n << g_62C0) + g_62BE);
    } else
        gfx_put_picture_hook(r.left, r.top, *ui_icon_bitmap_handle + (n << 5), 16, 16);
}

/* Two separate mode tests with identical calls: the 8x8 call of mode 6 is laid out inline
   and cross-jumped into the 16x16 tail; `==6 || ==2` places the shared block last. */
void far gfx_draw_tile_at(int x, int y, int n)
{
    if (!(gfx_display_mode & 1)) {
        if (gfx_display_mode == 6)
            gfx_put_picture_hook(x, y, *ui_icon_bitmap_handle + (n << 5), 8, 8);
        else if (gfx_display_mode == 2)
            gfx_put_picture_hook(x, y, *ui_icon_bitmap_handle + (n << 5), 8, 8);
        else
            g_917C(x, y, (n << g_62C0) + g_62BE);
    } else
        gfx_put_picture_hook(x, y, *ui_icon_bitmap_handle + (n << 5), 16, 16);
}

extern char far * far db_LoadObject(int object, int kind);
extern void far Punt(char far *format, ...);

char far * far res_load_required_object(int kind, int object)
{
    char far *p;

    p = db_LoadObject(object, kind);
    if (p == 0)
        Punt("\aCouldn't load resource %x,%x", object, kind);
    return p;
}

extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern void far font_print_at_pen(char far *text);

void far font_printf_at_pen(char far *format, ...)
{
    char buf[100];

    vsprintf(buf, format, (char far *)(&format + 1));
    font_print_at_pen(buf);
}

void far win_printf_obj_text(int obj, char far *format, ...)
{
    struct Rect r;
    char buf[100];

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    vsprintf(buf, format, (char far *)(&format + 1));
    font_PrintStr(r.left, r.top, buf);
}

void far f_208F_0403(void)
{
}

void far f_208F_0404(void)
{
}

extern void far db_PurgeHandle(char far *handle);

void far res_purge_handle(char far *handle)
{
    db_PurgeHandle(handle);
}

extern char far * far mem_Lock(char far *h);
extern void far UnpackInit(char far *packed, int length);
extern unsigned int far Unpack(char far *dest, unsigned int length);
extern void far mem_Unlock(char far *h);
extern void far db_ReleaseObject(unsigned int object, int kind);

int far gr_BitMapSize(Point far *size, int object)
{
    char far *h;
    int far *p;
    int hdr[6];

    h = db_LoadObject(object, 2);
    if (h == 0) {
        size->x = size->y = 1;
        return 0;
    }
    p = (int far *)mem_Lock(h);
    if (p[0] == -1) {
        UnpackInit((char far *)(p + 2), p[1]);
        Unpack((char far *)hdr, 12);
        size->x = hdr[4];
        size->y = hdr[5];
    } else {
        size->x = p[4];
        size->y = p[5];
    }
    mem_Unlock(h);
    db_ReleaseObject(object, 2);
    return 1;
}

static long g_8CE8;
extern int far dialog_wait_delay;
extern unsigned long far TickCount(void);

void far ui_start_dismiss_timer(int delay)
{
    g_8CE8 = TickCount();
    dialog_wait_delay = delay;
}

extern int far kbd_poll_bios_key(void);
extern int far kbd_read_key_code(void);
extern int far WaitedEnough(long far *timer, int delay);

int far ui_poll_dismiss_timer(void)
{
    int key;

    if ((key = kbd_poll_bios_key()) != 0) {
        key = kbd_read_key_code();
        if (key != 13 && key != 27)
            key = 0;
    }
    return WaitedEnough(&g_8CE8, dialog_wait_delay) || key;
}

extern int far fd_1B73_0006;

void far timer_wait_countdown(int ticks)
{
    fd_1B73_0006 = ticks;
    while (fd_1B73_0006 != 0)
        ;
}

void far timer_start_countdown(int ticks)
{
    fd_1B73_0006 = ticks;
}

int far timer_countdown_done(void)
{
    return !fd_1B73_0006;
}

int far kbd_poll_escape_key(void)
{
    while (kbd_poll_bios_key())
        if (kbd_read_key_code() == 0x1b)
            return 1;
    return 0;
}

int far f_208F_058B(void)
{
    return 3;
}
