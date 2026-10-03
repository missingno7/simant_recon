#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_refs.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect *g_5AAC;
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

extern SimWindowRefRegistry sim_window_ref_registry;
/* Root module 21FA: DOS window-object drawing (partial). */
struct Pt {
    int16_t x;
    int16_t y;
};

struct Sides {
    uint8_t left : 1;
    uint8_t top : 1;
    uint8_t right : 1;
    uint8_t bottom : 1;
};

extern int16_t  f_24AB_030B(void);
extern int16_t  f_24AB_0329(char  *text);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);
extern void  f_24AB_02AD(int16_t font);
extern void  f_1CE2_046D(struct Rect  *rect, int16_t color);
extern void  f_1CE2_044D(struct Rect  *rect, int16_t width);
extern void  f_1CE2_09E2(struct Rect  *rect, int16_t width, struct Sides sides, int16_t light, int16_t dark);
extern void  f_1CE2_0278(struct Rect  *rect, int16_t width, struct Sides sides, int16_t color);
extern void  f_1CE2_0430(struct Rect  *rect);
extern void  win_LockWin(int16_t win);
extern void  win_UnlockWin(int16_t win);
extern char  *  win_ObjAddr(int16_t obj);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  clip_Push(void);
extern void  clip_SubInclude(char  *obj);
extern void  clip_Pop(void);
extern void  f_23E6_0392(char  *obj);
extern void  f_23E6_066C(char  *obj);
extern void  win_DrawBitMapAtObj(int16_t id, struct Rect  *rect);

extern char  *  f_171C_1B84(char  *  *handle);
extern void  f_208F_0419(struct Pt  *size, int16_t id);
extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);
extern void  win_LockWinHigh(int16_t win);
extern char  *  f_2505_0006(int16_t win);
extern void  f_1E57_0296(void);
extern void  f_1E57_0A9C(char  *p);
extern void  clip_SetWin(int16_t win);
extern void  clip_Off(void);
extern void  clip_SubExclude(struct Rect  *rect);
extern void  f_1FD2_05FD(void);
extern void  f_171C_1BBA(char  *  *handle);


extern int16_t g_6300;
extern int16_t g_5702[];
extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];
extern int8_t (*win_colors)[SIM_WINDOW_SOURCE_COLOR_BYTES];
extern void ( *  g_9138)(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t mode);

static char  *colorEntry;

void  gr_JustifyStrInRect(int16_t mode, struct Rect  *rect, char  *text)
{
    struct Rect r;
    int16_t x;

    r = *rect;
    switch (mode) {
    case 0:
    case 3:
        x = (r.left + (r.right - f_24AB_0329(text))) / 2;
        break;
    case 1:
        x = r.left + 4;
        break;
    case 2:
        x = r.right - f_24AB_0329(text) - 4;
        break;
    }
    if (r.left > x)
        x = r.left;
    r.top = (r.bottom + (r.top - f_24AB_030B())) / 2;
    f_24AB_038D(x, r.top, text);
    if (mode == 3) {
        (*g_9134)(SIM_GRAPHICS_SOURCE_g_3DA0, r.top, rect->right, r.top + SIM_GRAPHICS_SOURCE_g_3DDC, SIM_GRAPHICS_SOURCE_g_3DE2);
        (*g_9134)(rect->left, r.top, x, r.top + SIM_GRAPHICS_SOURCE_g_3DDC, SIM_GRAPHICS_SOURCE_g_3DE2);
    }
}

void  win_SetColorNum(int16_t color)
{
    colorEntry = win_colors[color];
    if ((g_5A97 & 1) == 0)
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void  win_SetColorFromObj(char  *obj)
{
    if (obj[0x24] & 4)
        colorEntry = win_colors[obj[0x27]];
    else
        colorEntry = win_colors[obj[0x26]];
    if ((g_5A97 & 1) == 0)
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void  win_SetColorFromObjNum(int16_t obj)
{
    win_LockWin(obj);
    win_SetColorFromObj(win_ObjAddr(obj));
    win_UnlockWin(obj);
}

void  win_RectFill(struct Rect  *rect)
{
    if (colorEntry[2] != colorEntry[3] && (g_5A97 & 1) == 0) {
        (*g_9128)(colorEntry[3] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
        (*g_9138)(rect->left, rect->top, rect->right, rect->bottom, 0);
        (*g_9128)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    } else
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
}

void  win_FillObjRect(int16_t obj, int16_t color)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    f_1CE2_046D(&r, color);
}

void  win_RectFillOutline(int16_t width, struct Rect  *rect)
{
    win_RectFill(rect);
    f_1CE2_044D(rect, width);
}

void  win_RectOutline(struct Rect  *rect, int16_t width)
{
    f_1CE2_044D(rect, width);
}

void  win_RectVOutline(struct Rect  *rect, int16_t width)
{
    struct Sides sides;

    sides.left = 0;
    sides.right = 0;
    sides.top = 1;
    sides.bottom = 1;
    f_1CE2_09E2(rect, width, sides, SIM_GRAPHICS_SOURCE_g_3DE0, SIM_GRAPHICS_SOURCE_g_3DE0);
}

void  win_RectHOutline(struct Rect  *rect, int16_t width)
{
    struct Sides sides;

    sides.left = 1;
    sides.right = 1;
    sides.top = 0;
    sides.bottom = 0;
    f_1CE2_09E2(rect, width, sides, SIM_GRAPHICS_SOURCE_g_3DE0, SIM_GRAPHICS_SOURCE_g_3DE0);
}

void  win_DrawButtonBorder(char  *obj)
{
    struct Rect  *rect;
    char  *entry;
    struct Sides sides;
    int16_t i;

    rect = (struct Rect  *)obj;
    entry = win_colors[obj[0x26]];
    if ((obj[0x24] & 4) == 0) {
        for (i = 3; i > 0; i--) {
            sides.left = 1;
            sides.right = 1;
            sides.top = 0;
            sides.bottom = 0;
            f_1CE2_0278(rect, i, sides, entry[3] * 0x101);
            sides.left = 0;
            sides.right = 0;
            sides.top = 1;
            sides.bottom = 1;
            f_1CE2_09E2(rect, i, sides, entry[2] * 0x101, entry[3] * 0x101);
        }
    } else {
        (*g_9128)(entry[0] * 0x101, entry[0] * 0x101, entry[0] * 0x101);
        f_1CE2_044D(rect, 3);
        if ((g_5A97 & 1) == 0) {
            (*g_9128)(entry[3] * 0x101, entry[3] * 0x101, entry[1] * 0x101);
            f_1CE2_044D(rect, 2);
        }
    }
}

/* Unclaimed draft below (win_DrawObjectI): bytes exact, but the FIXUPP order inside the
 * f_1CE2_046D and f_24AB_02AD relocation groups differs (the original object had
 * LEDATA record breaks inside this function). */
struct WinObj {
    struct Rect rect;
    int16_t origin[4];
    int16_t ref[4];
    int16_t mode[4];
    char unk20;
    char type;
    int16_t size;
    int16_t flags;
    int16_t data[3];
};

void  win_DrawObjectI(struct WinObj  *obj)
{
    char  *  *h;
    char  *text;
    char  *p;
    struct Rect  *rect;

    rect = (struct Rect  *)obj;
    win_SetColorFromObj((char  *)obj);
    if (obj->flags & 0x200) {
        clip_Push();
        clip_SubInclude((char  *)obj);
    }
    switch (obj->type) {
    case 0:
        win_RectFillOutline(*(char  *)&obj->data[1], rect);
        break;
    case 2:
        win_RectFill(rect);
        break;
    case 4:
        f_23E6_0392((char  *)obj);
        break;
    case 5:
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
        win_DrawButtonBorder((char  *)obj);
        win_SetColorFromObj((char  *)obj);
    case 9:
    plainText:
        text = (char  *)obj + 0x2a;
        goto drawText;
    case 6:
        win_DrawBitMapAtObj(obj->data[1], (struct Rect  *)obj);
        break;
    case 7:
    case 8:
        f_23E6_066C((char  *)obj);
        break;
    case 12:
        win_RectFill(rect);
        (*g_9134)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto plainText;
    case 13:
        win_DrawBitMapAtObj(*(int16_t  *)((char  *)obj->data + ((obj->flags & 4) ? 2 : 4)), (struct Rect  *)obj);
        break;
    case 15:
        win_RectOutline(rect, *(char  *)&obj->data[1]);
        break;
    case 17:
        f_1CE2_046D(rect, colorEntry[2] * 0x101);
        win_DrawButtonBorder((char  *)obj);
        win_SetColorFromObj((char  *)obj);
    case 16:
    formatText:
        f_24AB_02AD(*(char  *)&obj->data[1]);
        if (*sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)obj, 0x2a) == 0) {
            text = (char  *)obj + 0x2e;
            if (g_6300 != 0 || _fstrchr(text, '%') == 0) {
        drawText:
                f_24AB_02AD(*(char  *)&obj->data[1]);
                gr_JustifyStrInRect(((uint16_t)obj->flags & 0x180) >> 7, rect, text);
            }
        } else {
            h = *sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, (char *)obj, 0x2a);
            p = f_171C_1B84(h);
            gr_JustifyStrInRect(((uint16_t)obj->flags & 0x180) >> 7, rect, p);
            f_171C_1BBA(h);
        }
        f_24AB_02AD(0);
        break;
    case 18:
        win_RectFill(rect);
        (*g_9134)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto formatText;
    case 19:
        win_RectHOutline(rect, *(char  *)&obj->data[1]);
        break;
    case 20:
        win_RectVOutline(rect, *(char  *)&obj->data[1]);
        break;
    case 21:
        win_RectFill(rect);
        win_RectHOutline(rect, *(char  *)&obj->data[1]);
        break;
    case 22:
        win_RectFill(rect);
        win_RectVOutline(rect, *(char  *)&obj->data[1]);
        break;
    }
    if (obj->flags & 4) {
        switch (obj->type) {
        case 1:
        case 6:
            f_1CE2_0430((struct Rect  *)obj);
            break;
        }
    }
    if (obj->flags & 0x200)
        clip_Pop();
}

void  win_DrawObject(struct WinObj  *obj)
{
    if (obj->flags & 1)
        win_DrawObjectI(obj);
}

void  win_DrawObjectNum(int16_t objNum)
{
    win_LockWin(objNum);
    win_DrawObjectI((struct WinObj  *)win_ObjAddr(objNum));
    win_UnlockWin(objNum);
}

void  f_21FA_077D(char  *w)
{
    struct Rect rect;
    struct Pt size;
    int16_t m;

    rect = *(struct Rect  *)w;
    m = sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0][0x28];
    rect.bottom -= m;
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140)
        m = m / 2;
    rect.left += m;
    rect.right -= m;
    rect.top += m;
    if (g_5A97 & 1)
        (*g_9128)(0, 0, 0x40);
    if (*(int16_t  *)(w + 0x1c) & 4) {
        win_DrawBitMap(rect.left, rect.top, 0x64);
        f_208F_0419(&size, 0x64);
        rect.left += size.x;
    }
    if (*(int16_t  *)(w + 0x1c) & 8) {
        f_208F_0419(&size, 0x70);
        win_DrawBitMap(rect.right - size.x, rect.bottom - size.y, 0x70);
    }
    if (*(int16_t  *)(w + 0x1c) & 0x100) {
        if (*(int16_t  *)(w + 0x1c) & 0x80) {
            f_208F_0419(&size, 0x66);
            rect.right -= size.x;
            win_DrawBitMap(rect.right, rect.top, 0x66);
        } else {
            f_208F_0419(&size, 0x67);
            rect.right -= size.x;
            win_DrawBitMap(rect.right, rect.top, 0x67);
        }
    }
    if (*(int16_t  *)(w + 0x1c) & 0x10)
        win_DrawBitMap(rect.left, rect.top, 0x65);
    if (*(int16_t  *)(w + 0x1c) & 0x400) {
        f_208F_0419(&size, 0x69);
        rect.right -= size.x;
        win_DrawBitMap(rect.right, rect.top, 0x69);
    }
}

/* Bytes exact; relocation order WITHIN_GROUP_PENDING: the original object breaks its
 * LEDATA record between 0A35 and 0A55 (sprintf group).  Under /Zi that is the 52-entry
 * line flush landing 9-10 line entries earlier than in this source (or a goto label). */
void  win_DrawWindow(int16_t win)
{
    char buf[40];
    char  *w;
    int16_t n;
    int16_t i;

    dos_sprintf(buf, "!!W:%x", win);
    win_LockWinHigh(win);
    dos_sprintf(buf, "QQW:%x", win);
    w = f_2505_0006(win);
    if ((*(int16_t  *)(w + 0x1c) & 0x20) == 0) {
        if (g_5AAC != 0 && g_5AAC->top == (int16_t)0x8000)
            goto hooks;
        dos_sprintf(buf, "##W:%x", win);
        if (win_drawHooks[win >> 8])
            (*win_drawHooks[win >> 8])(1);
        dos_sprintf(buf, "**W:%x", win);
        n = sim_window_wire_read_i16(w, 0x0c);
        for (i = 0; i < n; i++) {
            dos_sprintf(buf, "w:%x, i:%x", win, i);
            win_DrawObject(((struct WinObj *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i]));
            if (i == 0)
                *(struct Rect  *)w = *((struct Rect *)sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0]);
            dos_sprintf(buf, "xxw:%x, i:%x", win, i);
        }
        dos_sprintf(buf, "zzw:%x, i:%x", win, i);
        f_21FA_077D(w);
hooks:
        dos_sprintf(buf, "ppw:%x, i:%x", win, i);
        if (win_drawHooks[win >> 8])
            (*win_drawHooks[win >> 8])(2);
    }
    dos_sprintf(buf, "%%w:%x, i:%x", win, i);
    win_UnlockWin(win);
}

void  win_DrawTitle(int16_t win)
{
    win_DrawObjectNum(win);
    win_LockWin(win);
    f_21FA_077D(f_2505_0006(win));
    win_UnlockWin(win);
}

void  f_21FA_0AD2(char  *p)
{
    int16_t i;

    f_1E57_0296();
    f_1E57_0A9C(p);
    f_1FD2_05FD();
    for (i = 0; g_5702[i] != (int16_t)0x8000; i++)
        ;
    while (--i >= 0) {
        clip_SetWin(g_5702[i]);
        f_1E57_0A9C(p);
        win_DrawWindow(g_5702[i]);
    }
    clip_Off();
}

void  f_21FA_0B4B(char  *p)
{
    char buf[20];
    struct Rect r;
    int16_t i;

    f_1E57_0296();
    f_1E57_0A9C(p);
    if (g_5702[0] != (int16_t)0x8000) {
        win_GetObjRect(g_5702[0], &r);
        clip_SubExclude(&r);
    }
    f_1FD2_05FD();
    for (i = 0; g_5702[i] != (int16_t)0x8000; i++)
        ;
    while (--i >= 1) {
        clip_SetWin(g_5702[i]);
        dos_sprintf(buf, "i:%x", i);
        f_1E57_0A9C(p);
        dos_sprintf(buf, "!!i:%x", i);
        clip_SubExclude(&r);
        dos_sprintf(buf, "@@i:%x", i);
        win_DrawWindow(g_5702[i]);
    }
    if (g_5702[0] != (int16_t)0x8000) {
        clip_SetWin(g_5702[0]);
        win_DrawWindow(g_5702[0]);
    }
    clip_Off();
}

/* Native layout guards for the source byte offsets. */
_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");
_Static_assert(offsetof(struct WinObj, data) + 2 * sizeof(((struct WinObj *)0)->data[0]) == 0x2a, "WinObj data[2] Handle offset");

#pragma pack(pop)
