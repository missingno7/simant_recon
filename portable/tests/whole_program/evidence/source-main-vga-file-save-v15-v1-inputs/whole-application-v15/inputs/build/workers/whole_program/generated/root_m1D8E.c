#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect *g_5AAC;
/* Root module 1D8E: rectangle clipping against the clip-rectangle list. */
#define RECT_END ((int16_t)0x8000)

struct Pt {
    int16_t x;
    int16_t y;
};
extern int16_t  fd_55B3_3DE8;
extern int16_t  fd_55B3_3DE6;

extern void ( *  g_9150)(int16_t, int16_t, char  *, int16_t, int16_t);

int16_t  f_1D8E_0002(int16_t x, int16_t y, struct Rect  *r)
{
    int16_t code;

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

struct Rect  *  f_1D8E_003F(struct Rect  *r, struct Rect  *c,
                                  struct Rect  *in, struct Rect  *out)
{
    struct Rect t;
    int16_t code1;
    int16_t code2;

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

struct Rect  *  f_1D8E_02BD(struct Rect  *c, struct Rect  *list,
                                  struct Rect  *in, struct Rect  *out)
{
    struct Rect  *res;

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

void  f_1D8E_0384(void ( *fn)(int16_t, int16_t, int16_t, int16_t, int16_t), int16_t unused1, int16_t unused2,
                     int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t color)
{
    int16_t i;
    int16_t tmp;
    struct Rect  *clip;
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

void  f_1D8E_0435(char  *port, int16_t x1, int16_t y1, int16_t x2, int16_t y2, int16_t color)
{
    int32_t slope;
    struct Rect  *clip;
    int16_t code[2];
    struct Pt p[2];
    struct Rect line;
    int16_t i;

    if (y2 != y1)
        slope = ((int32_t)(x2 - x1) << 16) / (y2 - y1);
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
                    p[i].x += (int32_t)(clip->top - p[i].y) * slope / 0x10000L;
                    p[i].y = clip->top;
                    code[i] = f_1D8E_0002(p[i].x, p[i].y, clip);
                } else if (code[i] & 0x40) {
                    p[i].x += (int32_t)(clip->bottom - p[i].y) * slope / 0x10000L;
                    p[i].y = clip->bottom - 1;
                    code[i] = f_1D8E_0002(p[i].x, p[i].y, clip);
                }
                if (code[i] & 0x20) {
                    p[i].y += ((int32_t)(clip->left - p[i].x) << 16) / slope;
                    p[i].x = clip->left;
                } else if (code[i] & 0x10) {
                    p[i].y += ((int32_t)(clip->right - p[i].x) << 16) / slope;
                    p[i].x = clip->right - 1;
                }
            }
        }
        g_9170(p[0].x, p[0].y, p[1].x, p[1].y, color);
    }
}

void  f_1D8E_070E(char  *port, int16_t x, int16_t y, char  *bits, int16_t width, int16_t height)
{
    int16_t i;
    int16_t tmp;
    int16_t rowbytes;
    struct Rect  *clip;
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

void  f_1D8E_07F6(char  *port, int16_t x, int16_t y, char  *bits, int16_t width, int16_t height)
{
    int16_t i;
    int16_t tmp;
    int16_t rowbytes;
    struct Rect  *clip;
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

void  f_1D8E_08EA(char  *port, int16_t x, int16_t y, char  *bits, int16_t width, int16_t height)
{
    int16_t tmp;
    struct Rect  *p;
    int16_t tmp2;
    int16_t rowbytes;
    struct Rect  *clip;
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

void  f_1D8E_09DE(char  *port, int16_t x, int16_t y, char  *bits, int16_t width, int16_t height)
{
    int16_t tmp;
    struct Rect  *p;
    int16_t tmp2;
    int16_t rowbytes;
    struct Rect  *clip;
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

void  f_1D8E_0AC7(char  *port, int16_t x, int16_t y, char  *bits, int16_t width, int16_t height)
{
    int16_t tmp;
    struct Rect  *p;
    int16_t tmp2;
    int16_t rowbytes;
    struct Rect  *clip;
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

void  f_1D8E_0BAE(char  *port, int16_t x, int16_t y, char  *bits, int16_t width, int16_t height)
{
    int16_t tmp;
    struct Rect  *p;
    int16_t tmp2;
    int16_t rowbytes;
    struct Rect  *clip;
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

#pragma pack(pop)
