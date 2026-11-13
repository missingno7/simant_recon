/*
 * Initializes menu bar data and fixes up its pointers. It calculates item rectangles and applies
 * menu colours before drawing.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 17 (S17); segment 384C; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern void far mouse_select_cursor_shape(int a);
extern void far mouse_initialize_driver(void);
extern void far input_install_hooks(void);
extern void far hotbox_initialize_dispatch(void);
extern void far mouse_set_mickey_ratio(int a, int b);
extern struct Rect far g_5A9C;
extern void far input_register_object_rect(struct Rect far *r, int ticks);

void far input_init_desktop_region(void)
{
    mouse_select_cursor_shape(0);
    mouse_initialize_driver();
    input_install_hooks();
    hotbox_initialize_dispatch();
    mouse_set_mickey_ratio(0x10, 0x10);
    input_register_object_rect(&g_5A9C, 0xff00);
}

extern long far * far * far db_LoadObject(int object, int kind);
extern long far * far fd_55B3_6054;
extern void far db_UnhookObject(int object, int kind);
extern int far menu_layout_bar(int draw);
extern int far fd_50F6_46BC[];
extern int far fd_50F6_46A8[];
void far menu_register_title_hit_rect(int x, int len, int id);

/* LIFE-2: draw is a real later call argument. Initializing it before the
 * pointer-fixup loops reproduces the frame and spill homes. Its spelling and
 * original width are unknown; int, unsigned and unsigned char controls match. */
int far menu_load_and_register(int id)
{
    long far * far *h;
    long far *p;
    long far *q;
    long far *r;
    int i;
    int draw;

    h = db_LoadObject(id, 6);
    if (h == 0L)
        return 0;
    fd_55B3_6054 = *h;
    db_UnhookObject(id, 6);
    draw = 0;
    for (p = fd_55B3_6054; *p; p++) {
        *p += (long)fd_55B3_6054;
        for (q = *(long far * far *)p; *q; q++)
            *q += (long)fd_55B3_6054;
    }
    menu_layout_bar(draw);
    for (i = 0, r = (long far *)*fd_55B3_6054; *r; i++, r++)
        menu_register_title_hit_rect(fd_50F6_46A8[i], fd_50F6_46BC[i], i - 0x200);
    return 1;
}

extern int far g_5FEA;
extern int far g_5FEC;
extern int far g_5FEE;

void far menu_set_state_colours(int a, int b, int c)
{
    g_5FEA = a;
    g_5FEC = b;
    g_5FEE = c;
}

extern int far g_5FE6;
extern int far g_5FE8;

void far win_set_desktop_colours(int a, int b)
{
    g_5FE6 = a;
    g_5FE8 = b;
}

extern char near g_3DDC;
extern char near fontWidth;

void far menu_register_title_hit_rect(int x, int len, int id)
{
    struct Rect r;

    r.top = 1;
    r.bottom = g_3DDC + 1;
    r.left = x;
    r.right = fontWidth * len + x;
    input_register_object_rect(&r, id);
}
