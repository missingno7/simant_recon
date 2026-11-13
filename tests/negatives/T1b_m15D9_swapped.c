/* AUDIT T1b: the two functions in SWAPPED order (declarations kept first) */
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

extern int near g_3DB2;
extern void far font_SetFont(int font);
extern struct Pt _fastcall win_StringSize(char far *text);
extern void far font_PrintStr(int x, int y, char far *text);
extern void far clip_SubExclude(struct Rect far *rect);

extern int far OptionStates[];
extern char far * far fd_55B3_19C6;
extern long far fd_55B3_19CA;
extern long far TickCount(void);
extern int far fd_55B3_19CE;
extern long far fd_55B3_299E;
extern char far * far mapMessage;
extern int far fd_55B3_29A2;

void far EditMessage(char far *message, long duration, int mode)
{
    if (mode == 0 && (OptionStates[4] == 0 || fd_55B3_19C6 != 0L)) {
        if (message != 0L || fd_55B3_19CA != 0x7fffffffL)
            return;
    }
    if (duration >= 0L)
        fd_55B3_19CA = TickCount() + (duration * 3L) / 2L;
    else
        fd_55B3_19CA = 0x7fffffffL;
    if (message != fd_55B3_19C6) {
        fd_55B3_19C6 = message;
        fd_55B3_19CE = 1;
    }
    if (duration >= 0L)
        fd_55B3_299E = TickCount() + (duration * 3L) / 2L;
    else
        fd_55B3_299E = 0x7fffffffL;
    if (message != mapMessage) {
        mapMessage = message;
        fd_55B3_29A2 = 1;
    }
}

void far ui_draw_centered_clipped_text(char far *text, struct Rect far *r, int y)
{
    struct Rect rc;
    struct Pt size;

    font_SetFont(g_3DB2 == 0x140 ? 0 : 2);
    size = win_StringSize(text);
    rc.top = y;
    rc.left = (r->right - size.x + r->left) / 2;
    rc.right = rc.left + size.x;
    rc.bottom = y + size.y;
    font_PrintStr(rc.left, y, text);
    clip_SubExclude(&rc);
    font_SetFont(0);
}

