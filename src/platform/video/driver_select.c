/*
 * Identifies the graphics adapter and selects its display and resource drivers. It installs the
 * screen and sprite callback tables for the chosen mode.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 205F; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

char g_6232[9] = { 4, 1, 4, 1, 4, 1, 8, 1, 4 };
char *g_623C[9] = {
    "Hires EGA", "CGA", "Tandy", "Hercules", "Lores EGA", "Mono EGA",
    "MCGA/VGA Color", "MCGA/VGA mono", "VGA Color"
};
int g_6260 = 0;
int fd_55B3_6262 = 0;
long g_6264[13] = {
    0x222e0L, 0x9c40L, 0xea60L, 0xea60L, 0xea60L, 0xea60L, 0x2e630L, 0xea60L,
    0L, 0L, 0x3a98L, 0x7530L, 0x7530L
};
int g_6298 = 0;
char *g_629A[9] = {
    "hcega", "mono", "tdyga", "mono", "lcega", "mono", "l256", "mono", "hcega"
};

extern void far gfx_reset_driver_callbacks(void);
extern int far o21_39C7_0000(void);
extern int far o21_39C7_016D(void);
extern char near g_5A97;
extern int far printf(char far *format, ...);
extern void far exit(int code);
extern int far sprintf(char far *buf, char far *format, ...);
extern void far db_SetDataBase(char far *name);
extern void far f_1B28_0006(void);
extern void far Punt(char far *message);
extern void far gfx_planar_init_640x350(void);
extern void far gfx_mono_init_banked_640x400(void);
extern void far o20_39C7_0160(void);
extern void far o20_39C7_0003(void);
extern void far gfx_tandy_init_tandy(void);
extern void far o20_39C7_0069(void);
extern void far o20_39C7_0001(void);
extern void far gfx_mono_init_hercules(void);
extern void far o20_39C7_0008(void);
extern void far o20_39C7_0000(void);
extern void far gfx_planar_init_320x200(void);
extern void far o20_39C7_01C1(void);
extern void far o20_39C7_0004(void);
extern void far gfx_mono_init_ega350_mono(void);
extern void far gfx_vga8_init_vga256(void);
extern void far o20_39C7_0212(void);
extern void far o20_39C7_0006(void);
extern void far gfx_mono_init_ega480_mono(void);
extern void far o20_39C7_00FF(void);
extern void far o20_39C7_0002(void);
extern void far gfx_planar_init_640x480(void);
extern void far o20_39C7_0211(void);
extern void far o20_39C7_0005(void);
extern void (far * near g_9130)(void);
extern int near g_3DB2;
extern struct Rect far g_5A9C;
extern int near g_3DB4;
extern void far gfx_mono_buffer_noop(void);
extern void (far * far fd_50F6_37EE)();
extern void far gfx_mono_buffer_intersection();
extern void (far * far fd_50F6_37EA)();
extern void far gfx_mono_mask_bitmap_to_buffer();
extern void (far * far fd_50F6_3B58)();
extern void far gfx_mono_copy_bitmap_to_buffer();
extern void (far * far fd_50F6_37E6)();
extern void far gfx_mono_scratch_to_buffer();
extern void far gfx_tandy_buffer_noop(void);
extern void far gfx_tandy_buffer_intersection();
extern void far gfx_tandy_mask_to_buffer();
extern void far gfx_tandy_copy_to_buffer();
extern void far gfx_tandy_scratch_to_buffer();
extern void far gfx_planar_buffer_noop(void);
extern void far gfx_planar_buffer_intersection();
extern void far gfx_planar_mask_to_buffer();
extern void far gfx_planar_copy_to_buffer();
extern void far gfx_planar_scratch_to_buffer();

void far gfx_select_driver_resources(char far *dbname)
{
    char path[100];
    char far *msg;
    int mode;
    int adapter;
    int display;
    int info;

    gfx_reset_driver_callbacks();
    info = o21_39C7_0000();
    display = (char)(info >> 8);
    adapter = info & 0xff;
    mode = -1;
    if (adapter & 0x80) {
        mode = 3;
    } else {
        switch (adapter) {
        case 1:
            msg = "MDA system detected. Cannot run graphics.";
            break;
        case 2:
            mode = o21_39C7_016D() ? 2 : 1;
            break;
        case 4:
            mode = 7;
            break;
        case 5:
            if (display == 3 || display == 5) {
                mode = 8;
                break;
            }
        case 3:
            switch (display) {
            case 1:
            case 4:
                mode = 5;
                break;
            case 2:
                mode = 1;
                break;
            case 3:
            case 5:
                mode = 0;
                break;
            }
            break;
        }
    }
    if (g_5A97 == -1) {
        if (mode == -1) {
            printf(msg);
            exit(4);
        }
        g_5A97 = mode;
    }
    if (g_6298) {
        switch (g_5A97) {
        case 0:
            g_5A97 = 5;
            break;
        case 1:
            g_5A97 = 1;
            break;
        case 6:
        case 8:
            g_5A97 = 7;
            break;
        }
    }
    sprintf(path, "%s%s", g_629A[g_5A97], dbname);
    db_SetDataBase(path);
    f_1B28_0006();
    switch (g_5A97) {
    case 0:
        gfx_planar_init_640x350();
        o20_39C7_0211();
        o20_39C7_0005();
        break;
    case 1:
        if (g_6298) {
            gfx_mono_init_banked_640x400();
            g_5A97 = 5;
        }
        o20_39C7_0160();
        o20_39C7_0003();
        break;
    case 2:
        gfx_tandy_init_tandy();
        o20_39C7_0069();
        o20_39C7_0001();
        break;
    case 3:
        gfx_mono_init_hercules();
        o20_39C7_0008();
        o20_39C7_0000();
        break;
    case 4:
        gfx_planar_init_320x200();
        o20_39C7_01C1();
        o20_39C7_0004();
        break;
    case 5:
        gfx_mono_init_ega350_mono();
        o20_39C7_0160();
        o20_39C7_0003();
        break;
    case 6:
        gfx_vga8_init_vga256();
        o20_39C7_0212();
        o20_39C7_0006();
        break;
    case 7:
        gfx_mono_init_ega480_mono();
        o20_39C7_00FF();
        o20_39C7_0002();
        break;
    case 8:
        gfx_planar_init_640x480();
        o20_39C7_0211();
        o20_39C7_0005();
        break;
    default:
        Punt("Illegal graphics mode for this version of SimCity");
        break;
    }
    (*g_9130)();
    g_5A9C.right = g_3DB2;
    g_5A9C.bottom = g_3DB4;
    fd_55B3_6262 = 1;
    if (g_5A97 & 1) {
        gfx_mono_buffer_noop();
        fd_50F6_37EE = gfx_mono_buffer_intersection;
        fd_50F6_37EA = gfx_mono_mask_bitmap_to_buffer;
        fd_50F6_3B58 = gfx_mono_copy_bitmap_to_buffer;
        fd_50F6_37E6 = gfx_mono_scratch_to_buffer;
    } else if (g_5A97 == 2) {
        gfx_tandy_buffer_noop();
        fd_50F6_37EE = gfx_tandy_buffer_intersection;
        fd_50F6_37EA = gfx_tandy_mask_to_buffer;
        fd_50F6_3B58 = gfx_tandy_copy_to_buffer;
        fd_50F6_37E6 = gfx_tandy_scratch_to_buffer;
    } else {
        gfx_planar_buffer_noop();
        fd_50F6_37EE = gfx_planar_buffer_intersection;
        fd_50F6_37EA = gfx_planar_mask_to_buffer;
        fd_50F6_3B58 = gfx_planar_copy_to_buffer;
        fd_50F6_37E6 = gfx_planar_scratch_to_buffer;
    }
}
