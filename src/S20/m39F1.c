/* Overlay section S20, code frame 39F1: IBM start-up (Win16 GR_MODULE IBMInitStuff..ReadConfig). */

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
extern char near g_5A97;
extern char far * far fd_55B3_1CDC;
extern int far printf(char far *fmt, ...);
extern void far exit(int code);
extern char far * far getenv(char far *name);
extern int far stricmp(char far *a, char far *b);
extern long far f_171C_1750(void);
extern long far fd_50F6_3944;
extern char far * far fd_55B3_1CD8;
extern void far f_277D_000D();
extern void far f_277D_000C(void);
extern char far * far getcwd(char far *buf, int size);
extern char far * far fd_50F6_38B2;
extern int far fd_50F6_38B6;
extern int far strlen(char far *s);
extern int far open(char far *name, int mode, ...);
extern int far close(int fd);
extern int far db_SetDataBase(char far *name);
extern char far * far fd_55B3_1CD4;
extern void far f_205F_0004(char far *s);
extern int _fastcall win_SetPalette(int id);
extern void far f_1B4E_0228(int color);
extern void far o17_384C_0000(void);
extern int far f_208F_058B();
extern void far _harderr(int (far *handler)());
extern int near g_3DB2;
extern void far o17_384C_0143(int a, int b, int c);
extern void far o17_384C_0169(int a, int b);
extern int far f_1B4E_000D(int color);
extern int near g_3DB4;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);
extern void far f_208F_0419(struct Pt far *size, int id);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far f_171C_1EFA(void);
extern void far f_171C_0EDE(void);
extern long far TickCount(void);
extern void far f_1B28_0129(int a);
extern int far o17_384C_0039(int a);
extern void far Punt(char far *fmt, ...);
extern void far SetMenuEntries(void);
extern void far LoadTiles(void);
extern void far f_00BA_01B6(void);
extern void far f_00BA_0002(void);
extern int far WaitedEnough(long far *timer, int delay);
extern void far f_1FD2_05FD(void);

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
                printf(fd_55B3_1CDC);
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
    fd_50F6_3944 = f_171C_1750();
    if (!g_6108 && fd_50F6_3944 < 0x1fbd0L) {
        printf(fd_55B3_1CD8);
        exit(1);
    }
    f_277D_000D(7);
    f_277D_000C();
    fd_50F6_38B2 = getcwd(0, 0);
    fd_50F6_38B6 = *fd_50F6_38B2;
    v = strlen(fd_50F6_38B2) - 1;
    if (fd_50F6_38B2[v] == '\\')
        fd_50F6_38B2[v] = 0;
    if ((i = open("language.dat", 0)) > 0) {
        close(i);
        db_SetDataBase("language");
    }
    db_SetDataBase("shared");
    switch (g_5A97) {
    case 2:
    case 4:
        db_SetDataBase("lrshare");
    }
    f_205F_0004(fd_55B3_1CD4);
    if (g_5A97 == 0)
        win_SetPalette(1);
    else if (g_5A97 == 8) {
        win_SetPalette(0);
        f_1B4E_0228(15);
    }
    o17_384C_0000();
    _harderr(f_208F_058B);
    if (g_3DB2 == 320) {
        o17_384C_0143(8, 11, 0);
        o17_384C_0169(0, 0);
    } else {
        o17_384C_0143(7, 14, 12);
        o17_384C_0169(7, 7);
    }
    (*g_9134)(0, 0, g_3DB2, g_3DB4, f_1B4E_000D(15));
    i = g_610C[g_5A97];
    f_208F_0419(&size, i);
    win_DrawBitMap((g_3DB2 - size.x) / 2, (g_3DB4 - size.y) / 2, i);
    f_171C_1EFA();
    f_171C_0EDE();
    t = TickCount();
    f_1B28_0129(4);
    if (g_3DB2 != 320 || !o17_384C_0039(1))
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

extern char far * far fd_55B3_1CE4;
extern char far * far fd_55B3_1CE0;
extern int far puts(char far *s);

void far ReadConfig(void)
{
    char mode;
    char lang;
    int fd;
    char far *msg;

    if ((fd = open(fd_55B3_1CE4, 0)) <= 0) {
        msg = fd_55B3_1CE0;
        goto fail;
    } else {
        SkipWords(fd, 2); read(fd, &mode, 1);
        SkipWords(fd, 2); read(fd, &lang, 1);
        close(fd);
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
