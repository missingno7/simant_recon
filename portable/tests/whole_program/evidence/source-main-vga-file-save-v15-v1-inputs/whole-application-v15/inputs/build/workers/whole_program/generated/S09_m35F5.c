#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/dos_files.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#include "portable/whole_program/platform/crt_abi.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

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
extern void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) ;
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

/* file selector: returns 1 with the chosen path in name, 0 when cancelled */
int16_t  FileSelect(char  *name, char  *title, char  *verb, int16_t save)
{
    char buf[80];
    char  *list;
    char path[67];
    struct find_t ff;
    Handle h;
    struct Event ev;
    char fname[14];
    int16_t x;
    int16_t y;
    struct Rect r3;
    struct Rect r2;
    struct Rect r;
    int16_t nDirs;
    int16_t oldDrive;
    int16_t sel;
    char  *p;
    char  *best;
    char  *q;
    int16_t count;
    int16_t i;
    int16_t nFiles;
    int16_t n;
    int16_t j;
    char ok;
    int16_t key;
    int16_t tmp2;

    oldDrive = 0;
    ok = 1;
    sel = -1;
    dos_chdir(lastDir);
    if (s_2966 == 0)
        s_2966 = fd_50F6_38B6;
    if (*name != 0 && f_1F66_00AF(s_2966 - '@', path) != 0) {
        if (path[_fstrlen(path) - 1] != '\\')
            _fstrcat(path, "\\");
        dos_sprintf(buf, "%s%s", path, name);
        _fstrcpy(name, buf);
    }
    h = f_171C_13CA(0xC80L, 0, "File list");
    list = *h;
    _fmemset(list, 0, 4);
    win_LockWin(0x1600);
    win_SetObjFormatStr(0x1613, verb);
    win_SetObjFormatStr(0x1601, title);
    f_22BF_00AA(0x1602, &r);
    if (save != 1) {
        win_MakeGroupUnselectable(0x1600, 5);
        win_MakeGroupInvisible(0x1600, 5);
        r2 = r;
        r2.bottom = 0;
        f_22BF_00DD(0x1602, &r2);
    } else {
        win_MakeGroupSelectable(0x1600, 5);
        win_MakeGroupVisible(0x1600, 5);
    }
    win_Open(0x1600, 0, 0, 0, 0, 0);
redraw:
    if (save == 1)
        win_DrawObjectNum(0x1603);
    *name = fname[0] = 0;
    nDirs = nFiles = 0;
    if (f_1F66_00AF(s_2966 - '@', path) == 0) {
retry:
        dos_sprintf(buf, "Cannot read drive %c", s_2966);
        f_1C62_00AC(buf);
        s_2966 = oldDrive;
        if ((s_2966 == 0 || f_1F66_00AF(s_2966 - '@', path) == 0) && ((uint16_t)save >= 0)) {
            if (fd_50F6_38B6 == s_2966)
                f_1C62_00AC("Can't read disk\nAborting");
            dos_sprintf(buf, "Cannot read drive %c", s_2966);
            f_1C62_00AC(buf);
            oldDrive = fd_50F6_38B6;
            goto retry;
        }
    }
    win_MakeObjSelected(s_2966 + 0x15CA);
    WinPrintf("\n<PATH=%s>", path);
    oldDrive = s_2966;
    count = 0;
    p = list;
    if (path[_fstrlen(path) - 1] != '\\')
        _fstrcat(path, "\\");
    dos_sprintf(buf, "%s*.*", path);
    f_208F_005B(0x1606, "", 0, 0);
    f_22BF_0C38(0x1606);
    f_208F_005B(0x1606, path, 4, 0);
    if (save == 1) {
        win_GetObjRect(0x1603, &r3);
        tmp2 = r3.top;
        y = (r3.bottom + tmp2 - f_24AB_030B() + 1) / 2;
        x = r3.left + 4;
        win_SetColorFromObjNum(0x1604);
        if (ok && *fd_50F6_3862 != 0) {
            _fstrcpy(name, _fstrrchr(fd_50F6_3862, '\\') + 1);
            f_1FBD_0000(x, y, name);
        }
    }
    if (_dos_findfirst(buf, _A_SUBDIR, &ff) == 0)
        goto first;
    while (_dos_findnext(&ff) == 0) {
first:
        if (count >= 200 - s_2968)
            break;
        if (ff.attrib & _A_SUBDIR) {
            if (_fstrcmp(ff.name, "..") == 0)
                _fstrcpy(p + 1, "\1..>");
            else {
                if (_fstrcmp(ff.name, ".") == 0)
                    continue;
                dos_sprintf(p + 1, "\1%s>", ff.name);
            }
            nDirs++;
            *p = '0';
            p += 16;
        } else {
            _fstrlen(ff.name);
            if (f_1F66_002D("*.ant", ff.name) == 0)
                continue;
            nFiles++;
            *p++ = '0';
            dos_sprintf(p, "%-12s", ff.name);
            p += 15;
        }
        count++;
    }
    *p = 0;
    if (count == 0) {
        _fstrcpy(p, "0No Files");
        p[_fstrlen(p) + 1] = 0;
    } else {
        for (p = list, i = 0; i < count; i++, p += 16) {
            best = p;
            for (q = p + 16, j = i + 1; j < count; j++, q += 16)
                if (_fmemcmp(best, q, 16) > 0)
                    best = q;
            if (p != best)
                f_1F58_0017(p, best, 16);
        }
    }
    p = q = list;
    for (i = 0; i < count; i++) {
        WinPrintf("\n%d:%s", i, q);
        if (q[1] == 1)
            q[1] = '<';
        _fstrcpy(p, q);
        WinPrintf(" -> %s", p);
        p += _fstrlen(p) + 1;
        q += 16;
    }
    *p = 0;
    f_23E6_0266(0x1609, *h);
    win_DrawObjectNum(0x1609);
    win_DrawObjectNum(0x1608);
    for (;;) {
        if (f_1F58_0038() && ((uint16_t)path >= 0)) {
            key = f_1F58_0090();
            if (!(key & 0x800) && isalnum(key) && save == 1) {
                g_2970 = key;
                goto edit;
            }
            switch (key) {
            case 0x0D:
                goto accept;
            case 0x1B:
                goto cancel;
            }
        }
        if (!win_GetEvent(&ev))
            continue;
        WinPrintf("\nEvent=%x,%x", ev.code, ev.modifiers);
        if (ev.code >= 0x160B && ev.code <= 0x1612)
            goto drive;
        switch (ev.code) {
        case 0x1604:
edit:
            f_23E6_016B(0x1609);
            win_DrawObjectNum(0x1603);
            win_SetColorFromObjNum(0x1604);
            o09_36EE_0092(x, y, name, 9, 0);
            break;
        case 0x1613:
            goto accept;
        case 0x1614:
            goto cancel;
        default:
            WinPrintf("\nDEFAULT:Event=%x,%x", ev.code, ev.modifiers);
            if (ev.code == 0x1609) {
                if (ev.modifiers & 0x0A00) {
                    n = f_23E6_0109(0x1609);
                    sel = -1;
                    for (i = 0; i < n; i++)
                        if (f_23E6_009F(0x1609, i)) {
                            sel = i;
                            break;
                        }
                    if (*name != 0) {
                        *name = 0;
                        if (save == 1)
                            win_DrawObjectNum(0x1604);
                        break;
                    }
                }
                if (ev.modifiers & 0x6000) {
                    n = f_23E6_0109(0x1609);
                    for (i = 0; i < n; i++)
                        if (f_23E6_009F(0x1609, i)) {
                            if ((i == sel) && ((uint16_t)i >= 0))
                                goto accept;
                            break;
                        }
                }
            }
            break;
        }
        continue;
accept:
        if (*name != 0)
            goto done;
        n = f_23E6_0109(0x1609);
        for (i = 0; i < n; i++)
            if (f_23E6_009F(0x1609, i)) {
                _fstrcpy(name, f_23E6_0132(0x1609, i) + 1);
                break;
            }
        if (*name == 0)
            continue;
        if (i >= nDirs)
            goto done;
        dos_sprintf(buf, "%c:%s", s_2966, name + 1);
        buf[_fstrlen(buf) - 1] = 0;
        WinPrintf("\nCHDIR(%s)", buf);
        dos_chdir(buf);
        ok = *name = 0;
        goto redraw;
drive:
        s_2966 = ev.code - 0x15CA;
        ok = *name = 0;
        goto redraw;
    }
cancel:
    *name = ok = 0;
    goto dos_close;
done:
    ok = 1;
dos_close:
    win_Close(0x1600);
    f_22BF_00DD(0x1602, &r);
    win_UnlockWin(0x1600);
    if (*name != 0) {
        WinPrintf("\nFilename:%s", name);
        o09_35F5_0D2B(name);
        WinPrintf("->%s", name);
    }
    f_171C_13E4(h);
    _fstrcpy(lastDir, path);
    _fstrcpy(buf, name);
    dos_sprintf(name, "%s%s", path, buf);
    dos_chdir(fd_50F6_38B2);
    WinPrintf("\nPathName=%s, iniPath=%s", name, fd_50F6_38B2);
    return ok;
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
extern uint8_t  fd_3D57_02B4[];
extern uint8_t  fd_3D57_02BC[];
extern uint8_t  fd_3D57_02A4[];
extern uint8_t  fd_3D57_02A8[];
extern uint8_t  fd_3D57_02AC[];
extern uint8_t  fd_3D57_02B0[];
extern uint8_t  fd_3D57_02B8[];
extern uint8_t  fd_3D57_07F2[];
extern uint8_t  fd_3D57_0810[];
extern uint8_t  IdealCaste[];
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
    { 1, 8192, (void  *)&MapA },
    { 1, 4096, (void  *)&MapB },
    { 1, 4096, (void  *)&MapR },
    { 1, 4096, (void  *)&ExitMapB },
    { 1, 4096, (void  *)&ExitMapR },
    { 1, 1000, (void  *)&AlistX },
    { 1, 1000, (void  *)&AlistY },
    { 1, 1000, (void  *)&AlistM },
    { 1, 1000, (void  *)&AlistT },
    { 1, 1000, (void  *)&AlistS },
    { 1, 500, (void  *)&BlistX },
    { 1, 500, (void  *)&BlistY },
    { 1, 500, (void  *)&BlistM },
    { 1, 500, (void  *)&BlistT },
    { 1, 500, (void  *)&BlistS },
    { 1, 500, (void  *)&RlistX },
    { 1, 500, (void  *)&RlistY },
    { 1, 500, (void  *)&RlistM },
    { 1, 500, (void  *)&RlistT },
    { 1, 500, (void  *)&RlistS },
    { 1, 2048, (void  *)&PherMapA },
    { 1, 2048, (void  *)&PherMapBN },
    { 1, 2048, (void  *)&PherMapBT },
    { 1, 2048, (void  *)&PherMapRN },
    { 1, 2048, (void  *)&PherMapRT },
    { 1, 64, (void  *)&HoleMapB },
    { 1, 64, (void  *)&HoleMapR },
    { 1, 192, (void  *)&fd_3D57_00A4 },
    { 1, 192, (void  *)&fd_3D57_0164 },
    { 2, 192, (void  *)&fd_3E1D_0000 },
    { 4, 1, (void  *)&native_state_BAntsEaten.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0F30.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0EFC.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_107E.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_109C.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0220.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0736.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0C26.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0ADA.raw_bytes },
    { 4, 1, (void  *)&native_state_RAntsEaten.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0FBC.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0F3E.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_1068.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_108E.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_1082.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_10A2.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_1000.raw_bytes },
    { 4, 1, (void  *)&native_state_fd_50F6_0FC2.raw_bytes },
    { 4, 1, (void  *)&native_sim_state_fd_50F6_0596.raw_bytes },
    { 4, 1, (void  *)&native_sim_state_fd_50F6_06A6.raw_bytes },
    { 4, 1, (void  *)&native_sim_state_fd_50F6_07CA.raw_bytes },
    { 4, 1, (void  *)&fd_3D57_02B4 },
    { 4, 1, (void  *)&fd_3D57_02BC },
    { 4, 1, (void  *)&fd_3D57_02A4 },
    { 4, 1, (void  *)&fd_3D57_02A8 },
    { 4, 1, (void  *)&fd_3D57_02AC },
    { 4, 1, (void  *)&fd_3D57_02B0 },
    { 4, 1, (void  *)&fd_3D57_02B8 },
    { 4, 1, (void  *)&native_sim_state_fd_50F6_0508.raw_bytes },
    { 4, 1, (void  *)&native_sim_state_fd_50F6_072E.raw_bytes },
    { 4, 1, (void  *)&native_sim_state_fd_50F6_07BC.raw_bytes },
    { 1, 50, (void  *)&native_sim_state_fd_50F6_0F46.unsigned_values },
    { 1, 50, (void  *)&native_sim_state_fd_50F6_0FC6.unsigned_values },
    { 1, 50, (void  *)&native_sim_state_fd_50F6_0F84.unsigned_values },
    { 1, 50, (void  *)&native_sim_state_fd_50F6_1008.unsigned_values },
    { 1, 100, (void  *)&fd_50F6_037C },
    { 1, 100, (void  *)&fd_50F6_0404 },
    { 1, 10, (void  *)&native_state_LionListM.values },
    { 1, 10, (void  *)&native_state_LionListS.values },
    { 1, 10, (void  *)&native_state_LionListT.values },
    { 1, 10, (void  *)&native_state_LionListX.values },
    { 1, 10, (void  *)&native_state_LionListY.values },
    { 1, 100, (void  *)&native_sim_state_fd_50F6_0256.unsigned_values },
    { 1, 100, (void  *)&native_sim_state_fd_50F6_02C0.unsigned_values },
    { 2, 3, (void  *)&native_sim_state_casteLevels.raw_bytes },
    { 2, 12, (void  *)&fd_3D57_07F2 },
    { 2, 3, (void  *)&native_sim_state_modeLevels.raw_bytes },
    { 2, 12, (void  *)&fd_3D57_0810 },
    { 2, 6, (void  *)&native_sim_state_fd_50F6_0AEC.raw_bytes },
    { 2, 6, (void  *)&native_sim_state_fd_50F6_0AFA.raw_bytes },
    { 2, 12, (void  *)&native_sim_state_fd_50F6_0334.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_08F0.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_0626.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_073C.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_0516.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_0A0A.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_0856.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_0970.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_06AE.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_07CE.raw_bytes },
    { 2, 64, (void  *)&native_sim_state_fd_50F6_05A0.raw_bytes },
    { 2, 4, (void  *)&IdealCaste },
    { 2, 6, (void  *)&native_sim_state_fd_50F6_0B12.raw_bytes },
    { 2, 6, (void  *)&native_sim_state_fd_50F6_0C2A.raw_bytes },
    { 2, 6, (void  *)&native_state_PillarMap.raw_bytes },
    { 2, 3, (void  *)&native_state_SowDir.raw_bytes },
    { 2, 3, (void  *)&native_state_SowSave.raw_bytes },
    { 2, 3, (void  *)&native_state_SowX.raw_bytes },
    { 2, 3, (void  *)&native_state_SowY.raw_bytes },
    { 2, 10, (void  *)(fd_3D57_087A + 20) },
    { 2, 6, (void  *)&fd_3D57_07A8 },
    { 2, 1, (void  *)&native_state_AntsEatenByLions.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0A9E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0A90.raw_bytes },
    { 2, 1, (void  *)&native_state_Barrier.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_108C.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0208.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0210.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_10A0.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_10AC.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_10BA.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_09FA.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_035E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0FFE.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C30 },
    { 2, 1, (void  *)&fd_3D57_0C32 },
    { 2, 1, (void  *)&fd_3D57_0C28 },
    { 2, 1, (void  *)&native_state_fd_50F6_10B0.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_10BC.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0246.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_023E.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C40 },
    { 2, 1, (void  *)&fd_3D57_0C34 },
    { 2, 1, (void  *)&fd_3D57_0C2A },
    { 2, 1, (void  *)&fd_3D57_0C2C },
    { 2, 1, (void  *)&fd_3D57_0C2E },
    { 2, 1, (void  *)&native_state_BpopT.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_022C.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0240.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0244.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0254.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_02BE.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_032C.raw_bytes },
    { 2, 1, (void  *)&native_state_ChaseSpid.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C1E },
    { 2, 1, (void  *)&native_state_fd_50F6_03E2.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0400.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C20 },
    { 2, 1, (void  *)&native_state_fd_50F6_0D70.raw_bytes },
    { 2, 1, (void  *)&native_state_CurExpTool.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_105E.raw_bytes },
    { 2, 1, (void  *)&fd_50F6_0EAC },
    { 2, 1, (void  *)&native_state_Cycle.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0476.raw_bytes },
    { 2, 1, (void  *)&native_state_DeathCnt.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0506.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04E4.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0510.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_059E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0624.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04BE.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04C6.raw_bytes },
    { 2, 1, (void  *)&native_state_EatCnt.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0212.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0226.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_08DC.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_08E8.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1040.raw_bytes },
    { 2, 1, (void  *)&native_state_FoodB.raw_bytes },
    { 2, 1, (void  *)&native_state_FoodR.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C3E },
    { 2, 1, (void  *)&native_state_fd_50F6_03E0.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_046A.raw_bytes },
    { 2, 1, (void  *)&native_state_FuzLocX.raw_bytes },
    { 2, 1, (void  *)&native_state_FuzLocY.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_047E.raw_bytes },
    { 2, 1, (void  *)(uint8_t  *)fd_3D57_07CC },
    { 2, 1, (void  *)&native_state_HealthB.raw_bytes },
    { 2, 1, (void  *)&native_state_HealthR.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0828 },
    { 2, 1, (void  *)&native_state_fd_50F6_04F4.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0478.raw_bytes },
    { 2, 1, (void  *)&native_state_InitialLions.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0504.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0488.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0492.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0228.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_02C0 },
    { 2, 1, (void  *)&native_state_fd_50F6_1074.raw_bytes },
    { 2, 1, (void  *)&LionIndex },
    { 2, 1, (void  *)&ListIndexA },
    { 2, 1, (void  *)&native_state_ListIndexB.signed_value },
    { 2, 1, (void  *)&native_state_ListIndexR.signed_value },
    { 2, 1, (void  *)&fd_3D57_0C0E },
    { 2, 1, (void  *)&fd_3D57_07C8 },
    { 2, 1, (void  *)&native_state_MapPlane.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_049A.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0A8E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04E2.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0D6C.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0EF8.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0EFA.raw_bytes },
    { 2, 1, (void  *)&fd_50F6_0496 },
    { 2, 1, (void  *)&native_state_fd_50F6_0B1E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0502.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C22 },
    { 2, 1, (void  *)&fd_3D57_0C26 },
    { 2, 1, (void  *)&native_state_fd_50F6_0AF8.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0AD6.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0AE8.raw_bytes },
    { 2, 1, (void  *)&native_state_MeHealth.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1006.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0AB6.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0AC6.raw_bytes },
    { 2, 1, (void  *)&MeLocX },
    { 2, 1, (void  *)&MeLocY },
    { 2, 1, (void  *)&fd_50F6_0A06 },
    { 2, 1, (void  *)&native_state_fd_50F6_0AA0.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C24 },
    { 2, 1, (void  *)&MePlane },
    { 2, 1, (void  *)&native_state_fd_50F6_0C38.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_06AC.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04C4.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0C3E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_07C0.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_084E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_08DA.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_08E2.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_09F0.raw_bytes },
    { 2, 1, (void  *)&fd_50F6_04C2 },
    { 2, 1, (void  *)&native_state_fd_50F6_0FBA.raw_bytes },
    { 2, 1, (void  *)&ModeMe },
    { 2, 1, (void  *)&native_state_fd_50F6_0470.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_047A.raw_bytes },
    { 2, 1, (void  *)(uint8_t  *)fd_3D57_0C1A },
    { 2, 1, (void  *)&fd_3D57_0C46 },
    { 2, 1, (void  *)&fd_3D57_0C48 },
    { 2, 1, (void  *)&native_state_fd_50F6_0332.raw_bytes },
    { 2, 1, (void  *)&native_state_PillDir.raw_bytes },
    { 2, 1, (void  *)&native_state_PillarSeg.raw_bytes },
    { 2, 1, (void  *)&PillarState },
    { 2, 1, (void  *)&PillarX },
    { 2, 1, (void  *)&PillarY },
    { 2, 1, (void  *)&native_state_fd_50F6_07C8.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0850.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0AC8.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0AC4.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0356.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0352.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0F0E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0F26.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04E0.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04F2.raw_bytes },
    { 2, 1, (void  *)&native_state_RedLocX.raw_bytes },
    { 2, 1, (void  *)&native_state_RedLocY.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0A00.raw_bytes },
    { 2, 1, (void  *)&native_state_RedPlane.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_036C.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_04A4.raw_bytes },
    { 2, 1, (void  *)&native_state_RpopT.raw_bytes },
    { 2, 1, (void  *)&native_state_SCorpseBase.raw_bytes },
    { 2, 1, (void  *)&native_state_SMode.raw_bytes },
    { 2, 1, (void  *)&native_state_Scycle2.raw_bytes },
    { 2, 1, (void  *)&native_state_Scycle.raw_bytes },
    { 2, 1, (void  *)&native_state_SpidBurpCnt.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1004.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0F0C.raw_bytes },
    { 2, 1, (void  *)&native_state_SpidRevenge.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0F12.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0F34.raw_bytes },
    { 2, 1, (void  *)&native_state_Starg.raw_bytes },
    { 2, 1, (void  *)&native_state_StargLife.raw_bytes },
    { 2, 1, (void  *)&native_state_StrategicModeB.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_10A6.raw_bytes },
    { 2, 1, (void  *)&native_state_SuserX.raw_bytes },
    { 2, 1, (void  *)&native_state_SuserY.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_103C.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1048.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_06AA.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_073A.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_105C.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1066.raw_bytes },
    { 2, 1, (void  *)&TERRAINset },
    { 2, 1, (void  *)&native_state_fd_50F6_10B2.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0200.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_10C0.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_020E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0224.raw_bytes },
    { 2, 1, (void  *)&native_state_TilesDugR.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_07A6 },
    { 2, 1, (void  *)&native_state_fd_50F6_10B8.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_07A4 },
    { 2, 1, (void  *)&fd_3D57_07A2 },
    { 2, 1, (void  *)&native_state_fd_50F6_0242.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_07C2.raw_bytes },
    { 2, 1, (void  *)&native_state_YardMode.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0F44.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_024E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0370.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C18 },
    { 2, 1, (void  *)&native_state_fd_50F6_0202.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_0366.raw_bytes },
    { 2, 1, (void  *)&CasteAuto },
    { 2, 1, (void  *)&fd_3D57_0C42 },
    { 2, 1, (void  *)&fd_3D57_0C44 },
    { 2, 1, (void  *)&native_state_fd_50F6_0376.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C14 },
    { 2, 1, (void  *)&fd_50F6_0354 },
    { 2, 1, (void  *)&native_state_fd_50F6_104E.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1058.raw_bytes },
    { 2, 1, (void  *)&native_state_fd_50F6_1044.raw_bytes },
    { 2, 1, (void  *)&native_state_ModeAuto.raw_bytes },
    { 2, 1, (void  *)&fd_3D57_0C16 },
    { 2, 1, (void  *)(uint8_t  *)&fd_3D57_0C1A[1] },
    { 2, 1, (void  *)&fd_3D57_0C12 },
    { 2, 1, (void  *)&fd_3D57_07EA },
    { 2, 1, (void  *)&native_state_fd_50F6_0468.raw_bytes },
    { 0, 0, 0 }
};

/* FileSelect: STEERED folded unsigned path, save-mode and index reads reproduce
 * the local use ordering and CMP operands. The original eliminated expressions
 * are unknown. USE-2 retains whole-module positive and independent negatives. */

#pragma pack(pop)
