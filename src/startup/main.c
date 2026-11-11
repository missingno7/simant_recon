/*
 * Contains main and the main game loop. It processes command line options, checks configuration
 * and resources, initializes the game and performs shutdown.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 15F8; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og.
 */

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
char far fd_4E37_0000[] =
    "\nSimAnt cannot open enough files to run.  Please increase the 'FILES=n'\n"
    "statement in the CONFIG.SYS file on your boot drive by %d.  If there \n"
    "is no 'FILES=n' (where n is some number) in your CONFIG.SYS file, or \n"
    "you have no CONFIG.SYS file, please refer to your DOS manual about   \n"
    "how to edit/create one.";
extern int far printf(char far *format, ...);
extern void far exit(int code);
extern char far * near sys_errlist[];
extern int far close(int fh);
extern int far fd_50F6_10D0;
extern void (far * far signal(int sig, void (far *func)(int)))(int);
extern void far res_install_cache_hook(void);
extern void far bios_probe_reset_disks(void);
extern void far IBMInitStuff(int argc, char far * far *argv);
extern void far db_SetDataBase(char far *name);
extern void far snd_init_driver_once(void);
extern char near g_5A97;
extern void far LoadMonoPats(void);
extern void far ShowIntro(void);
extern void far CustomerIDDialog(void);
extern int far NewGame(int a);
extern void far app_cleanup_and_exit(char far *message, int code);
extern int far fd_50F6_0A9C;
extern int far fd_50F6_0AA6;
extern long far MacTickCount(void);
extern int far GameSpeed;
extern void far win_NoWindowsShouldBeLocked(void);
extern void far snd_service_pending(void);
extern long far fd_50F6_383A;
void far f_15F8_0313(void);
extern int far GamePaused;
extern int far MeMoveMe;
extern int far CurGameTool;
extern int far fd_3D57_07CE[];
extern void far DoAntSim(void);
extern int _fastcall win_IsWinOpen(int win);
extern int _fastcall win_IsWinInFront(int win);
extern int far fd_50F6_04C0;
extern void far DrawMap(void);
extern void far MakeDMap(int a);
extern int far WaitedEnough(long *stamp, int delay);
extern int far YardMode;
extern void far yard_refresh_message_area(void);
extern void far UpdateYard(void);
extern void far UpdateEdit(void);
extern void far f_0250_0ED2(void);
extern void far ui_pump_events_edge_scroll(void);

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
    res_install_cache_hook();
    bios_probe_reset_disks();
    IBMInitStuff(argc, argv);
    db_SetDataBase("sound");
    snd_init_driver_once();
    if (g_5A97 & 1)
        LoadMonoPats();
    ShowIntro();
    CustomerIDDialog();
    if (NewGame(1) < 0)
        app_cleanup_and_exit("SimAnt cancelled.", 0);
    fd_50F6_0A9C = 0;
    fd_50F6_0AA6 = 0;
    frames = 0;
    MacTickCount();
    GameSpeed = 1;
    for (;;) {
        win_NoWindowsShouldBeLocked();
        frames++;
        snd_service_pending();
        fd_50F6_383A++;
        f_15F8_0313();
        i = MacTickCount();
        if (GamePaused == 0 || (MeMoveMe != 0 && CurGameTool < 10)) {
            i += fd_3D57_07CE[GameSpeed];
            DoAntSim();
        }
        if (GameSpeed != 3 || (fd_50F6_0A9C & 3) == 0) {
            if (win_IsWinOpen(0x100)) {
                if (fd_50F6_0AA6 >= 0 && !win_IsWinInFront(0x100) && GameSpeed != 3) {
                    if (fd_50F6_04C0 == 0) {
                        if (fd_50F6_0AA6 & 1)
                            DrawMap();
                        fd_50F6_0AA6 ^= 1;
                    }
                } else {
                    MakeDMap(0);
                    DrawMap();
                    fd_50F6_0AA6 = 0;
                }
            }
            if (win_IsWinOpen(0x1900)) {
                if (WaitedEnough(&stamp, 0x48) || YardMode <= 2)
                    UpdateYard();
                else if (YardMode > 1)
                    yard_refresh_message_area();
            }
            if (win_IsWinOpen(0)) {
                UpdateEdit();
                f_0250_0ED2();
            }
            last = frames;
            do
                ui_pump_events_edge_scroll();
            while (MacTickCount() < i);
        }
        ui_pump_events_edge_scroll();
        fd_50F6_0A9C = (fd_50F6_0A9C + 1) & 0x3f;
    }
}

void far f_15F8_0313(void)
{
}
