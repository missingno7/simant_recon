/*
 * Initializes DOS specific application resources and reads configuration words. It chooses
 * language and database resources and rejects invalid display mode settings.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 20 (S20); segment 39F1; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Og /Oe /Gs /Zi.
 */

struct Pt {
    int x;
    int y;
};

static char g_6108 = 0;         /* /! option: memory check override */
int g_610A = -1;
static int g_610C[9] = { 0x6d60, 0, 0x6d61, 0x6d62, 0x6d61, 0x6d62, 0, 0x6d62, 0x6d63 };

void far ReadConfig(void);
extern void far f_171C_0676();
extern char near g_432A;
extern char near gfx_display_mode;
extern char far * far startup_bad_switch_message;
extern int far printf(char far *fmt, ...);
extern void far exit(int code);
extern char far * far getenv(char far *name);
extern int far stricmp(char far *a, char far *b);
extern long far RallocMemoryFree(void);
extern long far startup_free_memory_bytes;
extern char far * far startup_low_memory_message;
extern void far f_277D_000D();
extern void far f_277D_000C(void);
extern char far * far getcwd(char far *buf, int size);
extern char far * far startup_working_directory;
extern int far startup_drive_letter;
extern int far strlen(char far *s);
extern int far open(char far *name, int mode, ...);
extern int far close(int fd);
extern int far db_SetDataBase(char far *name);
extern char far * far startup_config_strings;
extern void far gfx_select_driver_resources(char far *s);
extern int _fastcall win_SetPalette(int id);
extern void far gfx_set_border_colour(int color);
extern void far input_init_desktop_region(void);
extern int far f_208F_058B();
extern void far _harderr(int (far *handler)());
extern int near gfx_screen_width_pixels;
extern void far menu_set_state_colours(int a, int b, int c);
extern void far win_set_desktop_colours(int a, int b);
extern int far ConvColor(int color);
extern int near gfx_screen_height_pixels;
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);
extern void far gr_BitMapSize(struct Pt far *size, int id);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far mem_discard_soft_blocks(void);
extern void far mem_compact_any_region(void);
extern long far TickCount(void);
extern void far mouse_load_cursor_resources(int a);
extern int far menu_load_and_register(int a);
extern void far Punt(char far *fmt, ...);
extern void far SetMenuEntries(void);
extern void far LoadTiles(void);
extern void far InitApplicationStuff(void);
extern void far InitApplicationWindows(void);
extern int far WaitedEnough(long far *timer, int delay);
extern void far win_redraw_desktop_menu(void);

void far IBMInitStuff(int argc, char far * far *argv)
{
    int i;
    long v;
    struct Pt size;
    long t;

    g_610A = -1;
    ReadConfig();
    for (i = 1; i < argc; i++) {
        if (argv[i][0] != '/')
            continue;
        v = argv[i][2];
        switch (argv[i][1]) {
        case '!':
            g_6108 = v != '-';
            f_171C_0676(g_6108);
            break;
        case 'b':
            g_432A = 1;
            break;
        case 'd':
            switch (v) {
            case '2':
                gfx_display_mode = 6;
                break;
            case '?':
                gfx_display_mode = -1;
                break;
            case 'E':
                gfx_display_mode = 0;
                break;
            case 'H':
                gfx_display_mode = 3;
                break;
            case 'M':
                gfx_display_mode = 5;
                break;
            case 'T':
                gfx_display_mode = 2;
                break;
            case 'V':
                gfx_display_mode = 8;
                break;
            case 'e':
                gfx_display_mode = 4;
                break;
            case 'm':
                gfx_display_mode = 7;
                break;
            default:
                printf(startup_bad_switch_message);
                exit(4);
            }
            break;
        case 's':
            if (isdigit(v))
                g_610A = v - '0';
            break;
        }
    }
    if (getenv("BUG") && stricmp(getenv("BUG"), "MSMOUSE") == 0)
        g_432A = 1;
    startup_free_memory_bytes = RallocMemoryFree();
    if (!g_6108 && startup_free_memory_bytes < 0x1fbd0L) {
        printf(startup_low_memory_message);
        exit(1);
    }
    f_277D_000D(7);
    f_277D_000C();
    startup_working_directory = getcwd(0, 0);
    startup_drive_letter = *startup_working_directory;
    v = strlen(startup_working_directory) - 1;
    if (startup_working_directory[v] == '\\')
        startup_working_directory[v] = 0;
    if ((i = open("language.dat", 0)) > 0) {
        close(i);
        db_SetDataBase("language");
    }
    db_SetDataBase("shared");
    switch (gfx_display_mode) {
    case 2:
    case 4:
        db_SetDataBase("lrshare");
    }
    gfx_select_driver_resources(startup_config_strings);
    if (gfx_display_mode == 0)
        win_SetPalette(1);
    else if (gfx_display_mode == 8) {
        win_SetPalette(0);
        gfx_set_border_colour(15);
    }
    input_init_desktop_region();
    _harderr(f_208F_058B);
    if (gfx_screen_width_pixels == 320) {
        menu_set_state_colours(8, 11, 0);
        win_set_desktop_colours(0, 0);
    } else {
        menu_set_state_colours(7, 14, 12);
        win_set_desktop_colours(7, 7);
    }
    (*gfx_fill_rect_hook)(0, 0, gfx_screen_width_pixels, gfx_screen_height_pixels, ConvColor(15));
    i = g_610C[gfx_display_mode];
    gr_BitMapSize(&size, i);
    win_DrawBitMap((gfx_screen_width_pixels - size.x) / 2, (gfx_screen_height_pixels - size.y) / 2, i);
    mem_discard_soft_blocks();
    mem_compact_any_region();
    t = TickCount();
    mouse_load_cursor_resources(4);
    if (gfx_screen_width_pixels != 320 || !menu_load_and_register(1))
        if (!menu_load_and_register(0))
            Punt("Cannot load menu");
    SetMenuEntries();
    LoadTiles();
    InitApplicationStuff();
    InitApplicationWindows();
    SetMenuEntries();
    while (!WaitedEnough(&t, 0x48))
        ;
    win_redraw_desktop_menu();
}

extern int far read(int fd, char far *buf, unsigned n);

void far ReadWord(int fd, char far *buf)
{
    char c;

    while (read(fd, &c, 1) && isspace(c))
        ;
    do
        *buf++ = c;
    while (read(fd, &c, 1) && !isspace(c));
    *buf = 0;
}

void far SkipWords(int fd, int n)
{
    char buf[30];

    while (n--)
        ReadWord(fd, buf);
}

extern char far * far startup_config_path;
extern char far * far startup_missing_config_message;
extern int far puts(char far *s);

void far ReadConfig(void)
{
    char mode;
    char lang;
    int fd;
    char far *msg;

    if ((fd = open(startup_config_path, 0)) <= 0) {
        msg = startup_missing_config_message;
        goto fail;
    } else {
        SkipWords(fd, 2); read(fd, &mode, 1);
        SkipWords(fd, 2); read(fd, &lang, 1);
        close(fd);
        switch (mode) {
        case '?':
            gfx_display_mode = -1;
            break;
        case 'E':
            gfx_display_mode = 0;
            break;
        case 'H':
            gfx_display_mode = 3;
            break;
        case 'M':
            gfx_display_mode = 5;
            break;
        case 'T':
            gfx_display_mode = 2;
            break;
        case 'V':
            gfx_display_mode = 8;
            break;
        case 'e':
            gfx_display_mode = 4;
            break;
        case 'm':
            gfx_display_mode = 7;
            break;
        default:
            msg = "Bad 'Display Mode' in configuration file";
fail:
            puts(msg);
            exit(1);
        }
    }
    if (isdigit(lang))
        g_610A = lang - '0';
}
