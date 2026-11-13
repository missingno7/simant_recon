/* Root module 15D9: centred ribbon text and the ribbon/yard message setter (Win16 EditMessage). */

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

extern int near gfx_screen_width_pixels;
extern void far font_SetFont(int font);
extern struct Pt _fastcall win_StringSize(char far *text);
extern void far font_PrintStr(int x, int y, char far *text);
extern void far clip_SubExclude(struct Rect far *rect);

void far ui_draw_centered_clipped_text(char far *text, struct Rect far *r, int y)
{
    struct Rect rc;
    struct Pt size;

    font_SetFont(gfx_screen_width_pixels == 0x140 ? 0 : 2);
    size = win_StringSize(text);
    rc.top = y;
    rc.left = (r->right - size.x + r->left) / 2;
    rc.right = rc.left + size.x;
    rc.bottom = y + size.y;
    font_PrintStr(rc.left, y, text);
    clip_SubExclude(&rc);
    font_SetFont(0);
}

extern int far OptionStates[];
extern char far * far editMessage;
extern long far edit_message_deadline;
extern long far pascal TickCount(void);  /* AUDIT T7: wrong calling convention */
extern int far edit_message_dirty;
extern long far map_message_deadline;
extern char far * far mapMessage;
extern int far map_yard_redraw_pending;

void far EditMessage(char far *message, long duration, int mode)
{
    if (mode == 0 && (OptionStates[4] == 0 || editMessage != 0L)) {
        if (message != 0L || edit_message_deadline != 0x7fffffffL)
            return;
    }
    if (duration >= 0L)
        edit_message_deadline = TickCount() + (duration * 3L) / 2L;
    else
        edit_message_deadline = 0x7fffffffL;
    if (message != editMessage) {
        editMessage = message;
        edit_message_dirty = 1;
    }
    if (duration >= 0L)
        map_message_deadline = TickCount() + (duration * 3L) / 2L;
    else
        map_message_deadline = 0x7fffffffL;
    if (message != mapMessage) {
        mapMessage = message;
        map_yard_redraw_pending = 1;
    }
}
