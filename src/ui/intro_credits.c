/*
 * Displays the intro, credits and simulation payoff animation. The three entries manage these
 * presentation sequences and their resources.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 16 (S16); segment 384C; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory.
 */

typedef char far * far *Handle;

#include "rect.h"

#include "event.h"

void far DrawSimPayoff(void);
void far AboutDialog(void);
void far ShowIntro(void);

static int g_2C2C[6][2] = {
    { 0x4a, 0x48 }, { 0x42, 0x57 }, { 0x40, 0xaf },
    { 0x42, 0xbf }, { 0x7a, 0x9f }, { 0x7c, 0xb3 }
};

extern void far MapToYard(void);
extern int far YardMode;
extern void far f_015B_0273(int mode);
extern int far MapPlane;
extern void far f_015B_053C(int plane);
extern void far DrawYard(void);
extern void far myDelay(long ticks);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_SetObjBitmap(int obj, int bitmap);
extern int near gfx_screen_width_pixels;
extern void _fastcall win_get_obj_layout_rect(int obj, struct Rect far *r);
extern struct Rect far menu_bar_rect;
extern void _fastcall win_set_obj_layout_rect(int obj, struct Rect far *r);
extern void far win_Open(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void _fastcall win_UnlockWin(int win);
extern long far MacTickCount(void);
extern void far DialogWaitInit(int ticks);
extern int far mySongIsDone(void);
extern void far myBeginSong(int id, int arg);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern int far DialogAbortOrCont(void);
extern void _fastcall win_Close(int win);

void far DrawSimPayoff(void)
{
    struct Rect rect;
    struct Rect saved;
    struct Rect bounds;
    long nextFrame;
    long deadline;
    int song;
    int row;
    int i;
    int x;
    int y;

    MapToYard();
    if (YardMode)
        f_015B_0273(0);
    if (MapPlane)
        f_015B_053C(0);
    DrawYard();
    myDelay(0x96L);
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, 0x3f48);
    if (gfx_screen_width_pixels == 0x140) {
        win_get_obj_layout_rect(0x1a01, &saved);
        bounds = saved;
        bounds.left = 4;
        bounds.top = menu_bar_rect.bottom + 3;
        win_set_obj_layout_rect(0x1a01, &bounds);
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
                if (gfx_screen_width_pixels == 0x140) {
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
    if (gfx_screen_width_pixels == 0x140)
        win_set_obj_layout_rect(0x1a01, &saved);
}

extern char far * far * far LoadStringAnt(int object);
extern unsigned long far TickCount(void);
extern void far DialogClearWait(void);
/* Prototype spelling is inferred: the unnamed timer and graphics-hook arguments
 * preserve this TU's declaration-number context without unrelated declarations.
 * The original header boundaries and parameter names are unknown. */
extern int far WaitedEnough(long far *, int);
extern int far win_Events(void);
extern void far win_FlushEvents(void);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void far clip_set_screen_intersection(struct Rect far *r);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far font_SetFont(int font);
extern int far font_FontHeight(void);
extern void (far * near gfx_copy_screen_rect_hook)(int, int, int, int, int, int);
extern void _fastcall gr_JustifyStrInRect(int mode, struct Rect far *rect, char far *text);
extern int near g_3DE2;
extern int far gfx_text_pen_x;
extern void (far * near gfx_fill_rect_hook)(int, int, int, int, int);
extern void far clip_Off(void);
extern void far free(char far *p);
extern void far db_PurgeObject(int object, int kind);

void far AboutDialog(void)
{
    long count;
    char far * far *list;
    int n;
    long timer;
    struct Rect rect;
    struct Rect box;
    int line;
    int pix;
    int drawn;
    int height;
    int y;
    int idx;

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
        clip_set_screen_intersection(&rect);
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
            font_SetFont(4);
            height = font_FontHeight();
            y = rect.top - pix;
            idx = line;
            if (drawn)
                (*gfx_copy_screen_rect_hook)(rect.left, rect.top + 1, rect.right, rect.bottom, rect.left, rect.top);
            for (; y < rect.bottom; idx++, y += height) {
                if (idx < n && *list[idx] != 0) {
                    if (drawn && height + y < rect.bottom)
                        continue;
                    box.top = y;
                    box.bottom = height + y;
                    box.left = rect.left;
                    box.right = rect.right;
                    gr_JustifyStrInRect(3, &box, list[idx]);
                    (*gfx_fill_rect_hook)(gfx_text_pen_x, y, rect.right, height + y, g_3DE2);
                } else {
                    (*gfx_fill_rect_hook)(rect.left, y, rect.right, height + y, g_3DE2);
                }
            }
            if (++pix == height) {
                pix = 0;
                line++;
            }
            font_SetFont(0);
            drawn = 1;
        }
        clip_Off();
        win_DrawObjectNum(0x1f02);
    }
out:
    free((char far *)list);
    db_PurgeObject(0x6a4, 4);
    win_FlushEvents();
    win_Close(0x1f00);
}

extern Handle far startup_info_block_handle[];
extern Handle far mem_Alloc(long size, int flags, char far *name);
extern Handle far fd_50F6_3836;
extern Handle far fd_50F6_3938;
extern Handle far fd_50F6_3934;
extern char far * far mem_Lock(Handle h);
extern void far * far _fmemcpy(void far *dest, void far *src, unsigned n);
extern Handle far mem_Unlock(Handle h);
extern void far mem_Free(Handle h);
extern int _fastcall win_IsWinOpen(int win);

void far ShowIntro(void)
{
    char far *p;
    char far *a;
    char far *b;
    int i;

    win_Open(0x300);
    myBeginSong(0x2711, 0x7e);
    DialogWaitInit(0x28);
    if (startup_info_block_handle[0] != 0) {
        fd_50F6_3836 = mem_Alloc(0x28L, 1, "Malloc");
        fd_50F6_3938 = mem_Alloc(0x32L, 1, "Malloc");
        fd_50F6_3934 = mem_Alloc(0x1eL, 1, "Malloc");
        p = mem_Lock(startup_info_block_handle[0]);
        a = mem_Lock(fd_50F6_3836);
        b = mem_Lock(fd_50F6_3938);
        _fmemcpy(a, p + 0x80, 0x1e);
        _fmemcpy(b, p + 0x9e, 0x1e);
        p = mem_Lock(fd_50F6_3934);
        for (i = 0; i < 0x100; i++) {
            a[i % 30] ^= (char)(i + 0x55);
            p[i % 8] = (a[i % 30] + p[i % 8] + i) % 10 + '0';
            b[i % 30] ^= (char)(i + 0x55);
        }
        p[8] = 0;
        mem_Unlock(startup_info_block_handle[0]);
        mem_Free(startup_info_block_handle[0]);
        startup_info_block_handle[0] = 0;
        mem_Unlock(fd_50F6_3934);
        mem_Unlock(fd_50F6_3938);
        mem_Unlock(fd_50F6_3836);
    }
    while (win_IsWinOpen(0x300)) {
        if (win_Events() || DialogAbortOrCont())
            win_Close(0x300);
    }
    win_FlushEvents();
}
