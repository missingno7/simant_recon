/* Root module 0798: caste/mode control triangles (Win16 InitTriVars .. initControls unit). */

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

struct TriPoints {
    int apexX;
    int apexY;
    int leftX;
    int leftY;
    int rightX;
    int rightY;
};

struct TriLevel {
    unsigned frac;
    unsigned mid;
    unsigned weight;
};

struct CtlMsg {
    char pad[8];
    struct Pt pt;
    int code;
};

typedef char far * far *Handle;

char g_1B46[4] = { 36, 38, 34, 0 };
char g_1B4A[4] = { 40, 43, 39, 0 };
int g_1B4E = 0;
int g_1B50 = 0;
int g_1B52[8] = { 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000 };
int g_1B62 = 1;
int g_1B64 = 1;

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern unsigned far triWidth;
extern unsigned far triWidthR;
extern unsigned far triWidthL;
extern unsigned far triHeight;
extern long far fd_50F6_382E;

void far InitTriVars(int obj, struct TriPoints far *tri)
{
    struct Rect rect;
    unsigned half;

    win_GetObjRect(obj, &rect);
    triWidth = rect.right - rect.left;
    half = triWidth >> 1;
    triWidthR = half;
    triWidthL = half;
    triHeight = rect.bottom - rect.top;
    fd_50F6_382E = ((long)half << 8) / (long)triHeight;
    tri->apexX = half + rect.left;
    tri->apexY = rect.top;
    tri->leftY = tri->rightY = rect.bottom;
    tri->leftX = rect.left;
    tri->rightX = rect.right;
}

extern struct TriPoints far fd_50F6_3822;
void far SetTriLatPoint(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *out);
extern struct TriLevel far casteLevels;
extern struct Pt far fd_50F6_022E;
void far win_CasteControlClosed(void);

void far win_CasteControlChanged(void)
{
    InitTriVars(0x130d, &fd_50F6_3822);
    SetTriLatPoint(&casteLevels, &fd_50F6_3822, &fd_50F6_022E);
    win_CasteControlClosed();
}

extern struct TriPoints far fd_50F6_3816;
extern struct TriLevel far fd_50F6_049E;
extern struct Pt far fd_50F6_0358;
void far win_ModeControlClosed(void);

void far win_ModeControlChanged(void)
{
    InitTriVars(0x120d, &fd_50F6_3816);
    SetTriLatPoint(&fd_50F6_049E, &fd_50F6_3816, &fd_50F6_0358);
    win_ModeControlClosed();
}

extern void far win_Open(int win);

void far OpenCasteWindow(void)
{
    win_CasteControlChanged();
    win_Open(0x1300);
}

void far OpenModeWindow(void)
{
    win_ModeControlChanged();
    win_Open(0x1200);
}

extern void far clip_SetWin(int win);
extern void far DoWinHelp(int context);
extern int far CasteAuto;
extern void _fastcall win_MakeGroupInvisible(int win, int group);
extern void _fastcall win_MakeObjSelected(int obj);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);
extern struct TriLevel far fd_3D57_07F2[];
void far win_DrawCasteWindow(int flags);
int far IsPointInIsoTri(struct Pt far *pt, struct Rect far *r);
extern void _fastcall win_MakeGroupVisible(int win, int group);
extern int far _fmemcmp(void far *a, void far *b, unsigned n);
void far BoundPointToTri(struct Pt far *pt, struct Rect far *r);
void far GetTriLatDist(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *pt);
extern void far f_1FD2_04D0(struct Pt far *pt);
extern int far f_1FD2_0542(void);
void far cvtLevels2IdealCaste(int far *ideal);
extern int far IdealCaste[4];
extern void far f_1E57_0362(void);

void far ProcCasteEvent(struct CtlMsg far *msg)
{
    struct Rect rect;
    struct Pt last;

    clip_SetWin(0x1300);
    switch (msg->code - 0x1303) {
    case 0:
        DoWinHelp(0x130e);
        break;
    case 1:
        if (CasteAuto == 0) {
            CasteAuto = 1;
            win_MakeGroupInvisible(0x1300, 4);
        }
        break;
    case 3:
    case 4:
    case 5:
        win_MakeObjSelected(0x1305);
        _fmemcpy(&fd_3D57_07F2[g_1B4E], &casteLevels, 6);
        g_1B4E = msg->code - 0x1306;
        _fmemcpy(&casteLevels, &fd_3D57_07F2[g_1B4E], 6);
        clip_SetWin(0x1300);
        win_DrawCasteWindow(3);
    case 2:
        if (CasteAuto) {
            CasteAuto = 0;
            win_MakeGroupVisible(0x1300, 4);
        }
        break;
    case 10:
        win_GetObjRect(0x130d, &rect);
        if (!IsPointInIsoTri(&msg->pt, &rect))
            break;
        if (CasteAuto) {
            CasteAuto = 0;
            win_MakeObjSelected(0x1305);
            win_MakeGroupVisible(0x1300, 4);
        }
        last.x = -1;
        clip_SetWin(0x1300);
        do {
            if (_fmemcmp(&last, &msg->pt, 4)) {
                last = msg->pt;
                BoundPointToTri(&msg->pt, &rect);
                GetTriLatDist(&casteLevels, &fd_50F6_3822, &msg->pt);
                win_DrawCasteWindow(3);
            }
            f_1FD2_04D0(&msg->pt);
        } while (f_1FD2_0542());
        _fmemcpy(&fd_3D57_07F2[g_1B4E], &casteLevels, 6);
        cvtLevels2IdealCaste(IdealCaste);
        break;
    case 12:
    case 13:
    case 14:
        g_1B64 ^= 1;
        win_DrawCasteWindow(3);
        break;
    }
    f_1E57_0362();
}

extern int far ModeAuto;
extern struct TriLevel far fd_3D57_0810[];
void far win_DrawModeWindow(int flags);

void far ProcModeEvent(struct CtlMsg far *msg)
{
    struct Rect rect;
    struct Pt last;

    clip_SetWin(0x1200);
    switch (msg->code - 0x1203) {
    case 0:
        DoWinHelp(0x120e);
        break;
    case 1:
        if (ModeAuto == 0) {
            ModeAuto = 1;
            win_MakeGroupInvisible(0x1200, 4);
        }
        break;
    case 3:
    case 4:
    case 5:
        win_MakeObjSelected(0x1205);
        _fmemcpy(&fd_3D57_0810[g_1B50], &fd_50F6_049E, 6);
        g_1B50 = msg->code - 0x1206;
        _fmemcpy(&fd_50F6_049E, &fd_3D57_0810[g_1B50], 6);
        clip_SetWin(0x1200);
        win_DrawModeWindow(3);
    case 2:
        if (ModeAuto) {
            ModeAuto = 0;
            win_MakeGroupVisible(0x1200, 4);
        }
        break;
    case 10:
        win_GetObjRect(0x120d, &rect);
        if (!IsPointInIsoTri(&msg->pt, &rect))
            break;
        if (ModeAuto) {
            ModeAuto = 0;
            win_MakeObjSelected(0x1205);
            win_MakeGroupVisible(0x1200, 4);
        }
        last.x = -1;
        clip_SetWin(0x1200);
        do {
            if (_fmemcmp(&last, &msg->pt, 4)) {
                last = msg->pt;
                BoundPointToTri(&msg->pt, &rect);
                GetTriLatDist(&fd_50F6_049E, &fd_50F6_3816, &msg->pt);
                win_DrawModeWindow(3);
            }
            f_1FD2_04D0(&msg->pt);
        } while (f_1FD2_0542());
        _fmemcpy(&fd_3D57_0810[g_1B50], &fd_50F6_049E, 6);
        break;
    case 12:
    case 13:
    case 14:
        g_1B62 ^= 1;
        win_DrawModeWindow(3);
        break;
    }
    f_1E57_0362();
}

int far IsPointInIsoTri(struct Pt far *pt, struct Rect far *r)
{
    int top;
    int bottom;
    int right;
    int left;
    int mid;
    int x;
    int y;

    top = r->top;
    bottom = r->bottom;
    right = r->right;
    left = r->left;
    mid = (right + left) / 2;
    x = pt->x;
    y = pt->y;
    if (y >= bottom || y < top)
        return 0;
    if ((long)(left - mid) * (y - bottom) / (long)(bottom - top) + left > x)
        return 0;
    if ((long)(mid - right) * (y - top) / (long)(top - bottom) + mid < x)
        return 0;
    return 1;
}

void far BoundPointToTri(struct Pt far *pt, struct Rect far *r)
{
    int top;
    int bottom;
    int right;
    int left;
    int mid;
    int x;
    int y;
    int edge;

    top = r->top;
    bottom = r->bottom - 1;
    right = r->right;
    left = r->left;
    mid = (right + left) / 2;
    x = pt->x;
    y = pt->y;
    if (y > bottom)
        y = bottom;
    else if (y < top)
        y = top;
    edge = (long)(left - mid) * (y - bottom) / (long)(bottom - top) + left;
    if (edge > x)
        x = edge;
    else {
        edge = (long)(mid - right) * (y - top) / (long)(top - bottom) + mid;
        if (edge < x)
            x = edge;
    }
    pt->x = x;
    pt->y = y;
}

extern Handle far fd_50F6_37F6;
void far DrawControlLevels(int win, int unused, int percent);
extern Handle far hanim_MakeAnimSet(void);
extern struct Pt far knobSize;
extern int far hanim_AddAnimObject(Handle h, int x, int y, int pic, int pri);
extern int far fd_50F6_37FC;
extern void far hanim_SetObjectPos(int x, int y, int pic, Handle h, int id, int pri);
extern void far hanim_RenderAnimSet(Handle h);

void far win_DrawModeWindow(int flags)
{
    if (flags & 1) {
        if (!fd_50F6_37F6)
            clip_SetWin(0x1200);
    }
    if (!(flags & 2))
        return;
    DrawControlLevels(0x1200, 0, g_1B62);
    SetTriLatPoint(&fd_50F6_049E, &fd_50F6_3816, &fd_50F6_0358);
    if (!fd_50F6_37F6) {
        fd_50F6_37F6 = hanim_MakeAnimSet();
        fd_50F6_37FC = hanim_AddAnimObject(fd_50F6_37F6, fd_50F6_0358.x - knobSize.x / 2,
                                   fd_50F6_0358.y - knobSize.y / 2, 0x578, 0);
    } else
        hanim_SetObjectPos(fd_50F6_0358.x - knobSize.x / 2, fd_50F6_0358.y - knobSize.y / 2,
                    0x8000, fd_50F6_37F6, fd_50F6_37FC, 0x8000);
    hanim_RenderAnimSet(fd_50F6_37F6);
}

extern void far hanim_RemoveAnimSet(Handle h);

void far win_ModeControlClosed(void)
{
    if (fd_50F6_37F6) {
        hanim_RemoveAnimSet(fd_50F6_37F6);
        fd_50F6_37F6 = 0;
    }
}

extern Handle far fd_50F6_37F2;
extern int far fd_50F6_37FA;

void far win_DrawCasteWindow(int flags)
{
    if (flags & 1) {
        if (!fd_50F6_37F2)
            clip_SetWin(0x1300);
    }
    if (!(flags & 2))
        return;
    DrawControlLevels(0x1300, 0, g_1B64);
    SetTriLatPoint(&casteLevels, &fd_50F6_3822, &fd_50F6_022E);
    if (!fd_50F6_37F2) {
        fd_50F6_37F2 = hanim_MakeAnimSet();
        fd_50F6_37FA = hanim_AddAnimObject(fd_50F6_37F2, fd_50F6_022E.x - knobSize.x / 2,
                                   fd_50F6_022E.y - knobSize.y / 2, 0x578, 0);
    } else
        hanim_SetObjectPos(fd_50F6_022E.x - knobSize.x / 2, fd_50F6_022E.y - knobSize.y / 2,
                    0x8000, fd_50F6_37F2, fd_50F6_37FA, 0x8000);
    hanim_RenderAnimSet(fd_50F6_37F2);
}

void far win_CasteControlClosed(void)
{
    if (fd_50F6_37F2) {
        hanim_RemoveAnimSet(fd_50F6_37F2);
        fd_50F6_37F2 = 0;
    }
}

extern int near g_3DB2;
extern void far f_24AB_02AD(int font);
extern int far fd_50F6_0B12[3];
extern int far fd_50F6_0AEC;
extern void far win_PrintfAtObj(int obj, char far *format, ...);
extern void far f_22BF_0C38(int obj);
extern int far f_1B4E_000D(int color);
extern void far f_1CE2_046D(struct Rect far *r, int color);
extern void (far * near g_9128)(int fore, int back, int pattern);
extern void far f_1CE2_044D(struct Rect far *r, int width);

void far DrawControlLevels(int win, int unused, int percent)
{
    struct Rect rect;
    struct Rect r;
    char far *colors;
    unsigned far *levels;
    int h;
    long total;
    int w;
    int i;
    int obj;
    long val;
    int color;
    int x;      /* x, y, j: unused (identifier count, see promotion --steered) */
    int y;
    int j;

    f_24AB_02AD(g_3DB2 == 0x140 ? 0 : 4);
    win_GetObjRect((win & 0xff00) + 12, &rect);
    w = (rect.right - rect.left) / 5;
    h = rect.bottom - rect.top;
    if (win == 0x1200) {
        levels = (unsigned far *)&fd_50F6_049E;
        colors = g_1B4A;
        total = (long)fd_50F6_0B12[2] + fd_50F6_0B12[1] + fd_50F6_0B12[0];
    } else {
        levels = (unsigned far *)&casteLevels;
        colors = g_1B46;
        total = fd_50F6_0AEC;
    }
    for (i = 0; i < 3; i++) {
        obj = (win & 0xff00) + i + 9;
        if (percent) {
            val = (100L * levels[i] + 0x3fff) / 0xffff;
            win_PrintfAtObj(obj, "%-ld%%", val);
        } else {
            val = (levels[i] * (unsigned long)total + 0x3fff) / 0xffff;
            win_PrintfAtObj(obj, "%-ld", val);
        }
        f_22BF_0C38(obj);
        r.left = w * i * 2 + rect.left;
        r.right = r.left + w;
        r.bottom = rect.bottom;
        r.top = (long)levels[i] * h / -65535L + rect.bottom;
        if (r.top + 1 < rect.bottom) {
            color = f_1B4E_000D(colors[i]);
            f_1CE2_046D(&r, color);
            (*g_9128)(f_1B4E_000D(15), f_1B4E_000D(15), 0);
            f_1CE2_044D(&r, 1);
        } else
            r.top = rect.bottom;
        r.bottom = r.top;
        r.top = rect.top - 1;
        f_1CE2_046D(&r, f_1B4E_000D(0x40));
    }
    f_24AB_02AD(0);
}

void far cvtLevels2IdealCaste(int far *ideal)
{
    ideal[0] = (100UL * (&casteLevels.frac)[1] + 0x3fff) / 0xffff;
    ideal[1] = (100UL * (&casteLevels.frac)[2] + 0x3fff) / 0xffff;
    ideal[2] = (50UL * (&casteLevels.frac)[0] + 0x3fff) / 0xffff;
    ideal[3] = (50UL * (&casteLevels.frac)[0] + 0x3fff) / 0xffff;
}

void far GetTriLatDist(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *pt)
{
    int dx;
    int dy;
    int row;
    unsigned w;

    dx = pt->x - tri->leftX;
    dy = pt->y - tri->apexY;
    if ((unsigned)dy > triHeight - 2)
        level->frac = 0;
    else
        level->frac = (long)(triHeight - dy - 2) * 0xffffL / (long)(triHeight - 2);
    w = (unsigned long)level->frac * triWidthL / 0xffffUL;
    row = triWidth - w * 2;
    if (row <= 2) {
        level->weight = level->mid = 0;
        return;
    }
    if (dx - (int)w >= row - 2)
        level->weight = 0xffff - level->frac;
    else if (dx - (int)w <= 2)
        level->weight = 0;
    else
        level->weight = (0xffffL - level->frac) * (long)(dx - (int)w) / (long)(row - 2);
    level->mid = 0xffff - level->weight - level->frac;
}

void far SetTriLatPoint(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *out)
{
    unsigned w;
    int row;

    out->y = (triHeight - 2) * (0xffffUL - level->frac) / 0xffffUL + tri->apexY;
    w = (unsigned long)triWidthL * level->frac / 0xffffUL;
    row = triWidth - w * 2;
    if (level->frac == 0xffff || row < 3)
        out->x = tri->apexX + 2;
    else
        out->x = (long)(row - 3) * level->weight / (long)(0xffffU - level->frac) + tri->leftX + w + 2;
}

extern void far f_208F_0419(struct Pt far *size, int id);
extern int far fd_50F6_0468;
extern int far fd_3D57_07EA;
extern int far fd_50F6_0370;
extern int far fd_50F6_024E;
extern int far fd_3D57_080A[3];
extern int far fd_3D57_07EC[3];

void far initControls(void)
{
    struct Rect rect;
    int i;

    f_208F_0419(&knobSize, 0x578);
    win_GetObjRect(0x120d, &rect);
    ModeAuto = 1;
    CasteAuto = 1;
    fd_50F6_0468 = 1;
    fd_3D57_07EA = 1;
    fd_50F6_0370 = -1;
    fd_50F6_024E = -1;
    for (i = 0; i < 3; i++) {
        (&fd_50F6_049E.frac)[i] = fd_3D57_080A[i];
        (&fd_3D57_0810[0].frac)[i] = fd_3D57_080A[i];
        (&casteLevels.frac)[i] = fd_3D57_07EC[i];
        (&fd_3D57_07F2[0].frac)[i] = fd_3D57_07EC[i];
    }
    win_ModeControlChanged();
    win_CasteControlChanged();
    cvtLevels2IdealCaste(IdealCaste);
}
