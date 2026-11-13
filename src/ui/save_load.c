/*
 * Reads and writes saved games and presents the DOS file selector. It contains the 307 record
 * save schema and the initializations needed after loading.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 9 (S09); segment 35F5; complete original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory.
 * Steered functions: o09_35F5_03C6.
 */

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

extern int far gGameNeedsSaving;
extern int far CurGameType;
extern int far fd_3D57_07AA;
extern char far save_last_filename[];
extern struct SaveRec far save_record_table[];

extern int far ui_prompt_save_discard_cancel(int a);
extern void far ui_message_acknowledge(char far *msg);
extern int far ui_choice_prompt(char far *msg, int a);
extern void far ui_message_transient(char far *msg);
extern void far f_15D9_009C(void far *p, long a, int b);
extern void far o11_35F5_0000(void);
extern void far o11_35F5_0088(int a);
extern void far StopSong(void);
extern void far WinPrintf(char far *fmt, ...);

extern int far JustXfered;
extern long far LastThemeTime;
extern long far TimeTemp;
extern long far EditMsgDelay;
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
extern int far MeMode;
extern int far MeDir;
extern int far MeType;
extern int far MeLocY;
extern int far MeLocX;
extern int far MePlane;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int life);
extern void far FullCount(void);
extern void far o15_384C_037F(void);
extern void far f_0250_0FC4(int x, int y);
extern void far SetDefaultWindPrompt(int mode);

int far SaveGame(int useLast);
int far o09_35F5_03C6(char far *name, char far *title, char far *verb, int save);
void far DoPreLoadInits(void);
void far DoLoadInitializations(void);
void far save_normalize_basename(char far *name);

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
    if (gGameNeedsSaving != 0) {
        do {
            r = ui_prompt_save_discard_cancel(0);
            if (r == 2)
                return 0;
        } while (r == 1 && SaveGame(0) == 0);
    }
    if (o09_35F5_03C6(name, "Load Game", "LOAD", 0) != 0) {
        _fstrcpy(save_last_filename, name);
        gGameNeedsSaving = 0;
        fd = open(name, O_RDONLY | O_BINARY);
        if (fd <= 0)
            ui_message_acknowledge(sys_errlist[errno]);
        else {
            n = 0;
            for (p = save_record_table; p->count != 0; p++)
                n += p->count * p->size;
            DoPreLoadInits();
            for (p = save_record_table; p->count != 0; p++) {
                if ((r = read(fd, p->data, n = p->count * p->size)) != n) {
                    ui_message_acknowledge("  Read error  \ngame not loaded");
                    CurGameType = -1;
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
            DoLoadInitializations();
            if (fd_3D57_07AA == 0)
                StopSong();
        }
    }
    return ok;
}

/* SaveGame */
int far SaveGame(int useLast)
{
    struct SaveRec far *p;
    int fd;
    char name[100];
    char msg[100];
    int ok;
    int total;

    ok = 0;
    if (save_last_filename != 0L && *save_last_filename != 0 && useLast != 0) {
        _fstrcpy(name, save_last_filename);
        goto tryit;
    }
select:
    if (o09_35F5_03C6(name, "Save Game", "SAVE", 1) == 0)
        goto done;
    _fstrcpy(save_last_filename, name);
    WinPrintf("\nlastFileName==%s", save_last_filename);
tryit:
    fd = open(name, O_RDWR | O_BINARY);
    if (fd > 0) {
        sprintf(msg, "OVERWRITE\n%s", name);
        if (ui_choice_prompt(msg, 0) == 0)
            goto write;
        close(fd);
        goto select;
    }
    fd = open(name, O_RDWR | O_CREAT | O_TRUNC | O_BINARY, S_IREAD | S_IWRITE);
    if (fd <= 0) {
        ui_message_acknowledge(sys_errlist[errno]);
        *save_last_filename = 0;
        goto done;
    }
write:
    total = 0;
    for (p = save_record_table; p->count != 0; p++) {
        total += p->count * p->size;
        WinPrintf("\nTOTALLEN=%u", total);
    }
    WinPrintf("\nCOPYING DATA INTO BUFFER!");
    for (p = save_record_table; p->count != 0; p++) {
        if (write(fd, p->data, p->count * p->size) == -1) {
            *save_last_filename = 0;
            ui_message_acknowledge(sys_errlist[errno]);
            close(fd);
            remove(name);
            return 0;
        }
    }
    WinPrintf("\nWRITING");
    gGameNeedsSaving = 0;
    sprintf(msg, "%s\nSaved correctly", name);
    ui_message_transient(msg);
    _fstrcpy(save_last_filename, name);
    ok = 1;
    close(fd);
done:
    return ok;
}

#include "rect.h"

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

extern int far startup_drive_letter;
extern char far * far startup_working_directory;
extern char far text_entry_pending_key;

extern int far file_drive_current_directory(int drive, char far *path);
extern Handle far Ralloc(long size, int flags, char far *name);
extern void far RallocFree(Handle h);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_UnlockWin(int win);
extern void far win_SetObjFormatStr(int obj, ...);
extern void _fastcall win_get_obj_layout_rect(int obj, struct Rect far *r);
extern void _fastcall win_set_obj_layout_rect(int obj, struct Rect far *r);
extern void _fastcall win_MakeGroupUnselectable(int win, int group);
extern void _fastcall win_MakeGroupInvisible(int win, int group);
extern void _fastcall win_MakeGroupSelectable(int win, int group);
extern void _fastcall win_MakeGroupVisible(int win, int group);
extern void far win_Open(int win);
extern void _fastcall win_Close(int win);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void _fastcall win_MakeObjSelected(int obj);
extern void far win_print_text_at_obj_offset(int obj, char far *text, int dx, int dy);
extern void far win_ClearObjToEOL(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far font_FontHeight(void);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far GPutStr(int x, int y, char far *text);
extern int far file_wildcard_match(char far *pattern, char far *name);
extern void far mem_exchange_byte_ranges(void far *a, void far *b, unsigned n);
extern void _fastcall list_replace_text(int obj, char far *text);
extern int far kbd_poll_bios_key(void);
extern int far kbd_read_key_code(void);
extern void _fastcall list_clear_selection(int obj);
extern void far ui_edit_text_field(int x, int y, char far *text, int maxLen, int flags);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern int _fastcall list_line_count(int obj);
extern int _fastcall list_is_line_selected(int obj, int line);
extern char far * _fastcall list_line_record(int obj, int line);


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
        s_2966 = startup_drive_letter;
    if (*name != 0 && file_drive_current_directory(s_2966 - '@', path) != 0) {
        if (path[_fstrlen(path) - 1] != '\\')
            _fstrcat(path, "\\");
        sprintf(buf, "%s%s", path, name);
        _fstrcpy(name, buf);
    }
    h = Ralloc(0xC80L, 0, "File list");
    list = *h;
    _fmemset(list, 0, 4);
    win_LockWin(0x1600);
    win_SetObjFormatStr(0x1613, verb);
    win_SetObjFormatStr(0x1601, title);
    win_get_obj_layout_rect(0x1602, &r);
    if (save != 1) {
        win_MakeGroupUnselectable(0x1600, 5);
        win_MakeGroupInvisible(0x1600, 5);
        r2 = r;
        r2.bottom = 0;
        win_set_obj_layout_rect(0x1602, &r2);
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
    if (file_drive_current_directory(s_2966 - '@', path) == 0) {
retry:
        sprintf(buf, "Cannot read drive %c", s_2966);
        ui_message_acknowledge(buf);
        s_2966 = oldDrive;
        if ((s_2966 == 0 || file_drive_current_directory(s_2966 - '@', path) == 0) && ((unsigned)save >= 0)) {
            if (startup_drive_letter == s_2966)
                ui_message_acknowledge("Can't read disk\nAborting");
            sprintf(buf, "Cannot read drive %c", s_2966);
            ui_message_acknowledge(buf);
            oldDrive = startup_drive_letter;
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
    win_print_text_at_obj_offset(0x1606, "", 0, 0);
    win_ClearObjToEOL(0x1606);
    win_print_text_at_obj_offset(0x1606, path, 4, 0);
    if (save == 1) {
        win_GetObjRect(0x1603, &r3);
        tmp2 = r3.top;
        y = (r3.bottom + tmp2 - font_FontHeight() + 1) / 2;
        x = r3.left + 4;
        win_SetColorFromObjNum(0x1604);
        if (ok && *save_last_filename != 0) {
            _fstrcpy(name, _fstrrchr(save_last_filename, '\\') + 1);
            GPutStr(x, y, name);
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
            if (file_wildcard_match("*.ant", ff.name) == 0)
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
                mem_exchange_byte_ranges(p, best, 16);
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
    list_replace_text(0x1609, *h);
    win_DrawObjectNum(0x1609);
    win_DrawObjectNum(0x1608);
    for (;;) {
        if (kbd_poll_bios_key() && ((unsigned)path >= 0)) {
            key = kbd_read_key_code();
            if (!(key & 0x800) && isalnum(key) && save == 1) {
                text_entry_pending_key = key;
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
            list_clear_selection(0x1609);
            win_DrawObjectNum(0x1603);
            win_SetColorFromObjNum(0x1604);
            ui_edit_text_field(x, y, name, 9, 0);
            break;
        case 0x1613:
            goto accept;
        case 0x1614:
            goto cancel;
        default:
            WinPrintf("\nDEFAULT:Event=%x,%x", ev.code, ev.modifiers);
            if (ev.code == 0x1609) {
                if (ev.modifiers & 0x0A00) {
                    n = list_line_count(0x1609);
                    sel = -1;
                    for (i = 0; i < n; i++)
                        if (list_is_line_selected(0x1609, i)) {
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
                    n = list_line_count(0x1609);
                    for (i = 0; i < n; i++)
                        if (list_is_line_selected(0x1609, i)) {
                            if ((i == sel) && ((unsigned)i >= 0))
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
        n = list_line_count(0x1609);
        for (i = 0; i < n; i++)
            if (list_is_line_selected(0x1609, i)) {
                _fstrcpy(name, list_line_record(0x1609, i) + 1);
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
    win_set_obj_layout_rect(0x1602, &r);
    win_UnlockWin(0x1600);
    if (*name != 0) {
        WinPrintf("\nFilename:%s", name);
        save_normalize_basename(name);
        WinPrintf("->%s", name);
    }
    RallocFree(h);
    _fstrcpy(lastDir, path);
    _fstrcpy(buf, name);
    sprintf(name, "%s%s", path, buf);
    chdir(startup_working_directory);
    WinPrintf("\nPathName=%s, iniPath=%s", name, startup_working_directory);
    return ok;
}

/* append the default extension to a file name (max. 8 characters) */
void far save_normalize_basename(char far *name)
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
void far DoPreLoadInits(void)
{
    JustXfered = 1;
    LastThemeTime = 0L;
    TimeTemp = 300L;
    EditMsgDelay = 0L;
    RandYard();
}

/* rebuild the life maps from the loaded lists */
void far DoLoadInitializations(void)
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
    if (MeMode == 0)
        SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 255);
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
extern unsigned char far YMapPopB[];
extern unsigned char far YMapPopR[];
extern unsigned char far YMapSeeds[];
extern unsigned char far BAntsEaten[];
extern unsigned char far BAntsExpired[];
extern unsigned char far BAntsKilled[];
extern unsigned char far BirdDelay[];
extern unsigned char far BoyMsgCnt[];
extern unsigned char far CatDelay[];
extern unsigned char far DogBarkDelay[];
extern unsigned char far GameTime[];
extern unsigned char far OverallScore[];
extern unsigned char far RAntsEaten[];
extern unsigned char far RAntsExpired[];
extern unsigned char far RAntsKilled[];
extern unsigned char far TileTotXB[];
extern unsigned char far TileTotXR[];
extern unsigned char far TileTotYB[];
extern unsigned char far TileTotYR[];
extern unsigned char far TotalEggsDiedB[];
extern unsigned char far TotalEggsLaidB[];
extern unsigned char far AMapPnt[];
extern unsigned char far BMapPnt[];
extern unsigned char far CurYardPnt[];
extern unsigned char far LastBlackEgg[];
extern unsigned char far LastFoodDrop[];
extern unsigned char far LastNewExitB[];
extern unsigned char far LastNewExitR[];
extern unsigned char far LastNewHoleB[];
extern unsigned char far LastNewHoleR[];
extern unsigned char far LastRedEgg[];
extern unsigned char far MapPnt[];
extern unsigned char far RMapPnt[];
extern unsigned char far YMapPnt[];
extern unsigned char far SwarmXB[];
extern unsigned char far SwarmXR[];
extern unsigned char far SwarmYB[];
extern unsigned char far SwarmYR[];
extern unsigned char far DeadX[];
extern unsigned char far DeadY[];
extern unsigned char far LionListM[];
extern unsigned char far LionListS[];
extern unsigned char far LionListT[];
extern unsigned char far LionListX[];
extern unsigned char far LionListY[];
extern unsigned char far RxTab[];
extern unsigned char far RyTab[];
extern unsigned char far casteLevels[];
extern unsigned char far casteSetLevels[];
extern unsigned char far modeLevels[];
extern unsigned char far modeSetLevels[];
extern unsigned char far CastePopB[];
extern unsigned char far CastePopR[];
extern unsigned char far GrassMap[];
extern unsigned char far H_ADead[];
extern unsigned char far H_BFood[];
extern unsigned char far H_BHeal[];
extern unsigned char far H_BPop[];
extern unsigned char far H_FDead[];
extern unsigned char far H_FoodA[];
extern unsigned char far H_PDead[];
extern unsigned char far H_RFood[];
extern unsigned char far H_RHeal[];
extern unsigned char far H_RPop[];
extern unsigned char far IdealCaste[];
extern unsigned char far ModePopB[];
extern unsigned char far ModePopR[];
extern unsigned char far PillarMap[];
extern unsigned char far SowDir[];
extern unsigned char far SowSave[];
extern unsigned char far SowX[];
extern unsigned char far SowY[];
extern unsigned char far HistGraphColors[];
extern unsigned char far OptionStates[];
extern unsigned char far AntsEatenByLions[];
extern unsigned char far BColoniesKilled[];
extern unsigned char far BColoniesStarted[];
extern unsigned char far Barrier[];
extern unsigned char far BirdFrame[];
extern unsigned char far BirdGoalX[];
extern unsigned char far BirdGoalY[];
extern unsigned char far BirdOn[];
extern unsigned char far BirdX[];
extern unsigned char far BirdY[];
extern unsigned char far BlackLost[];
extern unsigned char far BlkQueens[];
extern unsigned char far BlkWarnHealth[];
extern unsigned char far BoyDir[];
extern unsigned char far BoyFrame[];
extern unsigned char far BoyHere[];
extern unsigned char far BoyMessOn[];
extern unsigned char far BoyMsgOffset[];
extern unsigned char far BoyPx[];
extern unsigned char far BoyPy[];
extern unsigned char far BoyStandCnt[];
extern unsigned char far BoyTurnCnt[];
extern unsigned char far BoyWait[];
extern unsigned char far BoyX[];
extern unsigned char far BoyY[];
extern unsigned char far BpopT[];
extern unsigned char far CatCycle[];
extern unsigned char far CatDir[];
extern unsigned char far CatFrame[];
extern unsigned char far CatOn[];
extern unsigned char far CatX[];
extern unsigned char far CatY[];
extern unsigned char far ChaseSpid[];
extern unsigned char far ClearRainFlag[];
extern unsigned char far ColonyTotalBlack[];
extern unsigned char far ColonyTotalRed[];
extern unsigned char far ColonyUpdateFlag[];
extern unsigned char far CurEditMode[];
extern unsigned char far CurExpTool[];
extern unsigned char far CurGameTool[];
extern unsigned char far Cycle[];
extern unsigned char far DdPtr[];
extern unsigned char far DeathCnt[];
extern unsigned char far DogDir[];
extern unsigned char far DogFrame[];
extern unsigned char far DogPx[];
extern unsigned char far DogPy[];
extern unsigned char far DogTurnCnt[];
extern unsigned char far DogX[];
extern unsigned char far DogY[];
extern unsigned char far EatCnt[];
extern unsigned char far EatCountB[];
extern unsigned char far EatCountR[];
extern unsigned char far FlyAwayB[];
extern unsigned char far FlyAwayR[];
extern unsigned char far FoodA[];
extern unsigned char far FoodB[];
extern unsigned char far FoodR[];
extern unsigned char far FootHere[];
extern unsigned char far FootX[];
extern unsigned char far FootY[];
extern unsigned char far FuzLocX[];
extern unsigned char far FuzLocY[];
extern unsigned char far GamePaused[];
extern unsigned char far GameSpeed[];
extern unsigned char far HealthB[];
extern unsigned char far HealthR[];
extern unsigned char far HistCnt[];
extern unsigned char far HistStart[];
extern unsigned char far HouseColonies[];
extern unsigned char far InitialLions[];
extern unsigned char far JustToBeMean[];
extern unsigned char far LastMowX[];
extern unsigned char far LastMowY[];
extern unsigned char far LastThemeSong[];
extern unsigned char far LayDownQueenMode[];
extern unsigned char far LessonTemp[];
extern unsigned char far LionIndex[];
extern unsigned char far MakeMe[];
extern unsigned char far MapMode[];
extern unsigned char far MapPlane[];
extern unsigned char far MeBase[];
extern unsigned char far MeCmd[];
extern unsigned char far MeColor[];
extern unsigned char far MeCrazyCnt[];
extern unsigned char far MeCrazyDir[];
extern unsigned char far MeCrazyRot[];
extern unsigned char far MeDis[];
extern unsigned char far MeEgg[];
extern unsigned char far MeEggCarried[];
extern unsigned char far MeFoodInType[];
extern unsigned char far MeGoalPlane[];
extern unsigned char far MeGoalX[];
extern unsigned char far MeGoalY[];
extern unsigned char far MeHealth[];
extern unsigned char far MeHealthCntDwn[];
extern unsigned char far MeLastX[];
extern unsigned char far MeLastY[];
extern unsigned char far MeMoveMe[];
extern unsigned char far MeNestStarted[];
extern unsigned char far MePrevDis[];
extern unsigned char far MeSMode[];
extern unsigned char far MeScent[];
extern unsigned char far MeSteps[];
extern unsigned char far MeTargIndex[];
extern unsigned char far MeTargLife[];
extern unsigned char far MeTargLifePlane[];
extern unsigned char far MeTargLifeX[];
extern unsigned char far MeTargLifeY[];
extern unsigned char far MeWarnHealth[];
extern unsigned char far ModeMe[];
extern unsigned char far MowX[];
extern unsigned char far MowY[];
extern unsigned char far NextFeed[];
extern unsigned char far NodeCnt[];
extern unsigned char far NodeNum[];
extern unsigned char far OldMapPlane[];
extern unsigned char far PillDir[];
extern unsigned char far PillarSeg[];
extern unsigned char far PillarState[];
extern unsigned char far PillarX[];
extern unsigned char far PillarY[];
extern unsigned char far QueenStorageB[];
extern unsigned char far QueenStorageR[];
extern unsigned char far RColoniesKilled[];
extern unsigned char far RColoniesStarted[];
extern unsigned char far RainCnt[];
extern unsigned char far RainOn[];
extern unsigned char far RebornX[];
extern unsigned char far RebornY[];
extern unsigned char far RedDestX[];
extern unsigned char far RedDestY[];
extern unsigned char far RedLocX[];
extern unsigned char far RedLocY[];
extern unsigned char far RedLost[];
extern unsigned char far RedPlane[];
extern unsigned char far RedQueens[];
extern unsigned char far RedTask[];
extern unsigned char far RpopT[];
extern unsigned char far SCorpseBase[];
extern unsigned char far SMode[];
extern unsigned char far Scycle2[];
extern unsigned char far Scycle[];
extern unsigned char far SpidBurpCnt[];
extern unsigned char far SpidDir[];
extern unsigned char far SpidOn[];
extern unsigned char far SpidRevenge[];
extern unsigned char far SpidX[];
extern unsigned char far SpidY[];
extern unsigned char far Starg[];
extern unsigned char far StargLife[];
extern unsigned char far StrategicModeB[];
extern unsigned char far StrategicModeR[];
extern unsigned char far SuserX[];
extern unsigned char far SuserY[];
extern unsigned char far SwarmCentX[];
extern unsigned char far SwarmCentY[];
extern unsigned char far SwarmCntB[];
extern unsigned char far SwarmCntR[];
extern unsigned char far SwarmDelayB[];
extern unsigned char far SwarmDelayR[];
extern unsigned char far TileMassXB[];
extern unsigned char far TileMassXR[];
extern unsigned char far TileMassYB[];
extern unsigned char far TileMassYR[];
extern unsigned char far TilesDugB[];
extern unsigned char far TilesDugR[];
extern unsigned char far TutGiven[];
extern unsigned char far TutHowLong[];
extern unsigned char far TutLesson[];
extern unsigned char far TutorCnt[];
extern unsigned char far WaterTable[];
extern unsigned char far YardCycle[];
extern unsigned char far YardMode[];
extern unsigned char far YellowDied[];
extern unsigned char far casteButtonState[];
extern unsigned char far modeButtonState[];
extern unsigned char far AlwaysHealthy[];
extern unsigned char far BoyIsMowing[];
extern unsigned char far BlackWon[];
extern unsigned char far CasteAuto[];
extern unsigned char far FootTog[];
extern unsigned char far ForSaleState[];
extern unsigned char far IsGameOver[];
extern unsigned char far Invincible[];
extern unsigned char far MeDropAlarm[];
extern unsigned char far MeStartedFight[];
extern unsigned char far MeWantFood[];
extern unsigned char far ModeAuto[];
extern unsigned char far NeverHungry[];
extern unsigned char far RedInitOn[];
extern unsigned char far RevSpider[];
extern unsigned char far ShowPercentCaste[];
extern unsigned char far ShowPercentMode[];

/*
 * Ordered save/load records; a zero count terminates traversal.
 */
struct SaveRec far save_record_table[308] = {
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
    { 1, 192, (void far *)&YMapPopB },
    { 1, 192, (void far *)&YMapPopR },
    { 2, 192, (void far *)&YMapSeeds },
    { 4, 1, (void far *)&BAntsEaten },
    { 4, 1, (void far *)&BAntsExpired },
    { 4, 1, (void far *)&BAntsKilled },
    { 4, 1, (void far *)&BirdDelay },
    { 4, 1, (void far *)&BoyMsgCnt },
    { 4, 1, (void far *)&CatDelay },
    { 4, 1, (void far *)&DogBarkDelay },
    { 4, 1, (void far *)&GameTime },
    { 4, 1, (void far *)&OverallScore },
    { 4, 1, (void far *)&RAntsEaten },
    { 4, 1, (void far *)&RAntsExpired },
    { 4, 1, (void far *)&RAntsKilled },
    { 4, 1, (void far *)&TileTotXB },
    { 4, 1, (void far *)&TileTotXR },
    { 4, 1, (void far *)&TileTotYB },
    { 4, 1, (void far *)&TileTotYR },
    { 4, 1, (void far *)&TotalEggsDiedB },
    { 4, 1, (void far *)&TotalEggsLaidB },
    { 4, 1, (void far *)&AMapPnt },
    { 4, 1, (void far *)&BMapPnt },
    { 4, 1, (void far *)&CurYardPnt },
    { 4, 1, (void far *)&LastBlackEgg },
    { 4, 1, (void far *)&LastFoodDrop },
    { 4, 1, (void far *)&LastNewExitB },
    { 4, 1, (void far *)&LastNewExitR },
    { 4, 1, (void far *)&LastNewHoleB },
    { 4, 1, (void far *)&LastNewHoleR },
    { 4, 1, (void far *)&LastRedEgg },
    { 4, 1, (void far *)&MapPnt },
    { 4, 1, (void far *)&RMapPnt },
    { 4, 1, (void far *)&YMapPnt },
    { 1, 50, (void far *)&SwarmXB },
    { 1, 50, (void far *)&SwarmXR },
    { 1, 50, (void far *)&SwarmYB },
    { 1, 50, (void far *)&SwarmYR },
    { 1, 100, (void far *)&DeadX },
    { 1, 100, (void far *)&DeadY },
    { 1, 10, (void far *)&LionListM },
    { 1, 10, (void far *)&LionListS },
    { 1, 10, (void far *)&LionListT },
    { 1, 10, (void far *)&LionListX },
    { 1, 10, (void far *)&LionListY },
    { 1, 100, (void far *)&RxTab },
    { 1, 100, (void far *)&RyTab },
    { 2, 3, (void far *)&casteLevels },
    { 2, 12, (void far *)&casteSetLevels },
    { 2, 3, (void far *)&modeLevels },
    { 2, 12, (void far *)&modeSetLevels },
    { 2, 6, (void far *)&CastePopB },
    { 2, 6, (void far *)&CastePopR },
    { 2, 12, (void far *)&GrassMap },
    { 2, 64, (void far *)&H_ADead },
    { 2, 64, (void far *)&H_BFood },
    { 2, 64, (void far *)&H_BHeal },
    { 2, 64, (void far *)&H_BPop },
    { 2, 64, (void far *)&H_FDead },
    { 2, 64, (void far *)&H_FoodA },
    { 2, 64, (void far *)&H_PDead },
    { 2, 64, (void far *)&H_RFood },
    { 2, 64, (void far *)&H_RHeal },
    { 2, 64, (void far *)&H_RPop },
    { 2, 4, (void far *)&IdealCaste },
    { 2, 6, (void far *)&ModePopB },
    { 2, 6, (void far *)&ModePopR },
    { 2, 6, (void far *)&PillarMap },
    { 2, 3, (void far *)&SowDir },
    { 2, 3, (void far *)&SowSave },
    { 2, 3, (void far *)&SowX },
    { 2, 3, (void far *)&SowY },
    { 2, 10, (void far *)(HistGraphColors + 20) },
    { 2, 6, (void far *)&OptionStates },
    { 2, 1, (void far *)&AntsEatenByLions },
    { 2, 1, (void far *)&BColoniesKilled },
    { 2, 1, (void far *)&BColoniesStarted },
    { 2, 1, (void far *)&Barrier },
    { 2, 1, (void far *)&BirdFrame },
    { 2, 1, (void far *)&BirdGoalX },
    { 2, 1, (void far *)&BirdGoalY },
    { 2, 1, (void far *)&BirdOn },
    { 2, 1, (void far *)&BirdX },
    { 2, 1, (void far *)&BirdY },
    { 2, 1, (void far *)&BlackLost },
    { 2, 1, (void far *)&BlkQueens },
    { 2, 1, (void far *)&BlkWarnHealth },
    { 2, 1, (void far *)&BoyDir },
    { 2, 1, (void far *)&BoyFrame },
    { 2, 1, (void far *)&BoyHere },
    { 2, 1, (void far *)&BoyMessOn },
    { 2, 1, (void far *)&BoyMsgOffset },
    { 2, 1, (void far *)&BoyPx },
    { 2, 1, (void far *)&BoyPy },
    { 2, 1, (void far *)&BoyStandCnt },
    { 2, 1, (void far *)&BoyTurnCnt },
    { 2, 1, (void far *)&BoyWait },
    { 2, 1, (void far *)&BoyX },
    { 2, 1, (void far *)&BoyY },
    { 2, 1, (void far *)&BpopT },
    { 2, 1, (void far *)&CatCycle },
    { 2, 1, (void far *)&CatDir },
    { 2, 1, (void far *)&CatFrame },
    { 2, 1, (void far *)&CatOn },
    { 2, 1, (void far *)&CatX },
    { 2, 1, (void far *)&CatY },
    { 2, 1, (void far *)&ChaseSpid },
    { 2, 1, (void far *)&ClearRainFlag },
    { 2, 1, (void far *)&ColonyTotalBlack },
    { 2, 1, (void far *)&ColonyTotalRed },
    { 2, 1, (void far *)&ColonyUpdateFlag },
    { 2, 1, (void far *)&CurEditMode },
    { 2, 1, (void far *)&CurExpTool },
    { 2, 1, (void far *)&CurGameTool },
    { 2, 1, (void far *)&CurGameType },
    { 2, 1, (void far *)&Cycle },
    { 2, 1, (void far *)&DdPtr },
    { 2, 1, (void far *)&DeathCnt },
    { 2, 1, (void far *)&DogDir },
    { 2, 1, (void far *)&DogFrame },
    { 2, 1, (void far *)&DogPx },
    { 2, 1, (void far *)&DogPy },
    { 2, 1, (void far *)&DogTurnCnt },
    { 2, 1, (void far *)&DogX },
    { 2, 1, (void far *)&DogY },
    { 2, 1, (void far *)&EatCnt },
    { 2, 1, (void far *)&EatCountB },
    { 2, 1, (void far *)&EatCountR },
    { 2, 1, (void far *)&FlyAwayB },
    { 2, 1, (void far *)&FlyAwayR },
    { 2, 1, (void far *)&FoodA },
    { 2, 1, (void far *)&FoodB },
    { 2, 1, (void far *)&FoodR },
    { 2, 1, (void far *)&FootHere },
    { 2, 1, (void far *)&FootX },
    { 2, 1, (void far *)&FootY },
    { 2, 1, (void far *)&FuzLocX },
    { 2, 1, (void far *)&FuzLocY },
    { 2, 1, (void far *)&GamePaused },
    { 2, 1, (void far *)&GameSpeed },
    { 2, 1, (void far *)&HealthB },
    { 2, 1, (void far *)&HealthR },
    { 2, 1, (void far *)&HistCnt },
    { 2, 1, (void far *)&HistStart },
    { 2, 1, (void far *)&HouseColonies },
    { 2, 1, (void far *)&InitialLions },
    { 2, 1, (void far *)&JustToBeMean },
    { 2, 1, (void far *)&LastMowX },
    { 2, 1, (void far *)&LastMowY },
    { 2, 1, (void far *)&LastThemeSong },
    { 2, 1, (void far *)&LayDownQueenMode },
    { 2, 1, (void far *)&LessonTemp },
    { 2, 1, (void far *)&LionIndex },
    { 2, 1, (void far *)&ListIndexA },
    { 2, 1, (void far *)&ListIndexB },
    { 2, 1, (void far *)&ListIndexR },
    { 2, 1, (void far *)&MakeMe },
    { 2, 1, (void far *)&MapMode },
    { 2, 1, (void far *)&MapPlane },
    { 2, 1, (void far *)&MeBase },
    { 2, 1, (void far *)&MeCmd },
    { 2, 1, (void far *)&MeColor },
    { 2, 1, (void far *)&MeCrazyCnt },
    { 2, 1, (void far *)&MeCrazyDir },
    { 2, 1, (void far *)&MeCrazyRot },
    { 2, 1, (void far *)&MeDir },
    { 2, 1, (void far *)&MeDis },
    { 2, 1, (void far *)&MeEgg },
    { 2, 1, (void far *)&MeEggCarried },
    { 2, 1, (void far *)&MeFoodInType },
    { 2, 1, (void far *)&MeGoalPlane },
    { 2, 1, (void far *)&MeGoalX },
    { 2, 1, (void far *)&MeGoalY },
    { 2, 1, (void far *)&MeHealth },
    { 2, 1, (void far *)&MeHealthCntDwn },
    { 2, 1, (void far *)&MeLastX },
    { 2, 1, (void far *)&MeLastY },
    { 2, 1, (void far *)&MeLocX },
    { 2, 1, (void far *)&MeLocY },
    { 2, 1, (void far *)&MeMode },
    { 2, 1, (void far *)&MeMoveMe },
    { 2, 1, (void far *)&MeNestStarted },
    { 2, 1, (void far *)&MePlane },
    { 2, 1, (void far *)&MePrevDis },
    { 2, 1, (void far *)&MeSMode },
    { 2, 1, (void far *)&MeScent },
    { 2, 1, (void far *)&MeSteps },
    { 2, 1, (void far *)&MeTargIndex },
    { 2, 1, (void far *)&MeTargLife },
    { 2, 1, (void far *)&MeTargLifePlane },
    { 2, 1, (void far *)&MeTargLifeX },
    { 2, 1, (void far *)&MeTargLifeY },
    { 2, 1, (void far *)&MeType },
    { 2, 1, (void far *)&MeWarnHealth },
    { 2, 1, (void far *)&ModeMe },
    { 2, 1, (void far *)&MowX },
    { 2, 1, (void far *)&MowY },
    { 2, 1, (void far *)&NextFeed },
    { 2, 1, (void far *)&NodeCnt },
    { 2, 1, (void far *)&NodeNum },
    { 2, 1, (void far *)&OldMapPlane },
    { 2, 1, (void far *)&PillDir },
    { 2, 1, (void far *)&PillarSeg },
    { 2, 1, (void far *)&PillarState },
    { 2, 1, (void far *)&PillarX },
    { 2, 1, (void far *)&PillarY },
    { 2, 1, (void far *)&QueenStorageB },
    { 2, 1, (void far *)&QueenStorageR },
    { 2, 1, (void far *)&RColoniesKilled },
    { 2, 1, (void far *)&RColoniesStarted },
    { 2, 1, (void far *)&RainCnt },
    { 2, 1, (void far *)&RainOn },
    { 2, 1, (void far *)&RebornX },
    { 2, 1, (void far *)&RebornY },
    { 2, 1, (void far *)&RedDestX },
    { 2, 1, (void far *)&RedDestY },
    { 2, 1, (void far *)&RedLocX },
    { 2, 1, (void far *)&RedLocY },
    { 2, 1, (void far *)&RedLost },
    { 2, 1, (void far *)&RedPlane },
    { 2, 1, (void far *)&RedQueens },
    { 2, 1, (void far *)&RedTask },
    { 2, 1, (void far *)&RpopT },
    { 2, 1, (void far *)&SCorpseBase },
    { 2, 1, (void far *)&SMode },
    { 2, 1, (void far *)&Scycle2 },
    { 2, 1, (void far *)&Scycle },
    { 2, 1, (void far *)&SpidBurpCnt },
    { 2, 1, (void far *)&SpidDir },
    { 2, 1, (void far *)&SpidOn },
    { 2, 1, (void far *)&SpidRevenge },
    { 2, 1, (void far *)&SpidX },
    { 2, 1, (void far *)&SpidY },
    { 2, 1, (void far *)&Starg },
    { 2, 1, (void far *)&StargLife },
    { 2, 1, (void far *)&StrategicModeB },
    { 2, 1, (void far *)&StrategicModeR },
    { 2, 1, (void far *)&SuserX },
    { 2, 1, (void far *)&SuserY },
    { 2, 1, (void far *)&SwarmCentX },
    { 2, 1, (void far *)&SwarmCentY },
    { 2, 1, (void far *)&SwarmCntB },
    { 2, 1, (void far *)&SwarmCntR },
    { 2, 1, (void far *)&SwarmDelayB },
    { 2, 1, (void far *)&SwarmDelayR },
    { 2, 1, (void far *)&TERRAINset },
    { 2, 1, (void far *)&TileMassXB },
    { 2, 1, (void far *)&TileMassXR },
    { 2, 1, (void far *)&TileMassYB },
    { 2, 1, (void far *)&TileMassYR },
    { 2, 1, (void far *)&TilesDugB },
    { 2, 1, (void far *)&TilesDugR },
    { 2, 1, (void far *)&TutGiven },
    { 2, 1, (void far *)&TutHowLong },
    { 2, 1, (void far *)&TutLesson },
    { 2, 1, (void far *)&TutorCnt },
    { 2, 1, (void far *)&WaterTable },
    { 2, 1, (void far *)&YardCycle },
    { 2, 1, (void far *)&YardMode },
    { 2, 1, (void far *)&YellowDied },
    { 2, 1, (void far *)&casteButtonState },
    { 2, 1, (void far *)&modeButtonState },
    { 2, 1, (void far *)&AlwaysHealthy },
    { 2, 1, (void far *)&BoyIsMowing },
    { 2, 1, (void far *)&BlackWon },
    { 2, 1, (void far *)&CasteAuto },
    { 2, 1, (void far *)&FootTog },
    { 2, 1, (void far *)&ForSaleState },
    { 2, 1, (void far *)&IsGameOver },
    { 2, 1, (void far *)&Invincible },
    { 2, 1, (void far *)&JustXfered },
    { 2, 1, (void far *)&MeDropAlarm },
    { 2, 1, (void far *)&MeStartedFight },
    { 2, 1, (void far *)&MeWantFood },
    { 2, 1, (void far *)&ModeAuto },
    { 2, 1, (void far *)&NeverHungry },
    { 2, 1, (void far *)&RedInitOn },
    { 2, 1, (void far *)&RevSpider },
    { 2, 1, (void far *)&ShowPercentCaste },
    { 2, 1, (void far *)&ShowPercentMode },
    { 0, 0, 0 }
};

/* FileSelect: STEERED folded unsigned path, save-mode and index reads reproduce
 * the local use ordering and CMP operands. The original eliminated expressions
 * are unknown. USE-2 retains whole-module positive and independent negatives. */
