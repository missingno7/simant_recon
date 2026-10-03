#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include <ctype.h>
#pragma pack(push, 2)
#include "portable/whole_program/platform/graphics_source_fields.h"
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

#include "portable/whole_program/state/source_tables.h"
/* Overlay section S20, code frame 39F1: IBM start-up (Win16 GR_MODULE IBMInitStuff..ReadConfig). */

struct Pt {
    int16_t x;
    int16_t y;
};

static char g_6108 = 0;         /* /! option: memory check override */
static int16_t g_610A = -1;
static int16_t g_610C[9] = { 0x6d60, 0, 0x6d61, 0x6d62, 0x6d61, 0x6d62, 0, 0x6d62, 0x6d63 };

void  ReadConfig(void);
extern void  f_171C_0676();
extern char  g_432A;
extern char  g_5A97;
extern void  exit(int16_t code);
extern char  *  getenv(char  *name);

extern int32_t  f_171C_1750(void);
extern int32_t  fd_50F6_3944;
extern void  f_277D_000D();
extern void  f_277D_000C(void);

extern char  *  fd_50F6_38B2;
extern int16_t  fd_50F6_38B6;
extern int16_t  strlen(char  *s);


extern int16_t  db_SetDataBase(char  *name);
extern void  f_205F_0004(char  *s);
extern int16_t  win_SetPalette(int16_t id);
extern void  o17_384C_0000(void);
extern int16_t  f_208F_058B();
extern void  _harderr(int16_t ( *handler)());
extern void  o17_384C_0143(int16_t a, int16_t b, int16_t c);
extern void  o17_384C_0169(int16_t a, int16_t b);
extern void  f_208F_0419(struct Pt  *size, int16_t id);
extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);
extern void  f_171C_1EFA(void);
extern void  f_171C_0EDE(void);
extern int32_t  TickCount(void);
extern void  f_1B28_0129(int16_t a);
extern int16_t  o17_384C_0039(int16_t a);
extern void  Punt(char  *fmt, ...);
extern void  SetMenuEntries(void);
extern void  LoadTiles(void);
extern void  f_00BA_01B6(void);
extern void  f_00BA_0002(void);
extern int16_t  WaitedEnough(int32_t  *timer, int16_t delay);
extern void  f_1FD2_05FD(void);

void  IBMInitStuff(int16_t argc, char  *  *argv)
{
    int16_t i;
    int32_t v;
    struct Pt size;
    int32_t t;

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
                g_5A97 = 6;
                break;
            case '?':
                g_5A97 = -1;
                break;
            case 'E':
                g_5A97 = 0;
                break;
            case 'H':
                g_5A97 = 3;
                break;
            case 'M':
                g_5A97 = 5;
                break;
            case 'T':
                g_5A97 = 2;
                break;
            case 'V':
                g_5A97 = 8;
                break;
            case 'e':
                g_5A97 = 4;
                break;
            case 'm':
                g_5A97 = 7;
                break;
            default:
                dos_printf(fd_55B3_1CD4[2]);
                exit(4);
            }
            break;
        case 's':
            if (isdigit(v))
                g_610A = v - '0';
            break;
        }
    }
    if (getenv("BUG") && dos_stricmp(getenv("BUG"), "MSMOUSE") == 0)
        g_432A = 1;
    fd_50F6_3944 = f_171C_1750();
    if (!g_6108 && fd_50F6_3944 < 0x1fbd0L) {
        dos_printf(fd_55B3_1CD4[1]);
        exit(1);
    }
    f_277D_000D(7);
    f_277D_000C();
    fd_50F6_38B2 = dos_getcwd(0, 0);
    fd_50F6_38B6 = *fd_50F6_38B2;
    v = strlen(fd_50F6_38B2) - 1;
    if (fd_50F6_38B2[v] == '\\')
        fd_50F6_38B2[v] = 0;
    if ((i = dos_open("language.dat", 0)) > 0) {
        dos_close(i);
        db_SetDataBase("language");
    }
    db_SetDataBase("shared");
    switch (g_5A97) {
    case 2:
    case 4:
        db_SetDataBase("lrshare");
    }
    f_205F_0004(fd_55B3_1CD4[0]);
    if (g_5A97 == 0)
        win_SetPalette(1);
    else if (g_5A97 == 8) {
        win_SetPalette(0);
        f_1B4E_0228(15);
    }
    o17_384C_0000();
    _harderr(f_208F_058B);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 320) {
        o17_384C_0143(8, 11, 0);
        o17_384C_0169(0, 0);
    } else {
        o17_384C_0143(7, 14, 12);
        o17_384C_0169(7, 7);
    }
    (*g_9134)(0, 0, SIM_GRAPHICS_SOURCE_g_3DB2, SIM_GRAPHICS_SOURCE_g_3DB4, f_1B4E_000D(15));
    i = g_610C[g_5A97];
    f_208F_0419(&size, i);
    win_DrawBitMap((SIM_GRAPHICS_SOURCE_g_3DB2 - size.x) / 2, (SIM_GRAPHICS_SOURCE_g_3DB4 - size.y) / 2, i);
    f_171C_1EFA();
    f_171C_0EDE();
    t = TickCount();
    f_1B28_0129(4);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 != 320 || !o17_384C_0039(1))
        if (!o17_384C_0039(0))
            Punt("Cannot load menu");
    SetMenuEntries();
    LoadTiles();
    f_00BA_01B6();
    f_00BA_0002();
    SetMenuEntries();
    while (!WaitedEnough(&t, 0x48))
        ;
    f_1FD2_05FD();
}


void  ReadWord(int16_t fd, char  *buf)
{
    char c;

    while (dos_read(fd, &c, 1) && isspace(c))
        ;
    do
        *buf++ = c;
    while (dos_read(fd, &c, 1) && !isspace(c));
    *buf = 0;
}

void  SkipWords(int16_t fd, int16_t n)
{
    char buf[30];

    while (n--)
        ReadWord(fd, buf);
}

extern char  *  fd_55B3_1CE4;
extern char  *  fd_55B3_1CE0;
extern int16_t  puts(char  *s);

void  ReadConfig(void)
{
    char mode;
    char lang;
    int16_t fd;
    char  *msg;

    if ((fd = dos_open(fd_55B3_1CE4, 0)) <= 0) {
        msg = fd_55B3_1CE0;
        goto fail;
    } else {
        SkipWords(fd, 2); dos_read(fd, &mode, 1);
        SkipWords(fd, 2); dos_read(fd, &lang, 1);
        dos_close(fd);
        switch (mode) {
        case '?':
            g_5A97 = -1;
            break;
        case 'E':
            g_5A97 = 0;
            break;
        case 'H':
            g_5A97 = 3;
            break;
        case 'M':
            g_5A97 = 5;
            break;
        case 'T':
            g_5A97 = 2;
            break;
        case 'V':
            g_5A97 = 8;
            break;
        case 'e':
            g_5A97 = 4;
            break;
        case 'm':
            g_5A97 = 7;
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

#pragma pack(pop)
