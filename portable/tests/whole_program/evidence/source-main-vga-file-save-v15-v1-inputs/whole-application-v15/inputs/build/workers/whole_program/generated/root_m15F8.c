#include "portable/whole_program/state/main_loop_counter.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/state/source_tables.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

extern int16_t  fd_3D57_07CC[];
#include "platform/startup_host.h"
#include "platform/startup_preflight.h"
#include "platform/dos_io.h"
/* Root module 15F8: program entry (main) and the main loop. */

char  *fd_55B3_1CD4[] = {
    "nt",
    "Sorry, not enough memory to run.  Please see your SimAnt addendum for\nmore information on how to free up memory on your system.",
    "\nBAD SWITCH\nUSAGE: SimAnt [/d{EeTHMm2V}] [/s{NABCI}]",
    "SimAnt configuration file missing",
    "simant.cfg"
};
char g_1CE8 = 0;

extern int16_t g_38A0;

extern int16_t dos_errno;
char  fd_4E37_0000[] =
    "\nSimAnt cannot open enough files to run.  Please increase the 'FILES=n'\n"
    "statement in the CONFIG.SYS file on your boot drive by %d.  If there \n"
    "is no 'FILES=n' (where n is some number) in your CONFIG.SYS file, or \n"
    "you have no CONFIG.SYS file, please refer to your DOS manual about   \n"
    "how to edit/create one.";
extern void  exit(int16_t code);
extern char *dos_startup_error_text(int16_t error);


extern int16_t  fd_50F6_10D0;
extern void ( *  signal(int16_t sig, void ( *func)(int16_t)))(int16_t);
extern void  f_00F8_0585(void);
extern void  o15_384C_0125(void);
extern void  IBMInitStuff(int16_t argc, char  *  *argv);
extern void  db_SetDataBase(char  *name);
extern void  f_00DF_0004(void);

extern void  LoadMonoPats(void);
extern void  ShowIntro(void);
extern void  CustomerIDDialog(void);
extern int16_t  NewGame(int16_t a);
extern void  o15_384C_0152(char  *message, int16_t code);
extern int16_t  fd_50F6_0A9C;
extern int16_t  fd_50F6_0AA6;
extern int32_t  MacTickCount(void);
extern void  win_NoWindowsShouldBeLocked(void);
extern void  f_0000_046F(void);

void  f_15F8_0313(void);
extern void  DoAntSim(void);
extern int16_t  win_IsWinOpen(int16_t win);
extern int16_t  win_IsWinInFront(int16_t win);
extern int16_t  fd_50F6_04C0;
extern void  o12_384C_100A(void);
extern void  MakeDMap(int16_t a);
extern int16_t  WaitedEnough(int32_t *stamp, int16_t delay);
extern void  o13_384C_03F8(void);
extern void  UpdateYard(void);
extern void  UpdateEdit(void);
extern void  f_0250_0ED2(void);
extern void  f_00F8_01BE(void);

void dos_game_main(int16_t argc, char  *  *argv)
{
    int32_t i;
    int16_t last;
    int32_t stamp;
    int16_t fh[5];
     uint16_t frames;

    g_1CE8 = 1;
    g_38A0 = 8;
    {
        int16_t opened_before_failure;
        if (dos_startup_preflight("INSTALL.EXE", &fd_50F6_10D0,
                                  &opened_before_failure) < 0) {
            if (dos_errno == 24) {
                dos_printf(fd_4E37_0000, 5 - opened_before_failure);
                exit(1);
            } else {
                dos_printf("DOS Error %d: %s", dos_errno,
                       dos_startup_error_text(dos_errno));
                exit(2);
            }
        }
    }
    dos_host_ignore_legacy_break();
    dos_host_ignore_legacy_interrupt();
    f_00F8_0585();
    o15_384C_0125();
    IBMInitStuff(argc, argv);
    db_SetDataBase("sound");
    f_00DF_0004();
    if (g_5A97 & 1)
        LoadMonoPats();
    ShowIntro();
    CustomerIDDialog();
    if (NewGame(1) < 0)
        o15_384C_0152("SimAnt cancelled.", 0);
    fd_50F6_0A9C = 0;
    fd_50F6_0AA6 = 0;
    frames = 0;
    MacTickCount();
    (fd_3D57_07CC[0]) = 1;
    for (;;) {
        win_NoWindowsShouldBeLocked();
        frames++;
        f_0000_046F();
        fd_50F6_383A++;
        f_15F8_0313();
        i = MacTickCount();
        if (native_state_fd_50F6_047E.signed_value == 0 || (native_state_fd_50F6_0AA0.signed_value != 0 && native_state_fd_50F6_105E.signed_value < 10)) {
            i += (fd_3D57_07CC + 1)[(fd_3D57_07CC[0])];
            DoAntSim();
        }
        if ((fd_3D57_07CC[0]) != 3 || (fd_50F6_0A9C & 3) == 0) {
            if (win_IsWinOpen(0x100)) {
                if (fd_50F6_0AA6 >= 0 && !win_IsWinInFront(0x100) && (fd_3D57_07CC[0]) != 3) {
                    if (fd_50F6_04C0 == 0) {
                        if (fd_50F6_0AA6 & 1)
                            o12_384C_100A();
                        fd_50F6_0AA6 ^= 1;
                    }
                } else {
                    MakeDMap(0);
                    o12_384C_100A();
                    fd_50F6_0AA6 = 0;
                }
            }
            if (win_IsWinOpen(0x1900)) {
                if (WaitedEnough(&stamp, 0x48) || native_state_YardMode.signed_value <= 2)
                    UpdateYard();
                else if (native_state_YardMode.signed_value > 1)
                    o13_384C_03F8();
            }
            if (win_IsWinOpen(0)) {
                UpdateEdit();
                f_0250_0ED2();
            }
            last = frames;
            do
                f_00F8_01BE();
            while (MacTickCount() < i);
        }
        f_00F8_01BE();
        fd_50F6_0A9C = (fd_50F6_0A9C + 1) & 0x3f;
    }
}

void  f_15F8_0313(void)
{
}

#pragma pack(pop)
