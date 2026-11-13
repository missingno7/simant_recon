/*
 * Locks and unlocks window resources through nested access. It checks window numbers, discarded
 * handles and lock depth.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 23AE; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

extern void far Punt(char far *format, ...);

static int g_644C = 0;
static int g_644E = 0;
static unsigned char g_8DA6[45];
static char far *g_8CF2[45];

void far win_NoWindowsShouldBeLocked(void)
{
    int i;

    for (i = 0; i < 45; i++)
        if (g_8DA6[i])
            Punt("Window %d locked when it should not be!");
}

void far win_LockInit(void)
{
    _fmemset(g_8CF2, 0, sizeof g_8CF2);
    _fmemset(g_8DA6, 0, sizeof g_8DA6);
    g_644C = 1;
}

int _fastcall win_IsWinLocked(int win)
{
    if (g_644C == 0)
        return 1;
    return g_8DA6[win >> 8];
}

extern char far * far * near win_handles[];
extern void far win_LoadWindow(int win);
extern int far mem_LockLevel(char far * far *handle);
void far win_report_already_locked(void);
extern char far * far mem_move_high_and_lock(char far * far *handle);
extern char far * far mem_Lock(char far * far *handle);
extern void far mem_Free(char far * far *handle);
extern void far mem_set_alloc_type(char far * far *handle, int flag);
extern void _fastcall RepointObjects(int win);
extern void _fastcall win_Recalc(int win);

void _fastcall win_load_and_lock_resource(int win, int high)
{
    int loaded = 0;
    int n;
    char far * far *h;
    char far *w;

    g_644E++;
    if (g_644C == 0)
        return;
    n = (char)(win >> 8);
    if (n > 40 || n < 0)
        Punt("Illegal win num %x at lock", n);
    if (win_handles[n] == 0) {
        win_LoadWindow(win);
        loaded = 1;
    }
    h = win_handles[n];
    if (g_8DA6[n] == 0) {
        g_8DA6[n]++;
        if (mem_LockLevel(h)) {
            high = 0;
            win_report_already_locked();
        }
        if (high)
            w = mem_move_high_and_lock(h);
        else
            w = mem_Lock(h);
        if (w == 0) {
            mem_Free(h);
            win_LoadWindow(win);
            h = win_handles[n];
            if (high)
                w = mem_move_high_and_lock(h);
            else
                w = mem_Lock(h);
        }
        if (*(int far *)(w + 0x1c) & 0x800)
            mem_set_alloc_type(h, 1);
        if (g_8CF2[n] != w) {
            g_8CF2[n] = w;
            RepointObjects(win);
        }
        if (loaded)
            win_Recalc(win);
    } else if (g_8DA6[n]++ > 10) {
        Punt("win_Lock > 10 levels deep!!");
    }
    g_644E--;
}

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};


struct Obj {
    char pad[0x21];
    char type;
    char pad22[0x2a - 0x22];
    char far * far *h2a;
    char pad2e[0x34 - 0x2e];
    char far * far *h34;
};

struct Win {
    struct Rect rect;
    char pad08[4];
    int count;
    char pad0E[0x1c - 0x0e];
    int flags;
    char pad1E[0x2c - 0x1e];
    struct Obj far *objs[1];
};

extern int far RallocType(struct Win far * far *handle);
extern void far RallocFree(char far * far *handle);
extern void far mem_unlock_encoded_handle(struct Win far * far *handle);
extern void far mem_mark_discardable_20e2(struct Win far * far *handle);
extern struct Rect far win_offsets[];

extern int far WinPrintf(char far *format, ...);
extern void far debug_breakpoint(void);
void _fastcall win_UnlockWin(int win)
{
    char far * far * far *p;
    int n;
    struct Win far * far *h;
    int i;
    struct Obj far *obj;
    struct Win far *w;

    if (g_644C) {
        n = win >> 8;
        h = (struct Win far * far *)win_handles[n];
        if (g_8DA6[n] == 0)
            Punt("Attemp to unlock when not locked!!");
        if (RallocType(h) == 5)
            Punt("Attemp to unlock when discarded win %x", win);
        if (--g_8DA6[n] == 0) {
            if (!((*h)->flags & 0x200) && ((*h)->flags & 0x800) && g_644E == 0) {
                w = *h;
                for (i = 0; i < w->count; i++) {
                    obj = w->objs[i];
                    switch (obj->type) {
                    case 4:
                    case 10:
                        p = &obj->h34;
                        if (*p) {
                            RallocFree(*p);
                            *p = 0;
                        }
                        break;
                    case 16:
                    case 17:
                    case 18:
                        p = &obj->h2a;
                        if (*p) {
                            RallocFree(*p);
                            *p = 0;
                        }
                        break;
                    }
                }
                mem_unlock_encoded_handle(h);
                mem_mark_discardable_20e2(h);
                win_handles[n] = 0;
                g_8CF2[n] = 0;
                win_offsets[n] = *(struct Rect far *)((char far *)w->objs[0] + 8);
            } else {
                mem_unlock_encoded_handle(h);
            }
        }
    }
}



void far win_report_already_locked(void)
{
    WinPrintf("WINLOCKERR!! ALREADY LOCKED!!");
    debug_breakpoint();
}

void _fastcall win_LockWinHigh(int win)
{
    win_load_and_lock_resource(win, 1);
}

void _fastcall win_LockWin(int win)
{
    win_load_and_lock_resource(win, 0);
}
