#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include <stddef.h>
#include "platform/startup_host.h"
/* Overlay section S15, code frame 384C: start-up and shut-down helpers
   (demo expiry, monochrome patterns, disk reset, fatal exit, quit dialog,
   default windows, new game). */

typedef char  *  *Handle;

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

void  o15_384C_0152(char  *msg, int16_t flag);

void  o15_384C_0000(void)
{
    o15_384C_0152("SimAnt IBM DEMO version has expired.  Please get an update.", 0);
}

extern Handle  db_LoadObject(int16_t object, int16_t kind);
extern void  Punt(char  *format, ...);
extern uint8_t  g_8EC0[];
extern void  db_PurgeObject(int16_t object, int16_t kind);
extern uint8_t *g_8ED8;
extern int16_t sim_source_runtime_reserve_mono_patterns(size_t bytes);

void  LoadMonoPats(void)
{
    Handle h;
    uint8_t  *src;
    uint8_t  *dst;
    int16_t n;
    int16_t i;

    h = db_LoadObject(0x2710, 0x16);
    if (h == 0 || **(int16_t  *  *)h != 0x300)
        Punt("Cannot load monochrome patterns.");
    src = (uint8_t  *)*h + 2;
    dst = g_8EC0;
    n = 0x18;
    for (i = 0; i < n; i++)
        *dst++ = ~*src++;
    db_PurgeObject(0x2710, 0x16);
    h = db_LoadObject(0x271a, 0x16);
    if (h == 0)
        Punt("Cannot load monochrome patterns.");
    n = (*h)[1] << 3;
    if (n < 0 || !sim_source_runtime_reserve_mono_patterns((size_t)n))
        Punt("Cannot allocate monochrome patterns.");
    src = (uint8_t  *)*h + 2;
    dst = g_8ED8;
    for (i = 0; i < n; i++)
        *dst++ = ~*src++;
    db_PurgeObject(0x271a, 0x16);
}

void  o15_384C_0125(void)
{
    dos_host_retire_bios_reset_loop();
}

static int16_t g_2BD4 = 1;

extern void  f_171C_0676(int16_t flag);
extern void  f_277D_000B(char  *msg);
extern void  f_171C_030C(char  *msg);
extern int16_t g_610A;
extern void  f_277E_0154(void);
extern void  f_1C62_00A1(void);
extern void  f_1C62_0090(void);
extern int16_t  puts(char  *s);
extern void   f_00DE_000A(int16_t code);
extern void  exit(int16_t code);

void  o15_384C_0152(char  *msg, int16_t flag)
{
    f_171C_0676(0);
    switch (g_2BD4++) {
    case 0:
        g_2BD4 = 1;
        f_277D_000B(msg);
    case 1:
        g_2BD4 = 2;
        if (flag)
            f_171C_030C(msg);
    case 2:
        g_2BD4 = 3;
        if (g_610A)
            f_277E_0154();
        f_1C62_00A1();
        f_1C62_0090();
        puts(msg);
    }
    if (flag)
        f_00DE_000A(1);
    exit(0);
}

extern int16_t  fd_3D57_02C2;
int16_t  o15_384C_0239(int16_t which);
extern int16_t  o09_35F5_0188(int16_t flag);

int16_t  MenuQuit(void)
{
    int16_t r;

    if (fd_3D57_02C2) {
        do {
            r = o15_384C_0239(1);
            if (r == 2)
                return 0;
            if (r != 1)
                break;
        } while (o09_35F5_0188(0) == 0);
    }
    o15_384C_0152("SimAnt was brought to you by the people at MAXIS.  Thank you for playing.", 0);
}

extern void  win_Open(int16_t win);
extern Handle  f_1A53_00F0(int16_t object, int16_t kind, int16_t type);
extern char  *  f_171C_1B84(Handle h);
extern void  f_24AB_02AD(int16_t font);

extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  f_1CE2_044D(struct Rect  *rect, int16_t width);
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  win_PrintTextInRect(int16_t first, char  *text, struct Rect  *rect);
extern int16_t  f_1F58_0038(void);
extern int16_t  f_1F58_0090(void);
extern int16_t  win_GetEvent(struct Event  *ev);
extern Handle  f_171C_1BBA(Handle h);
extern void  db_ReleaseHandle(Handle handle);
extern void  win_Close(int16_t win);

int16_t  o15_384C_0239(int16_t which)
{
    struct Event ev;
    struct Rect r;
    Handle h;
    char  *text;
    int16_t result;

    win_Open(0x2100);
    h = f_1A53_00F0((0x41 - which) * 2, 10, 1);
    text = f_171C_1B84(h);
    f_24AB_02AD(SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140 ? 2 : 4);
    if (g_5A97 & 1) {
        win_GetObjRect(0x2100, &r);
        (*g_9128)(0, 0, 0);
        f_1CE2_044D(&r, 2);
    }
    win_GetObjRect(0x2101, &r);
    win_SetColorFromObjNum(0x2101);
    win_PrintTextInRect(0, text, &r);
    f_24AB_02AD(0);
    for (;;) {
        if (f_1F58_0038()) {
            switch (f_1F58_0090()) {
            case 0x0d:
            case 'D':
            case 'd':
                result = 0;
                goto done;
            case 'S':
            case 's':
                result = 1;
                goto done;
            case 0x1b:
            case 'C':
            case 'c':
                result = 2;
                goto done;
            }
        }
        if (win_GetEvent(&ev)) {
            switch (ev.code) {
            case 0x2103:
                result = 0;
                goto done;
            case 0x2104:
                result = 1;
                goto done;
            case 0x2105:
                result = 2;
                goto done;
            }
        }
    }
done:
    f_171C_1BBA(h);
    db_ReleaseHandle(h);
    win_Close(0x2100);
    return result;
}

extern void  OpenCasteWindow(void);
extern void  OpenModeWindow(void);
extern void  SetEditWinTitle(char  *title);
extern void  SetMapPlane(int16_t plane);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  YardToMap(void);
extern void  SetMapTitle(void);
extern void  OpenEditWindow(void);

void  SetDefaultWindows(void)
{
    OpenCasteWindow();
    OpenModeWindow();
    SetEditWinTitle(0L);
    SetMapPlane(native_state_MapPlane.signed_value);
    if (!win_IsWinOpen(0x100))
        YardToMap();
    SetMapTitle();
    OpenEditWindow();
}

extern int16_t  DoScenario(int16_t flag);
extern int16_t  LoadGame(int16_t a, int16_t b);
extern int16_t  fd_50F6_0EAC;
extern void  EndLifeTransferMode(void);
extern void  EndTargetMode(void);
extern void  SetDefaultWindPrompt(int16_t);
extern int16_t  fd_50F6_0354;
extern void  RandYard(void);
extern int16_t  MePlane;
extern int16_t  WinPrintf(char  *format, ...);
extern int16_t  fd_3D57_07A4;
extern int16_t  fd_3D57_07A6;
extern int16_t  f_22BF_0A65(void);
extern void  o26_39C7_0000(void);
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern void  CenterEdit(int16_t x, int16_t y);
extern void  UpdateEdit(void);

int16_t  NewGame(int16_t flag)
{
    int16_t r;

    fd_3D57_02C2 = 0;
    for (;;) {
        r = DoScenario(flag);
        if (r == 0x205)
            return -1;
        if (r == 0x207) {
            if (LoadGame(0, 0) == 0)
                continue;
            r = 1;
        } else {
            switch (r) {
            case 0x202:
                r = 1;
                break;
            case 0x203:
                r = 2;
                break;
            case 0x204:
                r = 3;
                break;
            case 0x206:
                r = 0;
                break;
            }
            if (r >= 0 && r < 4) {
                fd_50F6_0EAC = r;
                if (native_state_fd_50F6_105E.signed_value == 10)
                    EndLifeTransferMode();
                else if (native_state_fd_50F6_105E.signed_value == 11)
                    EndTargetMode();
                SetDefaultWindPrompt(1);
                SetEditWinTitle(0L);
                fd_50F6_0354 = 1;
                native_state_fd_50F6_07C8.signed_value = 0;
                RandYard();
                WinPrintf("MePLane=%d", MePlane);
                SetMapPlane(MePlane);
                if (fd_50F6_0EAC == 0) {
                    fd_3D57_07A4 = 1;
                    fd_3D57_07A6 = 0;
                    if (flag == 0)
                        win_Open(0);
                }
            }
        }
        break;
    }
    SetDefaultWindows();
    SetMapPlane(MePlane);
    if (r == 0 && !f_22BF_0A65())
        o26_39C7_0000();
    CenterEdit(MeLocX, MeLocY);
    UpdateEdit();
    fd_3D57_02C2 = 0;
    return r;
}

#pragma pack(pop)
