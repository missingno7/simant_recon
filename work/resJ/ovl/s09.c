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
        y = (r3.bottom + r3.top - f_24AB_030B() + 1) / 2;
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
        if (f_1F58_0038()) {
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
