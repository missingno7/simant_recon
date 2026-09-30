/* Root module 15F8: program entry (main) and the main loop. */

char far *fd_55B3_1CD4[] = {
    "nt",
    "Sorry, not enough memory to run.  Please see your SimAnt addendum for\nmore information on how to free up memory on your system.",
    "\nBAD SWITCH\nUSAGE: SimAnt [/d{EeTHMm2V}] [/s{NABCI}]",
    "SimAnt configuration file missing",
    "simant.cfg"
};
char g_1CE8 = 0;

extern int far fd_55B3_38A0;
extern int far open(char far *name, int mode, ...);
extern int near errno;
extern char far fd_4E37_0000[];
extern int far printf(char far *format, ...);
extern void far exit(int code);
extern char far * near sys_errlist[];
extern int far close(int fh);
extern int far fd_50F6_10D0;
extern void (far * far signal(int sig, void (far *func)(int)))(int);
extern void far f_00F8_0585(void);
extern void far o15_384C_0125(void);
extern void far IBMInitStuff(int argc, char far * far *argv);
extern void far db_SetDataBase(char far *name);
extern void far f_00DF_0004(void);
extern char near g_5A97;
extern void far LoadMonoPats(void);
extern void far ShowIntro(void);
extern void far CustomerIDDialog(void);
extern int far o15_384C_03C6(int a);
extern void far o15_384C_0152(char far *message, int code);
extern int far fd_50F6_0A9C;
extern int far fd_50F6_0AA6;
extern long far f_00F8_02BE(void);
extern int far fd_3D57_07CC;
extern void far win_NoWindowsShouldBeLocked(void);
extern void far f_0000_046F(void);
extern long far fd_50F6_383A;
void far f_15F8_0313(void);
extern int far fd_50F6_047E;
extern int far fd_50F6_0AA0;
extern int far fd_50F6_105E;
extern int far fd_3D57_07CE[];
extern void far DoAntSim(void);
extern int _fastcall win_IsWinOpen(int win);
extern int _fastcall win_IsWinInFront(int win);
extern int far fd_50F6_04C0;
extern void far o12_384C_100A(void);
extern void far f_00F8_03A5(int a);
extern int far WaitedEnough(long *stamp, int delay);
extern int far fd_50F6_035C;
extern void far o13_384C_03F8(void);
extern void far UpdateYard(void);
extern void far f_0250_0E9D(void);
extern void far f_0250_0ED2(void);
extern void far f_00F8_01BE(void);

void main(int argc, char far * far *argv)
{
    long i;
    int last;
    long stamp;
    int fh[5];
    register unsigned frames;

    g_1CE8 = 1;
    fd_55B3_38A0 = 8;
    for (i = 0; i < 5; i++) {
        if ((fh[i] = open("install.exe", 0)) <= 0) {
            if (errno == 24) {
                printf(fd_4E37_0000, 5 - i);
                exit(1);
            } else {
                printf("DOS Error %d: %s", errno, sys_errlist[errno]);
                exit(2);
            }
        }
    }
    for (i = 0; i < 5; i++)
        close(fh[i]);
    fd_50F6_10D0 = fh[0];
    signal(0x15, (void (far *)(int))1L);
    signal(2, (void (far *)(int))1L);
    f_00F8_0585();
    o15_384C_0125();
    IBMInitStuff(argc, argv);
    db_SetDataBase("sound");
    f_00DF_0004();
    if (g_5A97 & 1)
        LoadMonoPats();
    ShowIntro();
    CustomerIDDialog();
    if (o15_384C_03C6(1) < 0)
        o15_384C_0152("SimAnt cancelled.", 0);
    fd_50F6_0A9C = 0;
    fd_50F6_0AA6 = 0;
    frames = 0;
    f_00F8_02BE();
    fd_3D57_07CC = 1;
    for (;;) {
        win_NoWindowsShouldBeLocked();
        frames++;
        f_0000_046F();
        fd_50F6_383A++;
        f_15F8_0313();
        i = f_00F8_02BE();
        if (fd_50F6_047E == 0 || (fd_50F6_0AA0 != 0 && fd_50F6_105E < 10)) {
            i += fd_3D57_07CE[fd_3D57_07CC];
            DoAntSim();
        }
        if (fd_3D57_07CC != 3 || (fd_50F6_0A9C & 3) == 0) {
            if (win_IsWinOpen(0x100)) {
                if (fd_50F6_0AA6 >= 0 && !win_IsWinInFront(0x100) && fd_3D57_07CC != 3) {
                    if (fd_50F6_04C0 == 0) {
                        if (fd_50F6_0AA6 & 1)
                            o12_384C_100A();
                        fd_50F6_0AA6 ^= 1;
                    }
                } else {
                    f_00F8_03A5(0);
                    o12_384C_100A();
                    fd_50F6_0AA6 = 0;
                }
            }
            if (win_IsWinOpen(0x1900)) {
                if (WaitedEnough(&stamp, 0x48) || fd_50F6_035C <= 2)
                    UpdateYard();
                else if (fd_50F6_035C > 1)
                    o13_384C_03F8();
            }
            if (win_IsWinOpen(0)) {
                f_0250_0E9D();
                f_0250_0ED2();
            }
            last = frames;
            do
                f_00F8_01BE();
            while (f_00F8_02BE() < i);
        }
        f_00F8_01BE();
        fd_50F6_0A9C = (fd_50F6_0A9C + 1) & 0x3f;
    }
}

void far f_15F8_0313(void)
{
}
