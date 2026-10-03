#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect g_5A9C;
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Root module 205F: graphics adapter detection and display driver selection. */
char g_6232[9] = { 4, 1, 4, 1, 4, 1, 8, 1, 4 };
char *g_623C[9] = {
    "Hires EGA", "CGA", "Tandy", "Hercules", "Lores EGA", "Mono EGA",
    "MCGA/VGA Color", "MCGA/VGA mono", "VGA Color"
};
int16_t g_6260 = 0;
int16_t fd_55B3_6262 = 0;
int32_t g_6264[13] = {
    0x222e0L, 0x9c40L, 0xea60L, 0xea60L, 0xea60L, 0xea60L, 0x2e630L, 0xea60L,
    0L, 0L, 0x3a98L, 0x7530L, 0x7530L
};
int16_t g_6298 = 0;
char *g_629A[9] = {
    "hcega", "mono", "tdyga", "mono", "lcega", "mono", "l256", "mono", "hcega"
};

extern void  f_1B4E_0025(void);
extern int16_t  o21_39C7_0000(void);
extern int16_t  o21_39C7_016D(void);
extern void  exit(int16_t code);
extern void  db_SetDataBase(char  *name);
extern void  f_1B28_0006(void);
extern void  Punt(char  *message);
extern void  o00_31AD_2AB4(void);
extern void  o01_3126_0000(void);
extern void  o20_39C7_0160(void);
extern void  o20_39C7_0003(void);
extern void  o03_3126_0140(void);
extern void  o20_39C7_0069(void);
extern void  o20_39C7_0001(void);
extern void  o01_3126_010A(void);
extern void  o20_39C7_0008(void);
extern void  o20_39C7_0000(void);
extern void  o00_31AD_1AE7(void);
extern void  o20_39C7_01C1(void);
extern void  o20_39C7_0004(void);
extern void  o01_3126_007D(void);
extern void  o02_3126_0000(void);
extern void  o20_39C7_0212(void);
extern void  o20_39C7_0006(void);
extern void  o01_3126_0068(void);
extern void  o20_39C7_00FF(void);
extern void  o20_39C7_0002(void);
extern void  o00_31AD_2AE5(void);
extern void  o20_39C7_0211(void);
extern void  o20_39C7_0005(void);
extern void ( *  g_9130)(void);
extern void  o01_32B5_000E(void);
extern void ( *  fd_50F6_37EE)();
extern void  o01_32B5_0152();
extern void ( *  fd_50F6_37EA)();
extern void  o01_32B5_000F();
extern void ( *  fd_50F6_3B58)();
extern void  o01_32B5_00AA();
extern void ( *  fd_50F6_37E6)();
extern void  o01_32B5_024F();
extern void  o03_3258_040C(void);
extern void  o03_3258_05A7();
extern void  o03_3258_040D();
extern void  o03_3258_04CE();
extern void  o03_3258_175F();
extern void  o00_35A6_0006(void);
extern void  o00_35A6_02FD();
extern void  o00_35A6_0007();
extern void  o00_35A6_0177();
extern void  o00_35A6_0406();

void  f_205F_0004(char  *dbname)
{
    char path[100];
    char  *msg;
    int16_t mode;
    int16_t adapter;
    int16_t display;
    int16_t info;

    f_1B4E_0025();
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
            dos_printf(msg);
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
    dos_sprintf(path, "%s%s", g_629A[g_5A97], dbname);
    db_SetDataBase(path);
    f_1B28_0006();
    switch (g_5A97) {
    case 0:
        o00_31AD_2AB4();
        o20_39C7_0211();
        o20_39C7_0005();
        break;
    case 1:
        if (g_6298) {
            o01_3126_0000();
            g_5A97 = 5;
        }
        o20_39C7_0160();
        o20_39C7_0003();
        break;
    case 2:
        o03_3126_0140();
        o20_39C7_0069();
        o20_39C7_0001();
        break;
    case 3:
        o01_3126_010A();
        o20_39C7_0008();
        o20_39C7_0000();
        break;
    case 4:
        o00_31AD_1AE7();
        o20_39C7_01C1();
        o20_39C7_0004();
        break;
    case 5:
        o01_3126_007D();
        o20_39C7_0160();
        o20_39C7_0003();
        break;
    case 6:
        o02_3126_0000();
        o20_39C7_0212();
        o20_39C7_0006();
        break;
    case 7:
        o01_3126_0068();
        o20_39C7_00FF();
        o20_39C7_0002();
        break;
    case 8:
        o00_31AD_2AE5();
        o20_39C7_0211();
        o20_39C7_0005();
        break;
    default:
        Punt("Illegal graphics mode for this version of SimCity");
        break;
    }
    (*g_9130)();
    g_5A9C.right = SIM_GRAPHICS_SOURCE_g_3DB2;
    g_5A9C.bottom = SIM_GRAPHICS_SOURCE_g_3DB4;
    fd_55B3_6262 = 1;
    if (g_5A97 & 1) {
        o01_32B5_000E();
        fd_50F6_37EE = o01_32B5_0152;
        fd_50F6_37EA = o01_32B5_000F;
        fd_50F6_3B58 = o01_32B5_00AA;
        fd_50F6_37E6 = o01_32B5_024F;
    } else if (g_5A97 == 2) {
        o03_3258_040C();
        fd_50F6_37EE = o03_3258_05A7;
        fd_50F6_37EA = o03_3258_040D;
        fd_50F6_3B58 = o03_3258_04CE;
        fd_50F6_37E6 = o03_3258_175F;
    } else {
        o00_35A6_0006();
        fd_50F6_37EE = o00_35A6_02FD;
        fd_50F6_37EA = o00_35A6_0007;
        fd_50F6_3B58 = o00_35A6_0177;
        fd_50F6_37E6 = o00_35A6_0406;
    }
}

#pragma pack(pop)
