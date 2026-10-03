#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/state/game_views.h"
#include "native_owners.h"
#include "portable/whole_program/state/menu_bar_rect.h"
#pragma pack(push, 2)
/* Overlay section S16, code frame 384C: payoff animation, credits and intro. */

typedef char  *  *Handle;

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
    int16_t code;
    int16_t xE;
};

void  DrawSimPayoff(void);
void  AboutDialog(void);
void  ShowIntro(void);
void  LoadMonoPats(void);
void  o15_384C_0152(char  *msg, int16_t flag);

static int16_t g_2C2C[6][2] = {
    { 0x4a, 0x48 }, { 0x42, 0x57 }, { 0x40, 0xaf },
    { 0x42, 0xbf }, { 0x7a, 0x9f }, { 0x7c, 0xb3 }
};

extern void  MapToYard(void);
extern void  SetYardMode(int16_t mode);
extern void  SetMapPlane(int16_t plane);
extern void  DrawYard(void);
extern void  myDelay(int32_t ticks);
extern void  win_LockWin(int16_t win);
extern void  win_SetObjBitmap(int16_t obj, int16_t bitmap);
extern void  f_22BF_00AA(int16_t obj, struct Rect  *r);
extern void  f_22BF_00DD(int16_t obj, struct Rect  *r);
extern void  win_Open(int16_t win);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  win_UnlockWin(int16_t win);
extern int32_t  MacTickCount(void);
extern void  DialogWaitInit(int16_t ticks);
extern int16_t  mySongIsDone(void);
extern void  myBeginSong(int16_t id, int16_t arg);
extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);
extern int16_t  DialogAbortOrCont(void);
extern void  win_Close(int16_t win);

void  DrawSimPayoff(void)
{
    struct Rect rect;
    struct Rect saved;
    struct Rect bounds;
    int32_t nextFrame;
    int32_t deadline;
    int16_t song;
    int16_t row;
    int16_t i;
    int16_t x;
    int16_t y;

    MapToYard();
    if (native_state_YardMode.signed_value)
        SetYardMode(0);
    if (native_state_MapPlane.signed_value)
        SetMapPlane(0);
    DrawYard();
    myDelay(0x96L);
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, 0x3f48);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140) {
        f_22BF_00AA(0x1a01, &saved);
        bounds = saved;
        bounds.left = 4;
        bounds.top = fd_50F6_393C.bottom + 3;
        f_22BF_00DD(0x1a01, &bounds);
    }
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &rect);
    win_UnlockWin(0x1a00);
    song = 0x4e23;
    row = 1;
    nextFrame = MacTickCount() + 0x1eL;
    deadline = MacTickCount() + 0x258L;
    DialogWaitInit(10);
    while (!DialogAbortOrCont()) {
        if (MacTickCount() >= deadline)
            break;
        if (mySongIsDone() && song < 0x4e25) {
            myBeginSong(song, 0x7e);
            song++;
        }
        if (MacTickCount() >= nextFrame) {
            nextFrame = MacTickCount() + 8L;
            for (i = 0; i < 6; i++) {
                x = g_2C2C[i][1] + rect.left;
                y = g_2C2C[i][0] + rect.top;
                if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140) {
                    x += 0x3f;
                    y -= 10;
                }
                win_DrawBitMap(x, y, row + 0x3f52);
            }
            if (++row >= 3)
                row = 0;
        }
    }
    myDelay(0x12cL);
    win_Close(0x1a00);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140)
        f_22BF_00DD(0x1a01, &saved);
}

extern char  *  *  LoadStringAnt(int16_t object);
extern uint32_t  TickCount(void);
extern void  DialogClearWait(void);
extern int16_t  WaitedEnough(int32_t  *timer, int16_t delay);
extern int16_t  win_Events(void);
extern void  win_FlushEvents(void);
extern void  win_DrawObjectNum(int16_t objNum);
extern void  f_1E57_0FDC(struct Rect  *r);
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  f_24AB_02AD(int16_t font);
extern int16_t  f_24AB_030B(void);
extern void ( *  g_9188)(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t x, int16_t y);
extern void  gr_JustifyStrInRect(int16_t mode, struct Rect  *rect, char  *text);
extern void  clip_Off(void);
extern void  dos_free(char  *p);
extern void  db_PurgeObject(int16_t object, int16_t kind);

void  AboutDialog(void)
{
    int32_t count;
    char  *  *list;
    int16_t n;
    int32_t timer;
    struct Rect rect;
    struct Rect box;
    int16_t line;
    int16_t pix;
    int16_t drawn;
    int16_t height;
    int16_t y;
    int16_t idx;

    count = 0;
    win_Open(0x1f00);
    list = LoadStringAnt(0x6a4);
    for (n = 0; list[n] != 0; n++)
        ;
    for (;;) {
        timer = TickCount();
        DialogClearWait();
        while (!WaitedEnough(&timer, 0x5a)) {
            if (DialogAbortOrCont() || win_Events()) {
                if (count > 1)
                    goto out;
                win_FlushEvents();
                break;
            }
        }
        count++;
        win_GetObjRect(0x1f02, &rect);
        win_DrawObjectNum(0x1f01);
        f_1E57_0FDC(&rect);
        win_SetColorFromObjNum(0x1f02);
        line = 0;
        pix = 0;
        drawn = 0;
        while (line < n) {
            timer = TickCount();
            DialogClearWait();
            while (!WaitedEnough(&timer, (line == 0 && pix == 1) ? 0x36 : 1)) {
                if (DialogAbortOrCont() || win_Events()) {
                    if (count > 3)
                        goto out;
                    win_FlushEvents();
                    break;
                }
            }
            count++;
            f_24AB_02AD(4);
            height = f_24AB_030B();
            y = rect.top - pix;
            idx = line;
            if (drawn)
                (*g_9188)(rect.left, rect.top + 1, rect.right, rect.bottom, rect.left, rect.top);
            for (; y < rect.bottom; idx++, y += height) {
                if (idx < n && *list[idx] != 0) {
                    if (drawn && height + y < rect.bottom)
                        continue;
                    box.top = y;
                    box.bottom = height + y;
                    box.left = rect.left;
                    box.right = rect.right;
                    gr_JustifyStrInRect(3, &box, list[idx]);
                    (*g_9134)(SIM_GRAPHICS_SOURCE_g_3DA0, y, rect.right, height + y, SIM_GRAPHICS_SOURCE_g_3DE2);
                } else {
                    (*g_9134)(rect.left, y, rect.right, height + y, SIM_GRAPHICS_SOURCE_g_3DE2);
                }
            }
            if (++pix == height) {
                pix = 0;
                line++;
            }
            f_24AB_02AD(0);
            drawn = 1;
        }
        clip_Off();
        win_DrawObjectNum(0x1f02);
    }
out:
    dos_free((char  *)list);
    db_PurgeObject(0x6a4, 4);
    win_FlushEvents();
    win_Close(0x1f00);
}

extern Handle  f_171C_1A9E(int32_t size, int16_t flags, char  *name);
extern Handle  fd_50F6_3836;
extern Handle  fd_50F6_3938;
extern Handle  fd_50F6_3934;
extern char  *  f_171C_1B84(Handle h);

extern Handle  f_171C_1BBA(Handle h);
extern void  f_171C_1C0A(Handle h);
extern int16_t  win_IsWinOpen(int16_t win);

void  ShowIntro(void)
{
    char  *p;
    char  *a;
    char  *b;
    int16_t i;

    win_Open(0x300);
    myBeginSong(0x2711, 0x7e);
    DialogWaitInit(0x28);
    if (native_game_fd_50F6_10CC[0] != 0) {
        fd_50F6_3836 = f_171C_1A9E(0x28L, 1, "Malloc");
        fd_50F6_3938 = f_171C_1A9E(0x32L, 1, "Malloc");
        fd_50F6_3934 = f_171C_1A9E(0x1eL, 1, "Malloc");
        p = f_171C_1B84(native_game_fd_50F6_10CC[0]);
        a = f_171C_1B84(fd_50F6_3836);
        b = f_171C_1B84(fd_50F6_3938);
        _fmemcpy(a, p + 0x80, 0x1e);
        _fmemcpy(b, p + 0x9e, 0x1e);
        p = f_171C_1B84(fd_50F6_3934);
        for (i = 0; i < 0x100; i++) {
            a[i % 30] ^= (char)(i + 0x55);
            p[i % 8] = (a[i % 30] + p[i % 8] + i) % 10 + '0';
            b[i % 30] ^= (char)(i + 0x55);
        }
        p[8] = 0;
        f_171C_1BBA(native_game_fd_50F6_10CC[0]);
        f_171C_1C0A(native_game_fd_50F6_10CC[0]);
        native_game_fd_50F6_10CC[0] = 0;
        f_171C_1BBA(fd_50F6_3934);
        f_171C_1BBA(fd_50F6_3938);
        f_171C_1BBA(fd_50F6_3836);
    }
    while (win_IsWinOpen(0x300)) {
        if (win_Events() || DialogAbortOrCont())
            win_Close(0x300);
    }
    win_FlushEvents();
}

#pragma pack(pop)
