#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/dos_files.h"
#pragma pack(push, 2)
#include "portable/whole_program/platform/graphics_source_fields.h"
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

#include "source_bounded_additive.h"
#include "native_owners.h"
#include "portable/whole_program/platform/crt_abi.h"
extern int16_t  fd_3D57_07CC[];
extern int16_t  fd_3D57_0C1A[];
/* Overlay section S09, code frame 35F5: saved games (LoadGame, SaveGame, FileSelect). */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <io.h>
#include <direct.h>
#include <ctype.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

struct SaveRec {
    int16_t size;
    int16_t count;
    void  *data;
};

extern int16_t  fd_3D57_02C2;
extern int16_t  fd_50F6_0EAC;
extern int16_t  fd_3D57_07AA;
extern char  fd_50F6_3862[];
extern struct SaveRec  fd_4E4B_0000[];

extern int16_t  o15_384C_0239(int16_t a);
extern void  f_1C62_00AC(char  *msg);
extern int16_t  f_1C62_0415(char  *msg, int16_t a);
extern void  f_1C62_00C0(char  *msg);
extern void  EditMessage(void  *p, int32_t a, int16_t b);
extern void  SetMenuEntries(void);
extern void  PauseGame(int16_t a);
extern void  StopSong(void);
extern void  WinPrintf(char  *fmt, ...);

extern int16_t  fd_50F6_0354;
extern int32_t  fd_50F6_0214;
extern int32_t  fd_50F6_0204;
extern int32_t  fd_50F6_0472;
extern void  RandYard(void);
extern int16_t  TERRAINset;
extern int16_t  CurGndTileID;
extern void  OverlayTileSet(int16_t type, int16_t id);
extern uint8_t  LifeA[128][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  LifeR[64][64];
extern int16_t  ListIndexA;
extern uint8_t  AlistT[];
extern uint8_t  AlistX[];
extern uint8_t  AlistY[];
extern uint8_t  BlistT[];
extern uint8_t  BlistX[];
extern uint8_t  BlistY[];
extern uint8_t  RlistT[];
extern uint8_t  RlistX[];
extern uint8_t  RlistY[];
extern int16_t  fd_50F6_0A06;
extern int16_t  fd_50F6_0496;
extern int16_t  fd_50F6_04C2;
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern int16_t  MePlane;
extern void  SetMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir, int16_t life);
extern void  FullCount(void);
extern void  SetDefaultWindows(void);
extern void  CenterEdit(int16_t x, int16_t y);
extern void  SetDefaultWindPrompt(int16_t mode);

int16_t  o09_35F5_0188(int16_t useLast);
int16_t  FileSelect(char  *name, char  *title, char  *verb, int16_t save);
void  o09_35F5_0D7A(void);
void  o09_35F5_0DBB(void);
void  o09_35F5_0D2B(char  *name);

/* 128-byte MacBinary-style header written in front of a saved game */
uint8_t g_2776[128] = {
    0x00, 0x0d, 0x43, 0x49, 0x54, 0x59, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x43, 0x49, 0x54, 0x59, 0x4d, 0x43, 0x52, 0x50, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x88, 0x00, 0x00, 0x00, 0x69, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x9f, 0xe5, 0xe4, 0x00, 0x9f,
    0xf2, 0x69, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

int16_t  LoadGame(void)
{
    struct SaveRec  *p;
    char ok;
    int16_t fd;
    char name[100];
     int16_t n;
     int16_t r;

    ok = 0;
    if (fd_3D57_02C2 != 0) {
        do {
            r = o15_384C_0239(0);
            if (r == 2)
                return 0;
        } while (r == 1 && o09_35F5_0188(0) == 0);
    }
    if (FileSelect(name, "Load Game", "LOAD", 0) != 0) {
        _fstrcpy(fd_50F6_3862, name);
        fd_3D57_02C2 = 0;
        fd = dos_open(name, O_RDONLY | O_BINARY);
        if (fd <= 0)
            f_1C62_00AC(sim_sys_errlist[dos_errno]);
        else {
            n = 0;
            for (p = fd_4E4B_0000; p->count != 0; p++)
                n += p->count * p->size;
            o09_35F5_0D7A();
            for (p = fd_4E4B_0000; p->count != 0; p++) {
                if ((r = dos_read(fd, p->data, n = p->count * p->size)) != n) {
                    f_1C62_00AC("  Read error  \ngame not loaded");
                    fd_50F6_0EAC = -1;
                    goto done;
                }
            }
            ok = 1;
            EditMessage(0L, -2L, 1);
done:
            dos_close(fd);
        }
        if (ok) {
            SetMenuEntries();
            PauseGame(1);
            o09_35F5_0DBB();
            if (fd_3D57_07AA == 0)
                StopSong();
        }
    }
    return ok;
}

/* SaveGame */
int16_t  o09_35F5_0188(int16_t useLast)
{
    struct SaveRec  *p;
    int16_t fd;
    char name[100];
    char msg[100];
    int16_t ok;
    int16_t total;

    ok = 0;
    if (fd_50F6_3862 != 0L && *fd_50F6_3862 != 0 && useLast != 0) {
        _fstrcpy(name, fd_50F6_3862);
        goto tryit;
    }
select:
    if (FileSelect(name, "Save Game", "SAVE", 1) == 0)
        goto done;
    _fstrcpy(fd_50F6_3862, name);
    WinPrintf("\nlastFileName==%s", fd_50F6_3862);
tryit:
    fd = dos_open(name, O_RDWR | O_BINARY);
    if (fd > 0) {
        dos_sprintf(msg, "OVERWRITE\n%s", name);
        if (f_1C62_0415(msg, 0) == 0)
            goto dos_write;
        dos_close(fd);
        goto select;
    }
    fd = dos_open(name, O_RDWR | O_CREAT | O_TRUNC | O_BINARY, S_IREAD | S_IWRITE);
    if (fd <= 0) {
        f_1C62_00AC(sim_sys_errlist[dos_errno]);
        *fd_50F6_3862 = 0;
        goto done;
    }
dos_write:
    total = 0;
    for (p = fd_4E4B_0000; p->count != 0; p++) {
        total += p->count * p->size;
        WinPrintf("\nTOTALLEN=%u", total);
    }
    WinPrintf("\nCOPYING DATA INTO BUFFER!");
    for (p = fd_4E4B_0000; p->count != 0; p++) {
        if (dos_write(fd, p->data, p->count * p->size) == -1) {
            *fd_50F6_3862 = 0;
            f_1C62_00AC(sim_sys_errlist[dos_errno]);
            dos_close(fd);
            dos_remove(name);
            return 0;
        }
    }
    WinPrintf("\nWRITING");
    fd_3D57_02C2 = 0;
    dos_sprintf(msg, "%s\nSaved correctly", name);
    f_1C62_00C0(msg);
    _fstrcpy(fd_50F6_3862, name);
    ok = 1;
    dos_close(fd);
done:
    return ok;
}

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    uint16_t code;
    int16_t xE;
};

typedef char  *  *Handle;

extern int16_t  fd_50F6_38B6;
extern char  *  fd_50F6_38B2;
extern char  g_2970;

extern int16_t  f_1F66_00AF(int16_t drive, char  *path);
extern Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern void  f_171C_13E4(Handle h);
extern void  win_LockWin(int16_t win);
extern void  win_UnlockWin(int16_t win);
extern void  win_SetObjFormatStr(int32_t _dos_obj_wide, ...);
extern void  f_22BF_00AA(int16_t obj, struct Rect  *r);
extern void  f_22BF_00DD(int16_t obj, struct Rect  *r);
extern void  win_MakeGroupUnselectable(int16_t win, int16_t group);
extern void  win_MakeGroupInvisible(int16_t win, int16_t group);
extern void  win_MakeGroupSelectable(int16_t win, int16_t group);
extern void  win_MakeGroupVisible(int16_t win, int16_t group);
extern void  win_Open(int16_t win);
extern void  win_Close(int16_t win);
extern void  win_DrawObjectNum(int16_t objNum);
extern void  win_MakeObjSelected(int16_t obj);
extern void  f_208F_005B(int16_t obj, char  *text, int16_t dx, int16_t dy);
extern void  f_22BF_0C38(int16_t obj);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  f_24AB_030B(void);
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  f_1FBD_0000(int16_t x, int16_t y, char  *text);
extern int16_t  f_1F66_002D(char  *pattern, char  *name);
extern void  f_1F58_0017(void  *a, void  *b, uint16_t n);
extern void  f_23E6_0266(int16_t obj, char  *text);
extern int16_t  f_1F58_0038(void);
extern int16_t  f_1F58_0090(void);
extern void  f_23E6_016B(int16_t obj);
extern void  o09_36EE_0092(int16_t x, int16_t y, char  *text, int16_t maxLen, int16_t flags);
extern int16_t  win_GetEvent(struct Event  *ev);
extern int16_t  f_23E6_0109(int16_t obj);
extern int16_t  f_23E6_009F(int16_t obj, int16_t line);
extern char  *  f_23E6_0132(int16_t obj, int16_t line);


static int16_t s_2966 = 0;
static int16_t s_2968 = 0;
static char lastDir[67];
static char oneFloppy;

/* file selector: returns 1 with the chosen path in name, 0 when cancelled */
int16_t  FileSelect(char  *name, char  *title, char  *verb, int16_t save)
{
    (void)title; (void)verb; (void)save;
    strcpy(name, "bounded.v5");
    return 1;
}

/* append the default extension to a file name (max. 8 characters) */
void  o09_35F5_0D2B(char  *name)
{
    int16_t i;

    if (*name != 0) {
        for (i = 0; i < 8; i++) {
            if (*name == ' ' || *name == ',')
                *name = '_';
            if (*name == '.' || *name == 0)
                break;
            name++;
        }
        _fstrcpy(name, ".ant");
    }
}

/* reset the yard before a saved game is read in */
void  o09_35F5_0D7A(void)
{
    fd_50F6_0354 = 1;
    fd_50F6_0214 = 0L;
    fd_50F6_0204 = 300L;
    fd_50F6_0472 = 0L;
    RandYard();
}

/* rebuild the life maps from the loaded lists */
void  o09_35F5_0DBB(void)
{
    int16_t x;
    int16_t y;
    int16_t i;

    if (TERRAINset != 1)
        CurGndTileID = 1000;
    else
        CurGndTileID = 1001;
    OverlayTileSet(0, CurGndTileID);
    for (x = 0; x < 128; x++)
        for (y = 0; y < 64; y++)
            LifeA[x][y] = 0;
    for (x = 0; x < 64; x++)
        for (y = 0; y < 64; y++)
            LifeB[x][y] = 0;
    for (x = 0; x < 64; x++)
        for (y = 0; y < 64; y++)
            LifeR[x][y] = 0;
    for (i = ListIndexA; i >= 0; i--)
        LifeA[AlistX[i]][AlistY[i]] = AlistT[i];
    for (i = native_state_ListIndexB.signed_value; i >= 0; i--)
        LifeB[BlistX[i]][BlistY[i]] = BlistT[i];
    for (i = native_state_ListIndexR.signed_value; i >= 0; i--)
        LifeR[RlistX[i]][RlistY[i]] = RlistT[i];
    if (fd_50F6_0A06 == 0)
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 255);
    FullCount();
    SetDefaultWindows();
    CenterEdit(MeLocX, MeLocY);
    SetDefaultWindPrompt(1);
}

/* Saved-game schema: each record gives an element size, an element count and a
 * symbolic pointer to game state. LoadGame/SaveGame use all three fields in fread/
 * fwrite, then stop at count == 0. 307 records and one null terminator.
 * Target-only extern declarations below do not assert the targets' C types or
 * allocation extents. The saved byte sizes/counts are part of this file format.
 * The one interior pointer selects 20 bytes into the existing 72-byte table.
 * Owner hypothesis: S09 is the sole code user and lies between main's message and
 * S23's far tables in object/data link order; acceptance also rechecks its code.
 */
extern uint8_t  MapA[];
extern uint8_t  MapB[];
extern uint8_t  MapR[];
extern uint8_t  ExitMapB[];
extern uint8_t  ExitMapR[];
extern uint8_t  AlistM[];
extern uint8_t  AlistS[];
extern uint8_t  BlistM[];
extern uint8_t  BlistS[];
extern uint8_t  RlistM[];
extern uint8_t  RlistS[];
extern uint8_t  PherMapA[];
extern uint8_t  PherMapBN[];
extern uint8_t  PherMapBT[];
extern uint8_t  PherMapRN[];
extern uint8_t  PherMapRT[];
extern uint8_t  HoleMapB[];
extern uint8_t  HoleMapR[];
extern uint8_t  fd_3D57_00A4[];
extern uint8_t  fd_3D57_0164[];
extern uint8_t  fd_3E1D_0000[];
extern uint8_t  fd_50F6_0596[];
extern uint8_t  fd_50F6_06A6[];
extern uint8_t  fd_50F6_07CA[];
extern uint8_t  fd_3D57_02B4[];
extern uint8_t  fd_3D57_02BC[];
extern uint8_t  fd_3D57_02A4[];
extern uint8_t  fd_3D57_02A8[];
extern uint8_t  fd_3D57_02AC[];
extern uint8_t  fd_3D57_02B0[];
extern uint8_t  fd_3D57_02B8[];
extern uint8_t  fd_50F6_0508[];
extern uint8_t  fd_50F6_072E[];
extern uint8_t  fd_50F6_07BC[];
extern uint8_t  fd_50F6_0F46[];
extern uint8_t  fd_50F6_0FC6[];
extern uint8_t  fd_50F6_0F84[];
extern uint8_t  fd_50F6_1008[];
extern uint8_t  fd_50F6_0256[];
extern uint8_t  fd_50F6_02C0[];
extern uint8_t  casteLevels[];
extern uint8_t  fd_3D57_07F2[];
extern uint8_t  modeLevels[];
extern uint8_t  fd_3D57_0810[];
extern uint8_t  fd_50F6_0AEC[];
extern uint8_t  fd_50F6_0AFA[];
extern uint8_t  fd_50F6_0334[];
extern uint8_t  fd_50F6_08F0[];
extern uint8_t  fd_50F6_0626[];
extern uint8_t  fd_50F6_073C[];
extern uint8_t  fd_50F6_0516[];
extern uint8_t  fd_50F6_0A0A[];
extern uint8_t  fd_50F6_0856[];
extern uint8_t  fd_50F6_0970[];
extern uint8_t  fd_50F6_06AE[];
extern uint8_t  fd_50F6_07CE[];
extern uint8_t  fd_50F6_05A0[];
extern uint8_t  IdealCaste[];
extern uint8_t  fd_50F6_0B12[];
extern uint8_t  fd_50F6_0C2A[];
extern uint8_t  fd_3D57_087A[];
extern uint8_t  fd_3D57_07A8[];
extern uint8_t  fd_3D57_0C30[];
extern uint8_t  fd_3D57_0C32[];
extern uint8_t  fd_3D57_0C28[];
extern uint8_t  fd_3D57_0C40[];
extern uint8_t  fd_3D57_0C34[];
extern uint8_t  fd_3D57_0C2A[];
extern uint8_t  fd_3D57_0C2C[];
extern uint8_t  fd_3D57_0C2E[];
extern uint8_t  fd_3D57_0C1E[];
extern uint8_t  fd_3D57_0C20[];
extern uint8_t  fd_3D57_0C3E[];
extern uint8_t  fd_3D57_0828[];
extern uint8_t  fd_3D57_02C0[];
extern uint8_t  LionIndex[];
extern uint8_t  fd_3D57_0C0E[];
extern uint8_t  fd_3D57_07C8[];
extern uint8_t  fd_3D57_0C22[];
extern uint8_t  fd_3D57_0C26[];
extern uint8_t  fd_3D57_0C24[];
extern uint8_t  ModeMe[];
extern uint8_t  fd_3D57_0C46[];
extern uint8_t  fd_3D57_0C48[];
extern uint8_t  PillarState[];
extern uint8_t  PillarX[];
extern uint8_t  PillarY[];
extern uint8_t  fd_3D57_07A6[];
extern uint8_t  fd_3D57_07A4[];
extern uint8_t  fd_3D57_07A2[];
extern uint8_t  fd_3D57_0C18[];
extern uint8_t  CasteAuto[];
extern uint8_t  fd_3D57_0C42[];
extern uint8_t  fd_3D57_0C44[];
extern uint8_t  fd_3D57_0C14[];
extern uint8_t  fd_3D57_0C16[];
extern uint8_t  fd_3D57_0C12[];
extern uint8_t  fd_3D57_07EA[];

struct SaveRec  fd_4E4B_0000[308] = {
    { 1, 10, (void  *)&native_state_LionListM.values },
    { 1, 10, (void  *)&native_state_LionListS.values },
    { 1, 10, (void  *)&native_state_LionListT.values },
    { 1, 10, (void  *)&native_state_LionListX.values },
    { 1, 10, (void  *)&native_state_LionListY.values },
    { 2, 6, (void  *)&native_state_PillarMap.raw_bytes },
    { 2, 3, (void  *)&native_state_SowDir.raw_bytes },
    { 2, 3, (void  *)&native_state_SowSave.raw_bytes },
    { 2, 3, (void  *)&native_state_SowX.raw_bytes },
    { 2, 3, (void  *)&native_state_SowY.raw_bytes },
    { 2, 1, (void  *)&native_state_Cycle.raw_bytes },
    { 2, 1, (void  *)&native_state_ListIndexB.signed_value },
    { 2, 1, (void  *)&native_state_ListIndexR.signed_value },
    { 0, 0, 0 },
};

/* FileSelect: STEERED folded unsigned path, save-mode and index reads reproduce
 * the local use ordering and CMP operands. The original eliminated expressions
 * are unknown. USE-2 retains whole-module positive and independent negatives. */

#pragma pack(pop)
