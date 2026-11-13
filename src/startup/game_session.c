/*
 * Starts a new game and restores default windows, and handles quit and fatal exit paths. It also
 * loads monochrome patterns and checks the demo expiry date.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 15 (S15); segment 384C; partial original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Functions not yet exact: ui_prompt_save_discard_cancel.
 */

typedef char far * far *Handle;

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

void far app_cleanup_and_exit(char far *msg, int flag);

void far o15_384C_0000(void)
{
    app_cleanup_and_exit("SimAnt IBM DEMO version has expired.  Please get an update.", 0);
}

extern Handle far db_LoadObject(int object, int kind);
extern void far Punt(char far *format, ...);
extern unsigned char near g_8EC0[];
extern void far db_PurgeObject(int object, int kind);
extern unsigned char near g_8ED8[];

void far LoadMonoPats(void)
{
    Handle h;
    unsigned char far *src;
    unsigned char far *dst;
    int n;
    int i;

    h = db_LoadObject(0x2710, 0x16);
    if (h == 0 || **(int far * far *)h != 0x300)
        Punt("Cannot load monochrome patterns.");
    src = (unsigned char far *)*h + 2;
    dst = g_8EC0;
    n = 0x18;
    for (i = 0; i < n; i++)
        *dst++ = ~*src++;
    db_PurgeObject(0x2710, 0x16);
    h = db_LoadObject(0x271a, 0x16);
    if (h == 0)
        Punt("Cannot load monochrome patterns.");
    n = (*h)[1] << 3;
    src = (unsigned char far *)*h + 2;
    dst = g_8ED8;
    for (i = 0; i < n; i++)
        *dst++ = ~*src++;
    db_PurgeObject(0x271a, 0x16);
}

void far bios_probe_reset_disks(void)
{
    int drive;

    for (drive = 0; drive < 12; drive++) {
        _asm {
            mov dl, byte ptr drive
            or dl, 80h
            mov ah, 1
            int 13h
            jc skip
            mov ah, 0
            int 13h
        skip:
        }
    }
}

static int g_2BD4 = 1;

extern void far f_171C_0676(int flag);
extern void far f_277D_000B(char far *msg);
extern void far f_171C_030C(char far *msg);
extern int far fd_55B3_610A;
extern void far f_277E_0154(void);
extern void far f_1C62_00A1(void);
extern void far f_1C62_0090(void);
extern int far puts(char far *s);
extern void far pascal f_00DE_000A(int code);
extern void far exit(int code);

void far app_cleanup_and_exit(char far *msg, int flag)
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
        if (fd_55B3_610A)
            f_277E_0154();
        f_1C62_00A1();
        f_1C62_0090();
        puts(msg);
    }
    if (flag)
        f_00DE_000A(1);
    exit(0);
}

extern int far gGameNeedsSaving;
int far ui_prompt_save_discard_cancel(int which);
extern int far SaveGame(int flag);

int far MenuQuit(void)
{
    int r;

    if (gGameNeedsSaving) {
        do {
            r = ui_prompt_save_discard_cancel(1);
            if (r == 2)
                return 0;
            if (r != 1)
                break;
        } while (SaveGame(0) == 0);
    }
    app_cleanup_and_exit("SimAnt was brought to you by the people at MAXIS.  Thank you for playing.", 0);
}

extern void far win_Open(int win);
extern Handle far res_load_with_alloc_type(int object, int kind, int type);
extern char far * far mem_Lock(Handle h);
extern int near g_3DB2;
extern void far font_SetFont(int font);
extern char near g_5A97;
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void (far * near g_9128)(int a, int b, int c);
extern void far GRectOutline(struct Rect far *rect, int width);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_PrintTextInRect(int first, char far *text, struct Rect far *rect);
extern int far kbd_poll_bios_key(void);
extern int far kbd_read_key_code(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern Handle far mem_Unlock(Handle h);
extern void far db_ReleaseHandle(Handle handle);
extern void _fastcall win_Close(int win);

extern void far OpenCasteWindow(void);
extern void far OpenModeWindow(void);
extern void far SetEditWinTitle(char far *title);
extern int far MapPlane;
extern void far SetMapPlane(int plane);
extern int _fastcall win_IsWinOpen(int win);
extern void far YardToMap(void);
extern void far SetMapTitle(void);
extern void far OpenEditWindow(void);
extern int far DoScenario(int flag);
extern int far LoadGame(int a, int b);
extern int far CurGameType;
extern int far CurGameTool;
extern void far EndLifeTransferMode(void);
extern void far EndTargetMode(void);
extern void far SetDefaultWindPrompt(int);
extern int far JustXfered;
extern int far QueenStorageB;
extern void far RandYard(void);
extern int far MePlane;
extern int far WinPrintf(char far *format, ...);
extern int far TutLesson;
extern int far TutGiven;
extern int _fastcall win_is_zoomed();
extern void _fastcall win_toggle_zoom();
extern int far MeLocY;
extern int far MeLocX;
extern void far CenterEdit(int x, int y);
extern void far UpdateEdit(void);
int far ui_prompt_save_discard_cancel(int which)
{
    struct Event ev;
    struct Rect r;
    Handle h;
    char far *text;
    int result;

    win_Open(0x2100);
    h = res_load_with_alloc_type((0x41 - which) * 2, 10, 1);
    text = mem_Lock(h);
    font_SetFont(g_3DB2 == 0x140 ? 2 : 4);
    if (g_5A97 & 1) {
        win_GetObjRect(0x2100, &r);
        (*g_9128)(0, 0, 0);
        GRectOutline(&r, 2);
    }
    win_GetObjRect(0x2101, &r);
    win_SetColorFromObjNum(0x2101);
    win_PrintTextInRect(0, text, &r);
    font_SetFont(0);
    for (;;) {
        if (kbd_poll_bios_key()) {
            switch (kbd_read_key_code()) {
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
    mem_Unlock(h);
    db_ReleaseHandle(h);
    win_Close(0x2100);
    return result;
}


void far SetDefaultWindows(void)
{
    OpenCasteWindow();
    OpenModeWindow();
    SetEditWinTitle(0L);
    SetMapPlane(MapPlane);
    if (!win_IsWinOpen(0x100))
        YardToMap();
    SetMapTitle();
    OpenEditWindow();
}


int far NewGame(int flag)
{
    int r;

    gGameNeedsSaving = 0;
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
                CurGameType = r;
                if (CurGameTool == 10)
                    EndLifeTransferMode();
                else if (CurGameTool == 11)
                    EndTargetMode();
                SetDefaultWindPrompt(1);
                SetEditWinTitle(0L);
                JustXfered = 1;
                QueenStorageB = 0;
                RandYard();
                WinPrintf("MePLane=%d", MePlane);
                SetMapPlane(MePlane);
                if (CurGameType == 0) {
                    TutLesson = 1;
                    TutGiven = 0;
                    if (flag == 0)
                        win_Open(0);
                }
            }
        }
        break;
    }
    SetDefaultWindows();
    SetMapPlane(MePlane);
    if (r == 0 && !win_is_zoomed())
        win_toggle_zoom();
    CenterEdit(MeLocX, MeLocY);
    UpdateEdit();
    gGameNeedsSaving = 0;
    return r;
}
