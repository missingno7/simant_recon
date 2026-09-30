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
extern void far f_24AB_02AD(int font);
extern struct Pt _fastcall win_StringSize(char far *text);
extern void far f_24AB_038D(int x, int y, char far *text);
extern void far clip_SubExclude(struct Rect far *rect);

void far f_15D9_0006(char far *text, struct Rect far *r, int y)
{
    struct Rect rc;
    struct Pt size;

    f_24AB_02AD(g_3DB2 == 0x140 ? 0 : 2);
    size = win_StringSize(text);
    rc.top = y;
    rc.left = (r->right - size.x + r->left) / 2;
    rc.right = rc.left + size.x;
    rc.bottom = y + size.y;
    f_24AB_038D(rc.left, y, text);
    clip_SubExclude(&rc);
    f_24AB_02AD(0);
}

extern int far fd_3D57_07A8[];
extern char far * far fd_55B3_19C6;
extern long far fd_55B3_19CA;
extern long far TickCount(void);
extern int far fd_55B3_19CE;
extern long far fd_55B3_299E;
extern char far * far fd_55B3_299A;
extern int far fd_55B3_29A2;

void far EditMessage(char far *message, long duration, int mode)
{
    if (mode == 0 && (fd_3D57_07A8[4] == 0 || fd_55B3_19C6 != 0L)) {
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
    if (message != fd_55B3_299A) {
        fd_55B3_299A = message;
        fd_55B3_29A2 = 1;
    }
}
