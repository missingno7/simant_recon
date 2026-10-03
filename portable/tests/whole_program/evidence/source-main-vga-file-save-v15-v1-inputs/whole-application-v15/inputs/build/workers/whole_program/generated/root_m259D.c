#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
/* Root module 259D: DOS picture drawing for window objects (partial). */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pic {
    int16_t type;
    char mode;
    char pad[5];
    int16_t width;
    int16_t height;
};

extern char  *  db_LoadObject(int16_t object, int16_t kind);
extern void  db_ReleaseObject(int16_t object, int16_t kind);
extern void  GPutPacked(int16_t x, int16_t y, char  *pic);
extern void  f_1B4E_003B(int16_t x, int16_t y, char  *image);
extern void  f_1B4E_005E(int16_t x, int16_t y, char  *image);
extern char  *  dos_malloc(uint16_t size);
extern void  dos_free(char  *block);
extern int16_t  WinPrintf(char  *format, ...);
extern void  o03_3258_040D(char  *image, char  *buffer, int16_t shift, int16_t flag);
extern void  o01_32B5_000F(char  *image, char  *buffer, int16_t shift, int16_t flag);
extern void  o00_35A6_0007(char  *image, char  *buffer, int16_t shift, int16_t flag);
extern void  f_1CE2_046D(struct Rect  *rect, int16_t color);
extern void  win_LockWin(int16_t win);
extern void  win_UnlockWin(int16_t win);
extern char  *  win_ObjAddr(int16_t obj);
extern int16_t  f_24AB_030B(void);
extern int16_t  f_24AB_0367(int16_t c);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);



extern uint16_t ( *  g_9140)(int16_t x0, int16_t y0, int16_t x1, int16_t y1);
extern void ( *  g_9148)(int16_t x0, int16_t y0, int16_t x1, int16_t y1, char  *buffer);

int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);

/* SCAFFOLD BEGIN: win_DrawBitMap remains inexact (675 vs 663 bytes).
 * Register and stack-home allocation remain unresolved.
 * This module follows original function order; no new code is claimed. */
int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id)
{
    char  *h;
    struct Pic  *pic;
    int16_t x1;
    int16_t y1;
    uint16_t n;

    h = db_LoadObject(id, 2);
    if (h != 0) {
        pic = *(struct Pic  *  *)h;
        if (pic->type == -1) {
            GPutPacked(x, y, (char  *)pic);
            db_ReleaseObject(id, 2);
            return 1;
        }
        if ((*(struct Pic  *  *)h)->type == (int16_t)0x8000) {
            GPutPacked(x, y, *(char  *  *)h);
            db_ReleaseObject(id, 2);
            return 1;
        }
        if (pic->type == 0) {
            if (pic->mode == 1)
                f_1B4E_005E(x, y, (char  *)pic + 8);
            else
                f_1B4E_003B(x, y, (char  *)pic + 8);
            db_ReleaseObject(id, 2);
            return 1;
        }
        if (pic->type == 3) {
            if (g_5A97 == 2) {
                x1 = ((x & ~1) + pic->width + 3) & ~1;
                y1 = pic->height + y;
                h = dos_malloc((*g_9140)(x & ~1, y, x1, y1));
                (*g_9148)(x & ~1, y, x1, y1, h);
                o03_3258_040D((char  *)pic + 8, h, x & 1, 0);
                f_1B4E_003B(x & ~1, y, h);
                dos_free(h);
            } else {
                x1 = ((x & ~7) + pic->width + 15) & ~7;
                y1 = pic->height + y;
                n = (*g_9140)(x & ~7, y, x1, y1);
                WinPrintf("\nGGetPic - trans @ %d, %d (%d, %d), bytes=%u", x & ~7, y, x1, y1, n);
                h = dos_malloc(n + 1);
                h[n] = 0xf3;
                (*g_9148)(x & ~7, y, x1, y1, h);
                WinPrintf("\nGPutPic size AA %d, %d, tag=%x", *(int16_t  *)h, *(int16_t  *)h + 2, (uint8_t)h[n]);
                if (g_5A97 & 1)
                    o01_32B5_000F((char  *)pic + 8, h, x & 7, 0);
                else
                    o00_35A6_0007((char  *)pic + 8, h, x & 7, 0);
                WinPrintf("\nGPutPic size %d, %d, tag=%x", *(int16_t  *)h, *(int16_t  *)h + 2, (uint8_t)h[n]);
                f_1B4E_003B(x & ~7, y, h);
                dos_free(h);
            }
        }
        db_ReleaseObject(id, 2);
        return 1;
    }
    return 0;
}
/* SCAFFOLD END */


void  win_DrawBitMapAtObj(int16_t id, struct Rect  *rect)
{
    if (!win_DrawBitMap(rect->left, rect->top, id))
        f_1CE2_046D(rect, SIM_GRAPHICS_SOURCE_g_3DE4 | SIM_GRAPHICS_SOURCE_g_3DE0);
}

void  win_DrawBitMapAtObjNum(int16_t obj, int16_t id)
{
    struct Rect  *rect;

    win_LockWin(obj);
    rect = (struct Rect  *)win_ObjAddr(obj);
    if (!win_DrawBitMap(rect->left, rect->top, id))
        f_1CE2_046D(rect, SIM_GRAPHICS_SOURCE_g_3DE4 | SIM_GRAPHICS_SOURCE_g_3DE0);
    win_UnlockWin(obj);
}

/* `start` (always 0, read only in `brk == start`) and the order of the chained zero
   assignment reproduce the original's two dead stores: MSC keeps the store of a local whose
   only read is later replaced by the propagated constant, and the home of the enregistered i
   receives its own store in chain position (worker resG).  The name is a hypothesis. */
void  win_PrintTextInRect(int16_t first, char  *text, struct Rect  *rect)
{
    int16_t c;
    int16_t start;
    int16_t pixw;
    int16_t brk;
    int16_t line;
    int16_t done;
    char  *p;
    int16_t y;
    int16_t w;
    int16_t lh;
    int16_t nlines;
    int16_t len;
    char buf[150];
    int16_t i;

    w = rect->right - rect->left;
    y = rect->top;
    lh = f_24AB_030B();
    nlines = (rect->bottom - rect->top) / lh;
    line = 0;
    while (*text) {
        if (first + nlines <= line)
            break;
        p = text;
        done = start = i = brk = pixw = 0;
        while (pixw < w && !done) {
            c = *p++;
            pixw += f_24AB_0367(c);
            if (pixw < w) {
                switch (c) {
                case 0:
                case 10:
                case 13:
                    done = 1;
                case ' ':
                case '(':
                case '[':
                case '{':
                    brk = i - 1;
                    break;
                case '!':
                case ')':
                case ',':
                case '-':
                case '.':
                case '?':
                case ']':
                case '}':
                    brk = i;
                    break;
                }
            }
            i++;
        }
        if (brk == start)
            brk = i - 1;
        if (first <= line) {
            len = brk + 1;
            _fstrncpy(buf, text, len);
            buf[len] = 0;
            f_24AB_038D(rect->left, y, buf);
        }
        text += len;
        while (*text == ' ')
            text++;
        if (*text == 10 || *text == 13)
            text++;
        y += lh;
        line++;
    }
}

#pragma pack(pop)
