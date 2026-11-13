/*
 * Draws window frames, titles and objects. It includes colour selection, string justification
 * and button border helpers.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 21FA; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pt {
    int x;
    int y;
};

struct Sides {
    unsigned char left : 1;
    unsigned char top : 1;
    unsigned char right : 1;
    unsigned char bottom : 1;
};

extern int far font_FontHeight(void);
extern int far font_StringWidth(char far *text);
extern void far font_PrintStr(int x, int y, char far *text);
extern void far font_SetFont(int font);
extern void far GRectFill(struct Rect far *rect, int color);
extern void far GRectOutline(struct Rect far *rect, int width);
extern void far GRectPartialMixedOutline(struct Rect far *rect, int width, struct Sides sides, int light, int dark);
extern void far GRectPartialOutline(struct Rect far *rect, int width, struct Sides sides, int color);
extern void far GRectInv(struct Rect far *rect);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_UnlockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_Push(void);
extern void far clip_SubInclude(char far *obj);
extern void far clip_Pop(void);
extern void _fastcall list_draw_visible_rows(char far *obj);
extern void _fastcall win_draw_vertical_slider(char far *obj);
extern void _fastcall win_DrawBitMapAtObj(int id, struct Rect far *rect);
extern char far * far _fstrchr(char far *s, int c);
extern char far * far mem_Lock(char far * far *handle);
extern void far gr_BitMapSize(struct Pt far *size, int id);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void _fastcall win_LockWinHigh(int win);
extern char far * far win_locked_resource_ptr(int win);
extern int far sprintf(char far *buffer, char far *format, ...);
extern void far clip_set_desktop_region(void);
extern void far clip_restrict_rect(char far *p);
extern void far clip_SetWin(int win);
extern void far clip_Off(void);
extern void far clip_SubExclude(struct Rect far *rect);
extern void far win_redraw_desktop_menu(void);
extern void far mem_Unlock(char far * far *handle);

extern char near gfx_display_mode;
extern int near _foreColor;
extern char near gfx_font_height_pixels;
extern int near g_3DE2;
extern int gfx_text_pen_x;
extern int g_6300;
extern int clip_window_z_order[];
extern int near gfx_screen_width_pixels;
extern int far * near clip_active_list_offset;
extern void (far * far win_drawHooks[])(int phase);
extern char far win_colors[][6];
extern void (far * near gfx_set_attributes_hook)(int fore, int back, int pattern);
extern void (far * near gfx_fill_rect_hook)(int x0, int y0, int x1, int y1, int color);
extern void (far * near g_9138)(int left, int top, int right, int bottom, int mode);

static char far *colorEntry;

void _fastcall gr_JustifyStrInRect(int mode, struct Rect far *rect, char far *text)
{
    struct Rect r;
    int x;

    r = *rect;
    switch (mode) {
    case 0:
    case 3:
        x = (r.left + (r.right - font_StringWidth(text))) / 2;
        break;
    case 1:
        x = r.left + 4;
        break;
    case 2:
        x = r.right - font_StringWidth(text) - 4;
        break;
    }
    if (r.left > x)
        x = r.left;
    r.top = (r.bottom + (r.top - font_FontHeight())) / 2;
    font_PrintStr(x, r.top, text);
    if (mode == 3) {
        (*gfx_fill_rect_hook)(gfx_text_pen_x, r.top, rect->right, r.top + gfx_font_height_pixels, g_3DE2);
        (*gfx_fill_rect_hook)(rect->left, r.top, x, r.top + gfx_font_height_pixels, g_3DE2);
    }
}

void _fastcall win_SetColorNum(int color)
{
    colorEntry = win_colors[color];
    if ((gfx_display_mode & 1) == 0)
        (*gfx_set_attributes_hook)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*gfx_set_attributes_hook)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void _fastcall win_SetColorFromObj(char far *obj)
{
    if (obj[0x24] & 4)
        colorEntry = win_colors[obj[0x27]];
    else
        colorEntry = win_colors[obj[0x26]];
    if ((gfx_display_mode & 1) == 0)
        (*gfx_set_attributes_hook)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    else
        (*gfx_set_attributes_hook)(colorEntry[0] * 0x101, colorEntry[3] * 0x101, colorEntry[0] * 0x101);
}

void _fastcall win_SetColorFromObjNum(int obj)
{
    win_LockWin(obj);
    win_SetColorFromObj(win_ObjAddr(obj));
    win_UnlockWin(obj);
}

void _fastcall win_RectFill(struct Rect far *rect)
{
    if (colorEntry[2] != colorEntry[3] && (gfx_display_mode & 1) == 0) {
        (*gfx_set_attributes_hook)(colorEntry[3] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
        (*g_9138)(rect->left, rect->top, rect->right, rect->bottom, 0);
        (*gfx_set_attributes_hook)(colorEntry[0] * 0x101, colorEntry[2] * 0x101, colorEntry[0] * 0x101);
    } else
        GRectFill(rect, colorEntry[2] * 0x101);
}

void _fastcall win_FillObjRect(int obj, int color)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    GRectFill(&r, color);
}

void _fastcall win_RectFillOutline(int width, struct Rect far *rect)
{
    win_RectFill(rect);
    GRectOutline(rect, width);
}

void far win_RectOutline(struct Rect far *rect, int width)
{
    GRectOutline(rect, width);
}

void far win_RectVOutline(struct Rect far *rect, int width)
{
    struct Sides sides;

    sides.left = 0;
    sides.right = 0;
    sides.top = 1;
    sides.bottom = 1;
    GRectPartialMixedOutline(rect, width, sides, _foreColor, _foreColor);
}

void far win_RectHOutline(struct Rect far *rect, int width)
{
    struct Sides sides;

    sides.left = 1;
    sides.right = 1;
    sides.top = 0;
    sides.bottom = 0;
    GRectPartialMixedOutline(rect, width, sides, _foreColor, _foreColor);
}

void _fastcall win_DrawButtonBorder(char far *obj)
{
    struct Rect far *rect;
    char far *entry;
    struct Sides sides;
    int i;

    rect = (struct Rect far *)obj;
    entry = win_colors[obj[0x26]];
    if ((obj[0x24] & 4) == 0) {
        for (i = 3; i > 0; i--) {
            sides.left = 1;
            sides.right = 1;
            sides.top = 0;
            sides.bottom = 0;
            GRectPartialOutline(rect, i, sides, entry[3] * 0x101);
            sides.left = 0;
            sides.right = 0;
            sides.top = 1;
            sides.bottom = 1;
            GRectPartialMixedOutline(rect, i, sides, entry[2] * 0x101, entry[3] * 0x101);
        }
    } else {
        (*gfx_set_attributes_hook)(entry[0] * 0x101, entry[0] * 0x101, entry[0] * 0x101);
        GRectOutline(rect, 3);
        if ((gfx_display_mode & 1) == 0) {
            (*gfx_set_attributes_hook)(entry[3] * 0x101, entry[3] * 0x101, entry[1] * 0x101);
            GRectOutline(rect, 2);
        }
    }
}

/* Unclaimed draft below (win_DrawObjectI): bytes exact, but the FIXUPP order inside the
 * GRectFill and font_SetFont relocation groups differs (the original object had
 * LEDATA record breaks inside this function). */
struct WinObj {
    struct Rect rect;
    int origin[4];
    int ref[4];
    int mode[4];
    char unk20;
    char type;
    int size;
    int flags;
    int data[3];
};

void _fastcall win_DrawObjectI(struct WinObj far *obj)
{
    char far * far *h;
    char far *text;
    char far *p;
    struct Rect far *rect;

    rect = (struct Rect far *)obj;
    win_SetColorFromObj((char far *)obj);
    if (obj->flags & 0x200) {
        clip_Push();
        clip_SubInclude((char far *)obj);
    }
    switch (obj->type) {
    case 0:
        win_RectFillOutline(*(char far *)&obj->data[1], rect);
        break;
    case 2:
        win_RectFill(rect);
        break;
    case 4:
        list_draw_visible_rows((char far *)obj);
        break;
    case 5:
        GRectFill(rect, colorEntry[2] * 0x101);
        win_DrawButtonBorder((char far *)obj);
        win_SetColorFromObj((char far *)obj);
    case 9:
    plainText:
        text = (char far *)obj + 0x2a;
        goto drawText;
    case 6:
        win_DrawBitMapAtObj(obj->data[1], (struct Rect far *)obj);
        break;
    case 7:
    case 8:
        win_draw_vertical_slider((char far *)obj);
        break;
    case 12:
        win_RectFill(rect);
        (*gfx_fill_rect_hook)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto plainText;
    case 13:
        win_DrawBitMapAtObj(*(int far *)((char far *)obj->data + ((obj->flags & 4) ? 2 : 4)), (struct Rect far *)obj);
        break;
    case 15:
        win_RectOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 17:
        GRectFill(rect, colorEntry[2] * 0x101);
        win_DrawButtonBorder((char far *)obj);
        win_SetColorFromObj((char far *)obj);
    case 16:
    formatText:
        font_SetFont(*(char far *)&obj->data[1]);
        if (*(char far * far * far *)&obj->data[2] == 0) {
            text = (char far *)obj + 0x2e;
            if (g_6300 != 0 || _fstrchr(text, '%') == 0) {
        drawText:
                font_SetFont(*(char far *)&obj->data[1]);
                gr_JustifyStrInRect(((unsigned)obj->flags & 0x180) >> 7, rect, text);
            }
        } else {
            h = *(char far * far * far *)&obj->data[2];
            p = mem_Lock(h);
            gr_JustifyStrInRect(((unsigned)obj->flags & 0x180) >> 7, rect, p);
            mem_Unlock(h);
        }
        font_SetFont(0);
        break;
    case 18:
        win_RectFill(rect);
        (*gfx_fill_rect_hook)(rect->left, rect->bottom - 1, rect->right, rect->bottom, colorEntry[0] * 0x101);
        goto formatText;
    case 19:
        win_RectHOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 20:
        win_RectVOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 21:
        win_RectFill(rect);
        win_RectHOutline(rect, *(char far *)&obj->data[1]);
        break;
    case 22:
        win_RectFill(rect);
        win_RectVOutline(rect, *(char far *)&obj->data[1]);
        break;
    }
    if (obj->flags & 4) {
        switch (obj->type) {
        case 1:
        case 6:
            GRectInv((struct Rect far *)obj);
            break;
        }
    }
    if (obj->flags & 0x200)
        clip_Pop();
}

void _fastcall win_DrawObject(struct WinObj far *obj)
{
    if (obj->flags & 1)
        win_DrawObjectI(obj);
}

void _fastcall win_DrawObjectNum(int objNum)
{
    win_LockWin(objNum);
    win_DrawObjectI((struct WinObj far *)win_ObjAddr(objNum));
    win_UnlockWin(objNum);
}

void _fastcall win_draw_frame_controls(char far *w)
{
    struct Rect rect;
    struct Pt size;
    int m;

    rect = *(struct Rect far *)w;
    m = (*(char far * far *)(w + 0x2c))[0x28];
    rect.bottom -= m;
    if (gfx_screen_width_pixels == 0x140)
        m = m / 2;
    rect.left += m;
    rect.right -= m;
    rect.top += m;
    if (gfx_display_mode & 1)
        (*gfx_set_attributes_hook)(0, 0, 0x40);
    if (*(int far *)(w + 0x1c) & 4) {
        win_DrawBitMap(rect.left, rect.top, 0x64);
        gr_BitMapSize(&size, 0x64);
        rect.left += size.x;
    }
    if (*(int far *)(w + 0x1c) & 8) {
        gr_BitMapSize(&size, 0x70);
        win_DrawBitMap(rect.right - size.x, rect.bottom - size.y, 0x70);
    }
    if (*(int far *)(w + 0x1c) & 0x100) {
        if (*(int far *)(w + 0x1c) & 0x80) {
            gr_BitMapSize(&size, 0x66);
            rect.right -= size.x;
            win_DrawBitMap(rect.right, rect.top, 0x66);
        } else {
            gr_BitMapSize(&size, 0x67);
            rect.right -= size.x;
            win_DrawBitMap(rect.right, rect.top, 0x67);
        }
    }
    if (*(int far *)(w + 0x1c) & 0x10)
        win_DrawBitMap(rect.left, rect.top, 0x65);
    if (*(int far *)(w + 0x1c) & 0x400) {
        gr_BitMapSize(&size, 0x69);
        rect.right -= size.x;
        win_DrawBitMap(rect.right, rect.top, 0x69);
    }
}

/* Bytes exact; relocation order WITHIN_GROUP_PENDING: the original object breaks its
 * LEDATA record between 0A35 and 0A55 (sprintf group).  Under /Zi that is the 52-entry
 * line flush landing 9-10 line entries earlier than in this source (or a goto label). */
void _fastcall win_DrawWindow(int win)
{
    char buf[40];
    char far *w;
    int n;
    int i;

    sprintf(buf, "!!W:%x", win);
    win_LockWinHigh(win);
    sprintf(buf, "QQW:%x", win);
    w = win_locked_resource_ptr(win);
    if ((*(int far *)(w + 0x1c) & 0x20) == 0) {
        if (clip_active_list_offset != 0 && clip_active_list_offset[1] == (int)0x8000)
            goto hooks;
        sprintf(buf, "##W:%x", win);
        if (win_drawHooks[win >> 8])
            (*win_drawHooks[win >> 8])(1);
        sprintf(buf, "**W:%x", win);
        n = *(int far *)(w + 0xc);
        for (i = 0; i < n; i++) {
            sprintf(buf, "w:%x, i:%x", win, i);
            win_DrawObject(((struct WinObj far * far *)(w + 0x2c))[i]);
            if (i == 0)
                *(struct Rect far *)w = *((struct Rect far * far *)(w + 0x2c))[0];
            sprintf(buf, "xxw:%x, i:%x", win, i);
        }
        sprintf(buf, "zzw:%x, i:%x", win, i);
        win_draw_frame_controls(w);
hooks:
        sprintf(buf, "ppw:%x, i:%x", win, i);
        if (win_drawHooks[win >> 8])
            (*win_drawHooks[win >> 8])(2);
    }
    sprintf(buf, "%%w:%x, i:%x", win, i);
    win_UnlockWin(win);
}

void _fastcall win_DrawTitle(int win)
{
    win_DrawObjectNum(win);
    win_LockWin(win);
    win_draw_frame_controls(win_locked_resource_ptr(win));
    win_UnlockWin(win);
}

/*
 * Repaint the requested rectangle through the desktop and complete window stack.
 */
void _fastcall win_redraw_rect(char far *p)
{
    int i;

    clip_set_desktop_region();
    clip_restrict_rect(p);
    win_redraw_desktop_menu();
    for (i = 0; clip_window_z_order[i] != (int)0x8000; i++)
        ;
    while (--i >= 0) {
        clip_SetWin(clip_window_z_order[i]);
        clip_restrict_rect(p);
        win_DrawWindow(clip_window_z_order[i]);
    }
    clip_Off();
}

void _fastcall win_redraw_exposed_windows(char far *p)
{
    char buf[20];
    struct Rect r;
    int i;

    clip_set_desktop_region();
    clip_restrict_rect(p);
    if (clip_window_z_order[0] != (int)0x8000) {
        win_GetObjRect(clip_window_z_order[0], &r);
        clip_SubExclude(&r);
    }
    win_redraw_desktop_menu();
    for (i = 0; clip_window_z_order[i] != (int)0x8000; i++)
        ;
    while (--i >= 1) {
        clip_SetWin(clip_window_z_order[i]);
        sprintf(buf, "i:%x", i);
        clip_restrict_rect(p);
        sprintf(buf, "!!i:%x", i);
        clip_SubExclude(&r);
        sprintf(buf, "@@i:%x", i);
        win_DrawWindow(clip_window_z_order[i]);
    }
    if (clip_window_z_order[0] != (int)0x8000) {
        clip_SetWin(clip_window_z_order[0]);
        win_DrawWindow(clip_window_z_order[0]);
    }
    clip_Off();
}
