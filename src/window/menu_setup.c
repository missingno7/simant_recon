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
extern struct Rect far gfx_screen_clip_list;
extern void far input_register_object_rect(struct Rect far *r, int ticks);

void far input_init_desktop_region(void)
{
    mouse_select_cursor_shape(0);
    mouse_initialize_driver();
    input_install_hooks();
    hotbox_initialize_dispatch();
    mouse_set_mickey_ratio(0x10, 0x10);
    input_register_object_rect(&gfx_screen_clip_list, 0xff00);
}

extern long far * far * far db_LoadObject(int object, int kind);
extern long far * far menu_resource_tables;
extern void far db_UnhookObject(int object, int kind);
extern int far menu_layout_bar(int draw);
extern int far menu_title_char_counts[];
extern int far menu_title_x_pixels[];
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
    menu_resource_tables = *h;
    db_UnhookObject(id, 6);
    draw = 0;
    for (p = menu_resource_tables; *p; p++) {
        *p += (long)menu_resource_tables;
        for (q = *(long far * far *)p; *q; q++)
            *q += (long)menu_resource_tables;
    }
    menu_layout_bar(draw);
    for (i = 0, r = (long far *)*menu_resource_tables; *r; i++, r++)
        menu_register_title_hit_rect(menu_title_x_pixels[i], menu_title_char_counts[i], i - 0x200);
    return 1;
}

extern int far menu_normal_background_colour;
extern int far menu_normal_text_colour;
extern int far menu_disabled_text_colour;

void far menu_set_state_colours(int a, int b, int c)
{
    menu_normal_background_colour = a;
    menu_normal_text_colour = b;
    menu_disabled_text_colour = c;
}

extern int far desktop_fill_colour_a;
extern int far desktop_fill_colour_b;

void far win_set_desktop_colours(int a, int b)
{
    desktop_fill_colour_a = a;
    desktop_fill_colour_b = b;
}

extern char near gfx_font_height_pixels;
extern char near fontWidth;

void far menu_register_title_hit_rect(int x, int len, int id)
{
    struct Rect r;

    r.top = 1;
    r.bottom = gfx_font_height_pixels + 1;
    r.left = x;
    r.right = fontWidth * len + x;
    input_register_object_rect(&r, id);
}
