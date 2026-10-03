/* Root module 1D8E: rectangle clipping against the clip-rectangle list. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

#define RECT_END ((int)0x8000)

struct Pt {
    int x;
    int y;
};

extern struct Rect far * near g_5AAC;
extern void (far * near g_9170)(int, int, int, int, int);
extern int far fd_55B3_3DE8;
extern int far fd_55B3_3DE6;
extern void (far * near g_9158)(int, int, char far *, int, int);
extern char near g_5A97;
extern void (far * near g_9150)(int, int, char far *, int, int);

int far f_1D8E_0002(int x, int y, struct Rect far *r)
{
    int code;

    code = 0;
    if (y < r->top)
        code = 0x80;
    else if (y >= r->bottom)
        code = 0x40;
    if (x < r->left)
        code += 0x20;
    else if (x >= r->right)
        code += 0x10;
    return code;
}

struct Rect far * far f_1D8E_003F(struct Rect far *r, struct Rect far *c,
                                  struct Rect far *in, struct Rect far *out)
{
    struct Rect t;
    int code1;
    int code2;

    t = *r;
    code1 = f_1D8E_0002(r->left, r->top, c);
    code2 = f_1D8E_0002(r->right - 1, r->bottom - 1, c);
    if (code1 & code2) {
        if (out) {
            *out++ = *r;
            if (in)
                goto mark_in;
            goto mark_out;
        }
    } else if (code1 || code2) {
        goto clip;
    } else {
        if (in)
            *in++ = *r;
        if (out)
            goto mark_out;
    }
    in->top = RECT_END;
    return in;
clip:
    if (out) {
        if (code1 & 0x80) {
            out->top = t.top;
            out->bottom = c->top;
            out->left = t.left;
            out->right = t.right;
            out++;
            t.top = c->top;
        }
        if (code2 & 0x40) {
            out->top = c->bottom;
            out->bottom = t.bottom;
            out->left = t.left;
            out->right = t.right;
            out++;
            t.bottom = c->bottom;
        }
        if (code1 & 0x20) {
            out->top = t.top;
            out->bottom = t.bottom;
            out->left = t.left;
            out->right = c->left;
            out++;
            t.left = c->left;
        }
        if (code2 & 0x10) {
            out->top = t.top;
            out->bottom = t.bottom;
            out->left = c->right;
            out->right = r->right;
            out++;
            t.right = c->right;
        }
        if (in) {
            *in++ = t;
mark_in:
            in->top = RECT_END;
        }
mark_out:
        out->top = RECT_END;
        return out;
    }
    if (in == 0)
        return 0;
    if (code1 & 0x80)
        t.top = c->top;
    if (code2 & 0x40)
        t.bottom = c->bottom;
    if (code1 & 0x20)
        t.left = c->left;
    if (code2 & 0x10)
        t.right = c->right;
    *in++ = t;
    in->top = RECT_END;
    return in;
}

struct Rect far * far f_1D8E_02BD(struct Rect far *c, struct Rect far *list,
                                  struct Rect far *in, struct Rect far *out)
{
    struct Rect far *res;

    if (out == 0)
        res = in;
    if (list && list->top != RECT_END) {
        for (; list->top != RECT_END; list++) {
            res = f_1D8E_003F(list, c, in, out);
            if (out)
                out = res;
            else
                in = res;
        }
    } else {
        if (out)
            res = out;
        else {
            *in = *c;
            res = in + 1;
        }
        res->top = RECT_END;
    }
    return res;
}

void far f_1D8E_0384(void (far *fn)(int, int, int, int, int), int unused1, int unused2,
                     int left, int top, int right, int bottom, int color)
{
    int i;
    int tmp;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    if (top > bottom) {
        tmp = top;
        top = bottom;
        bottom = tmp;
    }
    if (left > right) {
        tmp = left;
        left = right;
        right = tmp;
    }
    r.top = top;
    r.left = left;
    r.right = right;
    r.bottom = bottom;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (i = 0; pieces[i].top != RECT_END; i++)
            fn(pieces[i].left, pieces[i].top, pieces[i].right, pieces[i].bottom, color);
    }
}

void far f_1D8E_0435(char far *port, int x1, int y1, int x2, int y2, int color)
{
    long slope;
    struct Rect far *clip;
    int code[2];
    struct Pt p[2];
    struct Rect line;
    int i;

    if (y2 != y1)
        slope = ((long)(x2 - x1) << 16) / (y2 - y1);
    else
        slope = 0;
    line.top = y1;
    line.left = x1;
    line.right = x2;
    line.bottom = y2;
    p[0].x = line.left;
    p[0].y = line.top;
    p[1].x = line.right;
    p[1].y = line.bottom;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        code[0] = f_1D8E_0002(x1, y1, clip);
        code[1] = f_1D8E_0002(x2, y2, clip);
        if (code[0] & code[1])
            continue;
        if (code[1] == 0 && code[0] == 0) {
            g_9170(x1, y1, x2, y2, color);
            return;
        }
        for (i = 0; i < 2; i++) {
            if (slope == 0) {
                if (code[i] == 0)
                    continue;
                if (code[i] & 0x80)
                    p[i].y = clip->top;
                else if (code[i] & 0x40)
                    p[i].y = clip->bottom - 1;
                else if (code[i] & 0x20)
                    p[i].x = clip->left;
                else
                    p[i].x = clip->right - 1;
            } else {
                if (code[i] & 0x80) {
                    p[i].x += (long)(clip->top - p[i].y) * slope / 0x10000L;
                    p[i].y = clip->top;
                    code[i] = f_1D8E_0002(p[i].x, p[i].y, clip);
                } else if (code[i] & 0x40) {
                    p[i].x += (long)(clip->bottom - p[i].y) * slope / 0x10000L;
                    p[i].y = clip->bottom - 1;
                    code[i] = f_1D8E_0002(p[i].x, p[i].y, clip);
                }
                if (code[i] & 0x20) {
                    p[i].y += ((long)(clip->left - p[i].x) << 16) / slope;
                    p[i].x = clip->left;
                } else if (code[i] & 0x10) {
                    p[i].y += ((long)(clip->right - p[i].x) << 16) / slope;
                    p[i].x = clip->right - 1;
                }
            }
        }
        g_9170(p[0].x, p[0].y, p[1].x, p[1].y, color);
    }
}

void far f_1D8E_070E(char far *port, int x, int y, char far *bits, int width, int height)
{
    int i;
    int tmp;
    int rowbytes;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    rowbytes = (width + 7) / 8;
    r.top = y;
    r.left = x;
    r.right = x + width;
    r.bottom = y + height;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (i = 0; pieces[i].top != RECT_END; i++) {
            fd_55B3_3DE8 = r.right - pieces[i].right;
            fd_55B3_3DE6 = pieces[i].left - r.left;
            g_9158(x, pieces[i].top, bits + (pieces[i].top - y) * rowbytes, width,
                   pieces[i].bottom - pieces[i].top);
        }
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
}

void far f_1D8E_07F6(char far *port, int x, int y, char far *bits, int width, int height)
{
    int i;
    int tmp;
    int rowbytes;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    rowbytes = (width + 7) / 8;
    if ((g_5A97 & 1) == 0)
        rowbytes <<= 2;
    r.left = x;
    r.right = x + width;
    r.top = y;
    r.bottom = y + height;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (i = 0; pieces[i].top != RECT_END; i++) {
            fd_55B3_3DE8 = r.right - pieces[i].right;
            fd_55B3_3DE6 = pieces[i].left - r.left;
            g_9150(x, pieces[i].top, bits + (pieces[i].top - y) * rowbytes, width,
                   pieces[i].bottom - pieces[i].top);
        }
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
}

void far f_1D8E_08EA(char far *port, int x, int y, char far *bits, int width, int height)
{
    int tmp;
    struct Rect far *p;
    int tmp2;
    int rowbytes;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    rowbytes = (width + 7) / 8;
    r.top = y;
    r.left = x;
    r.right = x + width;
    r.bottom = y + height;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (p = pieces; p->top != RECT_END; p++) {
            fd_55B3_3DE8 = r.right - p->right;
            fd_55B3_3DE6 = p->left - r.left;
            g_9158(x, p->top, bits + (p->top - y) * rowbytes, width, p->bottom - p->top);
        }
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
}

void far f_1D8E_09DE(char far *port, int x, int y, char far *bits, int width, int height)
{
    int tmp;
    struct Rect far *p;
    int tmp2;
    int rowbytes;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    rowbytes = (width + 1) / 2;
    r.top = y;
    r.left = x;
    r.right = x + width;
    r.bottom = y + height;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (p = pieces; p->top != RECT_END; p++) {
            fd_55B3_3DE8 = r.right - p->right;
            fd_55B3_3DE6 = p->left - r.left;
            g_9150(x, p->top, bits + (p->top - y) * rowbytes, width, p->bottom - p->top);
        }
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
}

void far f_1D8E_0AC7(char far *port, int x, int y, char far *bits, int width, int height)
{
    int tmp;
    struct Rect far *p;
    int tmp2;
    int rowbytes;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    rowbytes = width;
    r.top = y;
    r.left = x;
    r.right = x + width;
    r.bottom = y + height;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (p = pieces; p->top != RECT_END; p++) {
            fd_55B3_3DE8 = r.right - p->right;
            fd_55B3_3DE6 = p->left - r.left;
            g_9150(x, p->top, bits + (p->top - y) * rowbytes, width, p->bottom - p->top);
        }
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
}

void far f_1D8E_0BAE(char far *port, int x, int y, char far *bits, int width, int height)
{
    int tmp;
    struct Rect far *p;
    int tmp2;
    int rowbytes;
    struct Rect far *clip;
    struct Rect r;
    struct Rect pieces[10];

    rowbytes = width;
    r.top = y;
    r.left = x;
    r.right = x + width;
    r.bottom = y + height;
    for (clip = g_5AAC; clip->top != RECT_END; clip++) {
        f_1D8E_003F(&r, clip, pieces, 0);
        for (p = pieces; p->top != RECT_END; p++) {
            fd_55B3_3DE8 = r.right - p->right;
            fd_55B3_3DE6 = p->left - r.left;
            g_9158(x, p->top, bits + (p->top - y) * rowbytes, width, p->bottom - p->top);
        }
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
}
