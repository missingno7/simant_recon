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
    int size;
    int count;
    void far *data;
};

extern int far fd_3D57_02C2;
extern int far fd_50F6_0EAC;
extern int far fd_3D57_07AA;
extern char far fd_50F6_3862[];
extern struct SaveRec far fd_4E4B_0000[];

extern int far o15_384C_0239(int a);
extern void far f_1C62_00AC(char far *msg);
extern int far f_1C62_0415(char far *msg, int a);
extern void far f_1C62_00C0(char far *msg);
extern void far f_15D9_009C(void far *p, long a, int b);
extern void far o11_35F5_0000(void);
extern void far o11_35F5_0088(int a);
extern void far StopSong(void);
extern void far WinPrintf(char far *fmt, ...);

extern int far fd_50F6_0354;
extern long far fd_50F6_0214;
extern long far fd_50F6_0204;
extern long far fd_50F6_0472;
extern void far RandYard(void);
extern int far TERRAINset;
extern int far CurGndTileID;
extern void far OverlayTileSet(int type, int id);
extern unsigned char far LifeA[128][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far LifeR[64][64];
extern int far ListIndexA;
extern unsigned char far AlistT[];
extern unsigned char far AlistX[];
extern unsigned char far AlistY[];
extern int far ListIndexB;
extern unsigned char far BlistT[];
extern unsigned char far BlistX[];
extern unsigned char far BlistY[];
extern int far ListIndexR;
extern unsigned char far RlistT[];
extern unsigned char far RlistX[];
extern unsigned char far RlistY[];
extern int far fd_50F6_0A06;
extern int far fd_50F6_0496;
extern int far fd_50F6_04C2;
extern int far MeLocY;
extern int far MeLocX;
extern int far MePlane;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int life);
extern void far FullCount(void);
extern void far o15_384C_037F(void);
extern void far f_0250_0FC4(int x, int y);
extern void far SetDefaultWindPrompt(int mode);

int far o09_35F5_0188(int useLast);
int far o09_35F5_03C6(char far *name, char far *title, char far *verb, int save);
void far o09_35F5_0D7A(void);
void far o09_35F5_0DBB(void);
void far o09_35F5_0D2B(char far *name);

/* 128-byte MacBinary-style header written in front of a saved game */
unsigned char g_2776[128] = {
    0x00, 0x0d, 0x43, 0x49, 0x54, 0x59, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x43, 0x49, 0x54, 0x59, 0x4d, 0x43, 0x52, 0x50, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x88, 0x00, 0x00, 0x00, 0x69, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x9f, 0xe5, 0xe4, 0x00, 0x9f,
    0xf2, 0x69, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

int far LoadGame(void)
{
    struct SaveRec far *p;
    char ok;
    int fd;
    char name[100];
    register int n;
    register int r;

    ok = 0;
    if (fd_3D57_02C2 != 0) {
        do {
            r = o15_384C_0239(0);
            if (r == 2)
                return 0;
        } while (r == 1 && o09_35F5_0188(0) == 0);
    }
    if (o09_35F5_03C6(name, "Load Game", "LOAD", 0) != 0) {
        _fstrcpy(fd_50F6_3862, name);
        fd_3D57_02C2 = 0;
        fd = open(name, O_RDONLY | O_BINARY);
        if (fd <= 0)
            f_1C62_00AC(sys_errlist[errno]);
        else {
            n = 0;
            for (p = fd_4E4B_0000; p->count != 0; p++)
                n += p->count * p->size;
            o09_35F5_0D7A();
            for (p = fd_4E4B_0000; p->count != 0; p++) {
                if ((r = read(fd, p->data, n = p->count * p->size)) != n) {
                    f_1C62_00AC("  Read error  \ngame not loaded");
                    fd_50F6_0EAC = -1;
                    goto done;
                }
            }
            ok = 1;
            f_15D9_009C(0L, -2L, 1);
done:
            close(fd);
        }
        if (ok) {
            o11_35F5_0000();
            o11_35F5_0088(1);
            o09_35F5_0DBB();
            if (fd_3D57_07AA == 0)
                StopSong();
        }
    }
    return ok;
}

/* SaveGame */
int far o09_35F5_0188(int useLast)
{
    struct SaveRec far *p;
    int fd;
    char name[100];
    char msg[100];
    int ok;
    int total;

    ok = 0;
    if (fd_50F6_3862 != 0L && *fd_50F6_3862 != 0 && useLast != 0) {
        _fstrcpy(name, fd_50F6_3862);
        goto tryit;
    }
select:
    if (o09_35F5_03C6(name, "Save Game", "SAVE", 1) == 0)
        goto done;
    _fstrcpy(fd_50F6_3862, name);
    WinPrintf("\nlastFileName==%s", fd_50F6_3862);
tryit:
    fd = open(name, O_RDWR | O_BINARY);
    if (fd > 0) {
        sprintf(msg, "OVERWRITE\n%s", name);
        if (f_1C62_0415(msg, 0) == 0)
            goto write;
        close(fd);
        goto select;
    }
    fd = open(name, O_RDWR | O_CREAT | O_TRUNC | O_BINARY, S_IREAD | S_IWRITE);
    if (fd <= 0) {
        f_1C62_00AC(sys_errlist[errno]);
        *fd_50F6_3862 = 0;
        goto done;
    }
write:
    total = 0;
    for (p = fd_4E4B_0000; p->count != 0; p++) {
        total += p->count * p->size;
        WinPrintf("\nTOTALLEN=%u", total);
    }
    WinPrintf("\nCOPYING DATA INTO BUFFER!");
    for (p = fd_4E4B_0000; p->count != 0; p++) {
        if (write(fd, p->data, p->count * p->size) == -1) {
            *fd_50F6_3862 = 0;
            f_1C62_00AC(sys_errlist[errno]);
            close(fd);
            remove(name);
            return 0;
        }
    }
    WinPrintf("\nWRITING");
    fd_3D57_02C2 = 0;
    sprintf(msg, "%s\nSaved correctly", name);
    f_1C62_00C0(msg);
    _fstrcpy(fd_50F6_3862, name);
    ok = 1;
    close(fd);
done:
    return ok;
}

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    unsigned code;
    int xE;
};

typedef char far * far *Handle;

extern int far fd_50F6_38B6;
extern char far * far fd_50F6_38B2;
extern char far g_2970;

extern int far f_1F66_00AF(int drive, char far *path);
extern Handle far f_171C_13CA(long size, int flags, char far *name);
extern void far f_171C_13E4(Handle h);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_UnlockWin(int win);
extern void far win_SetObjFormatStr(int obj, ...);
extern void _fastcall f_22BF_00AA(int obj, struct Rect far *r);
extern void _fastcall f_22BF_00DD(int obj, struct Rect far *r);
extern void _fastcall win_MakeGroupUnselectable(int win, int group);
extern void _fastcall win_MakeGroupInvisible(int win, int group);
extern void _fastcall win_MakeGroupSelectable(int win, int group);
extern void _fastcall win_MakeGroupVisible(int win, int group);
extern void far win_Open(int win);
extern void _fastcall win_Close(int win);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void _fastcall win_MakeObjSelected(int obj);
extern void far f_208F_005B(int obj, char far *text, int dx, int dy);
extern void far f_22BF_0C38(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far f_24AB_030B(void);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far f_1FBD_0000(int x, int y, char far *text);
extern int far f_1F66_002D(char far *pattern, char far *name);
extern void far f_1F58_0017(void far *a, void far *b, unsigned n);
extern void _fastcall f_23E6_0266(int obj, char far *text);
extern int far f_1F58_0038(void);
extern int far f_1F58_0090(void);
extern void _fastcall f_23E6_016B(int obj);
extern void far o09_36EE_0092(int x, int y, char far *text, int maxLen, int flags);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern int _fastcall f_23E6_0109(int obj);
extern int _fastcall f_23E6_009F(int obj, int line);
extern char far * _fastcall f_23E6_0132(int obj, int line);


static int s_2966 = 0;
static int s_2968 = 0;
static char lastDir[67];
static char oneFloppy;

/* file selector: returns 1 with the chosen path in name, 0 when cancelled */
int far o09_35F5_03C6(char far *name, char far *title, char far *verb, int save)
{
    char buf[80];
    char far *list;
    char path[67];
    struct find_t ff;
    Handle h;
    struct Event ev;
    char fname[14];
    int x;
    int y;
    struct Rect r3;
    struct Rect r2;
    struct Rect r;
    int nDirs;
    int oldDrive;
    int sel;
    char far *p;
    char far *best;
    char far *q;
    int count;
    int i;
    int nFiles;
    int n;
    int j;
    char ok;
    int key;
    int tmp2;

    oldDrive = 0;
    ok = 1;
    sel = -1;
    chdir(lastDir);
    if (s_2966 == 0)
        s_2966 = fd_50F6_38B6;
    if (*name != 0 && f_1F66_00AF(s_2966 - '@', path) != 0) {
        if (path[_fstrlen(path) - 1] != '\\')
            _fstrcat(path, "\\");
        sprintf(buf, "%s%s", path, name);
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
    win_Open(0x1600);
redraw:
    if (save == 1)
        win_DrawObjectNum(0x1603);
    *name = fname[0] = 0;
    nDirs = nFiles = 0;
    oneFloppy = (*(unsigned char far *)0x00000410L & 0xC0) == 0;
    if (s_2966 == 'B' && oneFloppy)
        s_2966 = 'A';
    if (f_1F66_00AF(s_2966 - '@', path) == 0) {
retry:
        sprintf(buf, "Cannot read drive %c", s_2966);
        f_1C62_00AC(buf);
        s_2966 = oldDrive;
        if (s_2966 == 0 || f_1F66_00AF(s_2966 - '@', path) == 0) {
            if (fd_50F6_38B6 == s_2966)
                f_1C62_00AC("Can't read disk\nAborting");
            sprintf(buf, "Cannot read drive %c", s_2966);
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
    sprintf(buf, "%s*.*", path);
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
                sprintf(p + 1, "\1%s>", ff.name);
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
            sprintf(p, "%-12s", ff.name);
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
        if (f_1F58_0038() && ((unsigned)path >= 0)) {
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
                            if (i == sel)
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
        sprintf(buf, "%c:%s", s_2966, name + 1);
        buf[_fstrlen(buf) - 1] = 0;
        WinPrintf("\nCHDIR(%s)", buf);
        chdir(buf);
        ok = *name = 0;
        goto redraw;
drive:
        s_2966 = ev.code - 0x15CA;
        ok = *name = 0;
        goto redraw;
    }
cancel:
    *name = ok = 0;
    goto close;
done:
    ok = 1;
close:
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
    sprintf(name, "%s%s", path, buf);
    chdir(fd_50F6_38B2);
    WinPrintf("\nPathName=%s, iniPath=%s", name, fd_50F6_38B2);
    return ok;
}

/* append the default extension to a file name (max. 8 characters) */
void far o09_35F5_0D2B(char far *name)
{
    int i;

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
void far o09_35F5_0D7A(void)
{
    fd_50F6_0354 = 1;
    fd_50F6_0214 = 0L;
    fd_50F6_0204 = 300L;
    fd_50F6_0472 = 0L;
    RandYard();
}

/* rebuild the life maps from the loaded lists */
void far o09_35F5_0DBB(void)
{
    int x;
    int y;
    int i;

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
    for (i = ListIndexB; i >= 0; i--)
        LifeB[BlistX[i]][BlistY[i]] = BlistT[i];
    for (i = ListIndexR; i >= 0; i--)
        LifeR[RlistX[i]][RlistY[i]] = RlistT[i];
    if (fd_50F6_0A06 == 0)
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 255);
    FullCount();
    o15_384C_037F();
    f_0250_0FC4(MeLocX, MeLocY);
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
extern unsigned char far MapA[];
extern unsigned char far MapB[];
extern unsigned char far MapR[];
extern unsigned char far ExitMapB[];
extern unsigned char far ExitMapR[];
extern unsigned char far AlistM[];
extern unsigned char far AlistS[];
extern unsigned char far BlistM[];
extern unsigned char far BlistS[];
extern unsigned char far RlistM[];
extern unsigned char far RlistS[];
extern unsigned char far PherMapA[];
extern unsigned char far PherMapBN[];
extern unsigned char far PherMapBT[];
extern unsigned char far PherMapRN[];
extern unsigned char far PherMapRT[];
extern unsigned char far HoleMapB[];
extern unsigned char far HoleMapR[];
extern unsigned char far fd_3D57_00A4[];
extern unsigned char far fd_3D57_0164[];
extern unsigned char far fd_3E1D_0000[];
extern unsigned char far BAntsEaten[];
extern unsigned char far fd_50F6_0F30[];
extern unsigned char far fd_50F6_0EFC[];
extern unsigned char far fd_50F6_107E[];
extern unsigned char far fd_50F6_109C[];
extern unsigned char far fd_50F6_0220[];
extern unsigned char far fd_50F6_0736[];
extern unsigned char far fd_50F6_0C26[];
extern unsigned char far fd_50F6_0ADA[];
extern unsigned char far RAntsEaten[];
extern unsigned char far fd_50F6_0FBC[];
extern unsigned char far fd_50F6_0F3E[];
extern unsigned char far fd_50F6_1068[];
extern unsigned char far fd_50F6_108E[];
extern unsigned char far fd_50F6_1082[];
extern unsigned char far fd_50F6_10A2[];
extern unsigned char far fd_50F6_1000[];
extern unsigned char far fd_50F6_0FC2[];
extern unsigned char far fd_50F6_0596[];
extern unsigned char far fd_50F6_06A6[];
extern unsigned char far fd_50F6_07CA[];
extern unsigned char far fd_3D57_02B4[];
extern unsigned char far fd_3D57_02BC[];
extern unsigned char far fd_3D57_02A4[];
extern unsigned char far fd_3D57_02A8[];
extern unsigned char far fd_3D57_02AC[];
extern unsigned char far fd_3D57_02B0[];
extern unsigned char far fd_3D57_02B8[];
extern unsigned char far fd_50F6_0508[];
extern unsigned char far fd_50F6_072E[];
extern unsigned char far fd_50F6_07BC[];
extern unsigned char far fd_50F6_0F46[];
extern unsigned char far fd_50F6_0FC6[];
extern unsigned char far fd_50F6_0F84[];
extern unsigned char far fd_50F6_1008[];
extern unsigned char far fd_50F6_037C[];
extern unsigned char far fd_50F6_0404[];
extern unsigned char far LionListM[];
extern unsigned char far LionListS[];
extern unsigned char far LionListT[];
extern unsigned char far LionListX[];
extern unsigned char far LionListY[];
extern unsigned char far fd_50F6_0256[];
extern unsigned char far fd_50F6_02C0[];
extern unsigned char far casteLevels[];
extern unsigned char far fd_3D57_07F2[];
extern unsigned char far modeLevels[];
extern unsigned char far fd_3D57_0810[];
extern unsigned char far fd_50F6_0AEC[];
extern unsigned char far fd_50F6_0AFA[];
extern unsigned char far fd_50F6_0334[];
extern unsigned char far fd_50F6_08F0[];
extern unsigned char far fd_50F6_0626[];
extern unsigned char far fd_50F6_073C[];
extern unsigned char far fd_50F6_0516[];
extern unsigned char far fd_50F6_0A0A[];
extern unsigned char far fd_50F6_0856[];
extern unsigned char far fd_50F6_0970[];
extern unsigned char far fd_50F6_06AE[];
extern unsigned char far fd_50F6_07CE[];
extern unsigned char far fd_50F6_05A0[];
extern unsigned char far IdealCaste[];
extern unsigned char far fd_50F6_0B12[];
extern unsigned char far fd_50F6_0C2A[];
extern unsigned char far PillarMap[];
extern unsigned char far SowDir[];
extern unsigned char far SowSave[];
extern unsigned char far SowX[];
extern unsigned char far SowY[];
extern unsigned char far fd_3D57_087A[];
extern unsigned char far fd_3D57_07A8[];
extern unsigned char far AntsEatenByLions[];
extern unsigned char far fd_50F6_0A9E[];
extern unsigned char far fd_50F6_0A90[];
extern unsigned char far Barrier[];
extern unsigned char far fd_50F6_108C[];
extern unsigned char far fd_50F6_0208[];
extern unsigned char far fd_50F6_0210[];
extern unsigned char far fd_50F6_10A0[];
extern unsigned char far fd_50F6_10AC[];
extern unsigned char far fd_50F6_10BA[];
extern unsigned char far fd_50F6_09FA[];
extern unsigned char far fd_50F6_035E[];
extern unsigned char far fd_50F6_0FFE[];
extern unsigned char far fd_3D57_0C30[];
extern unsigned char far fd_3D57_0C32[];
extern unsigned char far fd_3D57_0C28[];
extern unsigned char far fd_50F6_10B0[];
extern unsigned char far fd_50F6_10BC[];
extern unsigned char far fd_50F6_0246[];
extern unsigned char far fd_50F6_023E[];
extern unsigned char far fd_3D57_0C40[];
extern unsigned char far fd_3D57_0C34[];
extern unsigned char far fd_3D57_0C2A[];
extern unsigned char far fd_3D57_0C2C[];
extern unsigned char far fd_3D57_0C2E[];
extern unsigned char far BpopT[];
extern unsigned char far fd_50F6_022C[];
extern unsigned char far fd_50F6_0240[];
extern unsigned char far fd_50F6_0244[];
extern unsigned char far fd_50F6_0254[];
extern unsigned char far fd_50F6_02BE[];
extern unsigned char far fd_50F6_032C[];
extern unsigned char far ChaseSpid[];
extern unsigned char far fd_3D57_0C1E[];
extern unsigned char far fd_50F6_03E2[];
extern unsigned char far fd_50F6_0400[];
extern unsigned char far fd_3D57_0C20[];
extern unsigned char far fd_50F6_0D70[];
extern unsigned char far CurExpTool[];
extern unsigned char far fd_50F6_105E[];
extern unsigned char far Cycle[];
extern unsigned char far fd_50F6_0476[];
extern unsigned char far DeathCnt[];
extern unsigned char far fd_50F6_0506[];
extern unsigned char far fd_50F6_04E4[];
extern unsigned char far fd_50F6_0510[];
extern unsigned char far fd_50F6_059E[];
extern unsigned char far fd_50F6_0624[];
extern unsigned char far fd_50F6_04BE[];
extern unsigned char far fd_50F6_04C6[];
extern unsigned char far EatCnt[];
extern unsigned char far fd_50F6_0212[];
extern unsigned char far fd_50F6_0226[];
extern unsigned char far fd_50F6_08DC[];
extern unsigned char far fd_50F6_08E8[];
extern unsigned char far fd_50F6_1040[];
extern unsigned char far FoodB[];
extern unsigned char far FoodR[];
extern unsigned char far fd_3D57_0C3E[];
extern unsigned char far fd_50F6_03E0[];
extern unsigned char far fd_50F6_046A[];
extern unsigned char far FuzLocX[];
extern unsigned char far FuzLocY[];
extern unsigned char far fd_50F6_047E[];
extern unsigned char far fd_3D57_07CC[];
extern unsigned char far HealthB[];
extern unsigned char far HealthR[];
extern unsigned char far fd_3D57_0828[];
extern unsigned char far fd_50F6_04F4[];
extern unsigned char far fd_50F6_0478[];
extern unsigned char far InitialLions[];
extern unsigned char far fd_50F6_0504[];
extern unsigned char far fd_50F6_0488[];
extern unsigned char far fd_50F6_0492[];
extern unsigned char far fd_50F6_0228[];
extern unsigned char far fd_3D57_02C0[];
extern unsigned char far fd_50F6_1074[];
extern unsigned char far LionIndex[];
extern unsigned char far fd_3D57_0C0E[];
extern unsigned char far fd_3D57_07C8[];
extern unsigned char far MapPlane[];
extern unsigned char far fd_50F6_049A[];
extern unsigned char far fd_50F6_0A8E[];
extern unsigned char far fd_50F6_04E2[];
extern unsigned char far fd_50F6_0D6C[];
extern unsigned char far fd_50F6_0EF8[];
extern unsigned char far fd_50F6_0EFA[];
extern unsigned char far fd_50F6_0B1E[];
extern unsigned char far fd_50F6_0502[];
extern unsigned char far fd_3D57_0C22[];
extern unsigned char far fd_3D57_0C26[];
extern unsigned char far fd_50F6_0AF8[];
extern unsigned char far fd_50F6_0AD6[];
extern unsigned char far fd_50F6_0AE8[];
extern unsigned char far MeHealth[];
extern unsigned char far fd_50F6_1006[];
extern unsigned char far fd_50F6_0AB6[];
extern unsigned char far fd_50F6_0AC6[];
extern unsigned char far fd_50F6_0AA0[];
extern unsigned char far fd_3D57_0C24[];
extern unsigned char far fd_50F6_0C38[];
extern unsigned char far fd_50F6_06AC[];
extern unsigned char far fd_50F6_04C4[];
extern unsigned char far fd_50F6_0C3E[];
extern unsigned char far fd_50F6_07C0[];
extern unsigned char far fd_50F6_084E[];
extern unsigned char far fd_50F6_08DA[];
extern unsigned char far fd_50F6_08E2[];
extern unsigned char far fd_50F6_09F0[];
extern unsigned char far fd_50F6_0FBA[];
extern unsigned char far ModeMe[];
extern unsigned char far fd_50F6_0470[];
extern unsigned char far fd_50F6_047A[];
extern unsigned char far fd_3D57_0C1A[];
extern unsigned char far fd_3D57_0C46[];
extern unsigned char far fd_3D57_0C48[];
extern unsigned char far fd_50F6_0332[];
extern unsigned char far PillDir[];
extern unsigned char far PillarSeg[];
extern unsigned char far PillarState[];
extern unsigned char far PillarX[];
extern unsigned char far PillarY[];
extern unsigned char far fd_50F6_07C8[];
extern unsigned char far fd_50F6_0850[];
extern unsigned char far fd_50F6_0AC8[];
extern unsigned char far fd_50F6_0AC4[];
extern unsigned char far fd_50F6_0356[];
extern unsigned char far fd_50F6_0352[];
extern unsigned char far fd_50F6_0F0E[];
extern unsigned char far fd_50F6_0F26[];
extern unsigned char far fd_50F6_04E0[];
extern unsigned char far fd_50F6_04F2[];
extern unsigned char far RedLocX[];
extern unsigned char far RedLocY[];
extern unsigned char far fd_50F6_0A00[];
extern unsigned char far RedPlane[];
extern unsigned char far fd_50F6_036C[];
extern unsigned char far fd_50F6_04A4[];
extern unsigned char far RpopT[];
extern unsigned char far SCorpseBase[];
extern unsigned char far SMode[];
extern unsigned char far Scycle2[];
extern unsigned char far Scycle[];
extern unsigned char far SpidBurpCnt[];
extern unsigned char far fd_50F6_1004[];
extern unsigned char far fd_50F6_0F0C[];
extern unsigned char far SpidRevenge[];
extern unsigned char far fd_50F6_0F12[];
extern unsigned char far fd_50F6_0F34[];
extern unsigned char far Starg[];
extern unsigned char far StargLife[];
extern unsigned char far StrategicModeB[];
extern unsigned char far fd_50F6_10A6[];
extern unsigned char far SuserX[];
extern unsigned char far SuserY[];
extern unsigned char far fd_50F6_103C[];
extern unsigned char far fd_50F6_1048[];
extern unsigned char far fd_50F6_06AA[];
extern unsigned char far fd_50F6_073A[];
extern unsigned char far fd_50F6_105C[];
extern unsigned char far fd_50F6_1066[];
extern unsigned char far fd_50F6_10B2[];
extern unsigned char far fd_50F6_0200[];
extern unsigned char far fd_50F6_10C0[];
extern unsigned char far fd_50F6_020E[];
extern unsigned char far fd_50F6_0224[];
extern unsigned char far TilesDugR[];
extern unsigned char far fd_3D57_07A6[];
extern unsigned char far fd_50F6_10B8[];
extern unsigned char far fd_3D57_07A4[];
extern unsigned char far fd_3D57_07A2[];
extern unsigned char far fd_50F6_0242[];
extern unsigned char far fd_50F6_07C2[];
extern unsigned char far YardMode[];
extern unsigned char far fd_50F6_0F44[];
extern unsigned char far fd_50F6_024E[];
extern unsigned char far fd_50F6_0370[];
extern unsigned char far fd_3D57_0C18[];
extern unsigned char far fd_50F6_0202[];
extern unsigned char far fd_50F6_0366[];
extern unsigned char far CasteAuto[];
extern unsigned char far fd_3D57_0C42[];
extern unsigned char far fd_3D57_0C44[];
extern unsigned char far fd_50F6_0376[];
extern unsigned char far fd_3D57_0C14[];
extern unsigned char far fd_50F6_104E[];
extern unsigned char far fd_50F6_1058[];
extern unsigned char far fd_50F6_1044[];
extern unsigned char far ModeAuto[];
extern unsigned char far fd_3D57_0C16[];
extern unsigned char far fd_3D57_0C1C[];
extern unsigned char far fd_3D57_0C12[];
extern unsigned char far fd_3D57_07EA[];
extern unsigned char far fd_50F6_0468[];

struct SaveRec far fd_4E4B_0000[308] = {
    { 1, 8192, (void far *)&MapA },
    { 1, 4096, (void far *)&MapB },
    { 1, 4096, (void far *)&MapR },
    { 1, 4096, (void far *)&ExitMapB },
    { 1, 4096, (void far *)&ExitMapR },
    { 1, 1000, (void far *)&AlistX },
    { 1, 1000, (void far *)&AlistY },
    { 1, 1000, (void far *)&AlistM },
    { 1, 1000, (void far *)&AlistT },
    { 1, 1000, (void far *)&AlistS },
    { 1, 500, (void far *)&BlistX },
    { 1, 500, (void far *)&BlistY },
    { 1, 500, (void far *)&BlistM },
    { 1, 500, (void far *)&BlistT },
    { 1, 500, (void far *)&BlistS },
    { 1, 500, (void far *)&RlistX },
    { 1, 500, (void far *)&RlistY },
    { 1, 500, (void far *)&RlistM },
    { 1, 500, (void far *)&RlistT },
    { 1, 500, (void far *)&RlistS },
    { 1, 2048, (void far *)&PherMapA },
    { 1, 2048, (void far *)&PherMapBN },
    { 1, 2048, (void far *)&PherMapBT },
    { 1, 2048, (void far *)&PherMapRN },
    { 1, 2048, (void far *)&PherMapRT },
    { 1, 64, (void far *)&HoleMapB },
    { 1, 64, (void far *)&HoleMapR },
    { 1, 192, (void far *)&fd_3D57_00A4 },
    { 1, 192, (void far *)&fd_3D57_0164 },
    { 2, 192, (void far *)&fd_3E1D_0000 },
    { 4, 1, (void far *)&BAntsEaten },
    { 4, 1, (void far *)&fd_50F6_0F30 },
    { 4, 1, (void far *)&fd_50F6_0EFC },
    { 4, 1, (void far *)&fd_50F6_107E },
    { 4, 1, (void far *)&fd_50F6_109C },
    { 4, 1, (void far *)&fd_50F6_0220 },
    { 4, 1, (void far *)&fd_50F6_0736 },
    { 4, 1, (void far *)&fd_50F6_0C26 },
    { 4, 1, (void far *)&fd_50F6_0ADA },
    { 4, 1, (void far *)&RAntsEaten },
    { 4, 1, (void far *)&fd_50F6_0FBC },
    { 4, 1, (void far *)&fd_50F6_0F3E },
    { 4, 1, (void far *)&fd_50F6_1068 },
    { 4, 1, (void far *)&fd_50F6_108E },
    { 4, 1, (void far *)&fd_50F6_1082 },
    { 4, 1, (void far *)&fd_50F6_10A2 },
    { 4, 1, (void far *)&fd_50F6_1000 },
    { 4, 1, (void far *)&fd_50F6_0FC2 },
    { 4, 1, (void far *)&fd_50F6_0596 },
    { 4, 1, (void far *)&fd_50F6_06A6 },
    { 4, 1, (void far *)&fd_50F6_07CA },
    { 4, 1, (void far *)&fd_3D57_02B4 },
    { 4, 1, (void far *)&fd_3D57_02BC },
    { 4, 1, (void far *)&fd_3D57_02A4 },
    { 4, 1, (void far *)&fd_3D57_02A8 },
    { 4, 1, (void far *)&fd_3D57_02AC },
    { 4, 1, (void far *)&fd_3D57_02B0 },
    { 4, 1, (void far *)&fd_3D57_02B8 },
    { 4, 1, (void far *)&fd_50F6_0508 },
    { 4, 1, (void far *)&fd_50F6_072E },
    { 4, 1, (void far *)&fd_50F6_07BC },
    { 1, 50, (void far *)&fd_50F6_0F46 },
    { 1, 50, (void far *)&fd_50F6_0FC6 },
    { 1, 50, (void far *)&fd_50F6_0F84 },
    { 1, 50, (void far *)&fd_50F6_1008 },
    { 1, 100, (void far *)&fd_50F6_037C },
    { 1, 100, (void far *)&fd_50F6_0404 },
    { 1, 10, (void far *)&LionListM },
    { 1, 10, (void far *)&LionListS },
    { 1, 10, (void far *)&LionListT },
    { 1, 10, (void far *)&LionListX },
    { 1, 10, (void far *)&LionListY },
    { 1, 100, (void far *)&fd_50F6_0256 },
    { 1, 100, (void far *)&fd_50F6_02C0 },
    { 2, 3, (void far *)&casteLevels },
    { 2, 12, (void far *)&fd_3D57_07F2 },
    { 2, 3, (void far *)&modeLevels },
    { 2, 12, (void far *)&fd_3D57_0810 },
    { 2, 6, (void far *)&fd_50F6_0AEC },
    { 2, 6, (void far *)&fd_50F6_0AFA },
    { 2, 12, (void far *)&fd_50F6_0334 },
    { 2, 64, (void far *)&fd_50F6_08F0 },
    { 2, 64, (void far *)&fd_50F6_0626 },
    { 2, 64, (void far *)&fd_50F6_073C },
    { 2, 64, (void far *)&fd_50F6_0516 },
    { 2, 64, (void far *)&fd_50F6_0A0A },
    { 2, 64, (void far *)&fd_50F6_0856 },
    { 2, 64, (void far *)&fd_50F6_0970 },
    { 2, 64, (void far *)&fd_50F6_06AE },
    { 2, 64, (void far *)&fd_50F6_07CE },
    { 2, 64, (void far *)&fd_50F6_05A0 },
    { 2, 4, (void far *)&IdealCaste },
    { 2, 6, (void far *)&fd_50F6_0B12 },
    { 2, 6, (void far *)&fd_50F6_0C2A },
    { 2, 6, (void far *)&PillarMap },
    { 2, 3, (void far *)&SowDir },
    { 2, 3, (void far *)&SowSave },
    { 2, 3, (void far *)&SowX },
    { 2, 3, (void far *)&SowY },
    { 2, 10, (void far *)(fd_3D57_087A + 20) },
    { 2, 6, (void far *)&fd_3D57_07A8 },
    { 2, 1, (void far *)&AntsEatenByLions },
    { 2, 1, (void far *)&fd_50F6_0A9E },
    { 2, 1, (void far *)&fd_50F6_0A90 },
    { 2, 1, (void far *)&Barrier },
    { 2, 1, (void far *)&fd_50F6_108C },
    { 2, 1, (void far *)&fd_50F6_0208 },
    { 2, 1, (void far *)&fd_50F6_0210 },
    { 2, 1, (void far *)&fd_50F6_10A0 },
    { 2, 1, (void far *)&fd_50F6_10AC },
    { 2, 1, (void far *)&fd_50F6_10BA },
    { 2, 1, (void far *)&fd_50F6_09FA },
    { 2, 1, (void far *)&fd_50F6_035E },
    { 2, 1, (void far *)&fd_50F6_0FFE },
    { 2, 1, (void far *)&fd_3D57_0C30 },
    { 2, 1, (void far *)&fd_3D57_0C32 },
    { 2, 1, (void far *)&fd_3D57_0C28 },
    { 2, 1, (void far *)&fd_50F6_10B0 },
    { 2, 1, (void far *)&fd_50F6_10BC },
    { 2, 1, (void far *)&fd_50F6_0246 },
    { 2, 1, (void far *)&fd_50F6_023E },
    { 2, 1, (void far *)&fd_3D57_0C40 },
    { 2, 1, (void far *)&fd_3D57_0C34 },
    { 2, 1, (void far *)&fd_3D57_0C2A },
    { 2, 1, (void far *)&fd_3D57_0C2C },
    { 2, 1, (void far *)&fd_3D57_0C2E },
    { 2, 1, (void far *)&BpopT },
    { 2, 1, (void far *)&fd_50F6_022C },
    { 2, 1, (void far *)&fd_50F6_0240 },
    { 2, 1, (void far *)&fd_50F6_0244 },
    { 2, 1, (void far *)&fd_50F6_0254 },
    { 2, 1, (void far *)&fd_50F6_02BE },
    { 2, 1, (void far *)&fd_50F6_032C },
    { 2, 1, (void far *)&ChaseSpid },
    { 2, 1, (void far *)&fd_3D57_0C1E },
    { 2, 1, (void far *)&fd_50F6_03E2 },
    { 2, 1, (void far *)&fd_50F6_0400 },
    { 2, 1, (void far *)&fd_3D57_0C20 },
    { 2, 1, (void far *)&fd_50F6_0D70 },
    { 2, 1, (void far *)&CurExpTool },
    { 2, 1, (void far *)&fd_50F6_105E },
    { 2, 1, (void far *)&fd_50F6_0EAC },
    { 2, 1, (void far *)&Cycle },
    { 2, 1, (void far *)&fd_50F6_0476 },
    { 2, 1, (void far *)&DeathCnt },
    { 2, 1, (void far *)&fd_50F6_0506 },
    { 2, 1, (void far *)&fd_50F6_04E4 },
    { 2, 1, (void far *)&fd_50F6_0510 },
    { 2, 1, (void far *)&fd_50F6_059E },
    { 2, 1, (void far *)&fd_50F6_0624 },
    { 2, 1, (void far *)&fd_50F6_04BE },
    { 2, 1, (void far *)&fd_50F6_04C6 },
    { 2, 1, (void far *)&EatCnt },
    { 2, 1, (void far *)&fd_50F6_0212 },
    { 2, 1, (void far *)&fd_50F6_0226 },
    { 2, 1, (void far *)&fd_50F6_08DC },
    { 2, 1, (void far *)&fd_50F6_08E8 },
    { 2, 1, (void far *)&fd_50F6_1040 },
    { 2, 1, (void far *)&FoodB },
    { 2, 1, (void far *)&FoodR },
    { 2, 1, (void far *)&fd_3D57_0C3E },
    { 2, 1, (void far *)&fd_50F6_03E0 },
    { 2, 1, (void far *)&fd_50F6_046A },
    { 2, 1, (void far *)&FuzLocX },
    { 2, 1, (void far *)&FuzLocY },
    { 2, 1, (void far *)&fd_50F6_047E },
    { 2, 1, (void far *)&fd_3D57_07CC },
    { 2, 1, (void far *)&HealthB },
    { 2, 1, (void far *)&HealthR },
    { 2, 1, (void far *)&fd_3D57_0828 },
    { 2, 1, (void far *)&fd_50F6_04F4 },
    { 2, 1, (void far *)&fd_50F6_0478 },
    { 2, 1, (void far *)&InitialLions },
    { 2, 1, (void far *)&fd_50F6_0504 },
    { 2, 1, (void far *)&fd_50F6_0488 },
    { 2, 1, (void far *)&fd_50F6_0492 },
    { 2, 1, (void far *)&fd_50F6_0228 },
    { 2, 1, (void far *)&fd_3D57_02C0 },
    { 2, 1, (void far *)&fd_50F6_1074 },
    { 2, 1, (void far *)&LionIndex },
    { 2, 1, (void far *)&ListIndexA },
    { 2, 1, (void far *)&ListIndexB },
    { 2, 1, (void far *)&ListIndexR },
    { 2, 1, (void far *)&fd_3D57_0C0E },
    { 2, 1, (void far *)&fd_3D57_07C8 },
    { 2, 1, (void far *)&MapPlane },
    { 2, 1, (void far *)&fd_50F6_049A },
    { 2, 1, (void far *)&fd_50F6_0A8E },
    { 2, 1, (void far *)&fd_50F6_04E2 },
    { 2, 1, (void far *)&fd_50F6_0D6C },
    { 2, 1, (void far *)&fd_50F6_0EF8 },
    { 2, 1, (void far *)&fd_50F6_0EFA },
    { 2, 1, (void far *)&fd_50F6_0496 },
    { 2, 1, (void far *)&fd_50F6_0B1E },
    { 2, 1, (void far *)&fd_50F6_0502 },
    { 2, 1, (void far *)&fd_3D57_0C22 },
    { 2, 1, (void far *)&fd_3D57_0C26 },
    { 2, 1, (void far *)&fd_50F6_0AF8 },
    { 2, 1, (void far *)&fd_50F6_0AD6 },
    { 2, 1, (void far *)&fd_50F6_0AE8 },
    { 2, 1, (void far *)&MeHealth },
    { 2, 1, (void far *)&fd_50F6_1006 },
    { 2, 1, (void far *)&fd_50F6_0AB6 },
    { 2, 1, (void far *)&fd_50F6_0AC6 },
    { 2, 1, (void far *)&MeLocX },
    { 2, 1, (void far *)&MeLocY },
    { 2, 1, (void far *)&fd_50F6_0A06 },
    { 2, 1, (void far *)&fd_50F6_0AA0 },
    { 2, 1, (void far *)&fd_3D57_0C24 },
    { 2, 1, (void far *)&MePlane },
    { 2, 1, (void far *)&fd_50F6_0C38 },
    { 2, 1, (void far *)&fd_50F6_06AC },
    { 2, 1, (void far *)&fd_50F6_04C4 },
    { 2, 1, (void far *)&fd_50F6_0C3E },
    { 2, 1, (void far *)&fd_50F6_07C0 },
    { 2, 1, (void far *)&fd_50F6_084E },
    { 2, 1, (void far *)&fd_50F6_08DA },
    { 2, 1, (void far *)&fd_50F6_08E2 },
    { 2, 1, (void far *)&fd_50F6_09F0 },
    { 2, 1, (void far *)&fd_50F6_04C2 },
    { 2, 1, (void far *)&fd_50F6_0FBA },
    { 2, 1, (void far *)&ModeMe },
    { 2, 1, (void far *)&fd_50F6_0470 },
    { 2, 1, (void far *)&fd_50F6_047A },
    { 2, 1, (void far *)&fd_3D57_0C1A },
    { 2, 1, (void far *)&fd_3D57_0C46 },
    { 2, 1, (void far *)&fd_3D57_0C48 },
    { 2, 1, (void far *)&fd_50F6_0332 },
    { 2, 1, (void far *)&PillDir },
    { 2, 1, (void far *)&PillarSeg },
    { 2, 1, (void far *)&PillarState },
    { 2, 1, (void far *)&PillarX },
    { 2, 1, (void far *)&PillarY },
    { 2, 1, (void far *)&fd_50F6_07C8 },
    { 2, 1, (void far *)&fd_50F6_0850 },
    { 2, 1, (void far *)&fd_50F6_0AC8 },
    { 2, 1, (void far *)&fd_50F6_0AC4 },
    { 2, 1, (void far *)&fd_50F6_0356 },
    { 2, 1, (void far *)&fd_50F6_0352 },
    { 2, 1, (void far *)&fd_50F6_0F0E },
    { 2, 1, (void far *)&fd_50F6_0F26 },
    { 2, 1, (void far *)&fd_50F6_04E0 },
    { 2, 1, (void far *)&fd_50F6_04F2 },
    { 2, 1, (void far *)&RedLocX },
    { 2, 1, (void far *)&RedLocY },
    { 2, 1, (void far *)&fd_50F6_0A00 },
    { 2, 1, (void far *)&RedPlane },
    { 2, 1, (void far *)&fd_50F6_036C },
    { 2, 1, (void far *)&fd_50F6_04A4 },
    { 2, 1, (void far *)&RpopT },
    { 2, 1, (void far *)&SCorpseBase },
    { 2, 1, (void far *)&SMode },
    { 2, 1, (void far *)&Scycle2 },
    { 2, 1, (void far *)&Scycle },
    { 2, 1, (void far *)&SpidBurpCnt },
    { 2, 1, (void far *)&fd_50F6_1004 },
    { 2, 1, (void far *)&fd_50F6_0F0C },
    { 2, 1, (void far *)&SpidRevenge },
    { 2, 1, (void far *)&fd_50F6_0F12 },
    { 2, 1, (void far *)&fd_50F6_0F34 },
    { 2, 1, (void far *)&Starg },
    { 2, 1, (void far *)&StargLife },
    { 2, 1, (void far *)&StrategicModeB },
    { 2, 1, (void far *)&fd_50F6_10A6 },
    { 2, 1, (void far *)&SuserX },
    { 2, 1, (void far *)&SuserY },
    { 2, 1, (void far *)&fd_50F6_103C },
    { 2, 1, (void far *)&fd_50F6_1048 },
    { 2, 1, (void far *)&fd_50F6_06AA },
    { 2, 1, (void far *)&fd_50F6_073A },
    { 2, 1, (void far *)&fd_50F6_105C },
    { 2, 1, (void far *)&fd_50F6_1066 },
    { 2, 1, (void far *)&TERRAINset },
    { 2, 1, (void far *)&fd_50F6_10B2 },
    { 2, 1, (void far *)&fd_50F6_0200 },
    { 2, 1, (void far *)&fd_50F6_10C0 },
    { 2, 1, (void far *)&fd_50F6_020E },
    { 2, 1, (void far *)&fd_50F6_0224 },
    { 2, 1, (void far *)&TilesDugR },
    { 2, 1, (void far *)&fd_3D57_07A6 },
    { 2, 1, (void far *)&fd_50F6_10B8 },
    { 2, 1, (void far *)&fd_3D57_07A4 },
    { 2, 1, (void far *)&fd_3D57_07A2 },
    { 2, 1, (void far *)&fd_50F6_0242 },
    { 2, 1, (void far *)&fd_50F6_07C2 },
    { 2, 1, (void far *)&YardMode },
    { 2, 1, (void far *)&fd_50F6_0F44 },
    { 2, 1, (void far *)&fd_50F6_024E },
    { 2, 1, (void far *)&fd_50F6_0370 },
    { 2, 1, (void far *)&fd_3D57_0C18 },
    { 2, 1, (void far *)&fd_50F6_0202 },
    { 2, 1, (void far *)&fd_50F6_0366 },
    { 2, 1, (void far *)&CasteAuto },
    { 2, 1, (void far *)&fd_3D57_0C42 },
    { 2, 1, (void far *)&fd_3D57_0C44 },
    { 2, 1, (void far *)&fd_50F6_0376 },
    { 2, 1, (void far *)&fd_3D57_0C14 },
    { 2, 1, (void far *)&fd_50F6_0354 },
    { 2, 1, (void far *)&fd_50F6_104E },
    { 2, 1, (void far *)&fd_50F6_1058 },
    { 2, 1, (void far *)&fd_50F6_1044 },
    { 2, 1, (void far *)&ModeAuto },
    { 2, 1, (void far *)&fd_3D57_0C16 },
    { 2, 1, (void far *)&fd_3D57_0C1C },
    { 2, 1, (void far *)&fd_3D57_0C12 },
    { 2, 1, (void far *)&fd_3D57_07EA },
    { 2, 1, (void far *)&fd_50F6_0468 },
    { 0, 0, 0 }
};
