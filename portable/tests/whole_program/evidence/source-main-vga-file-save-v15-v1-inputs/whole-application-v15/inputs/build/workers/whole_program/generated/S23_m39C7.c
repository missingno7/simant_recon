#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/platform/crt_abi.h"
#pragma pack(push, 2)
/* Overlay section S23, code frame 39C7: info window and card display. */

int16_t g_2E04[16] = { 0 };
int16_t g_2E24 = 0;
int16_t g_2E26 = 0x80;

void  XFlipLong(uint16_t  *words)
{
    uint16_t first = words[0];
    words[0] = words[1];
    words[1] = first;
}

void  FlipWords(uint8_t  *bytes, int32_t length)
{
    int32_t i;
    uint8_t saved;

    for (i = 0L; i < length; i += 2L) {
        saved = bytes[i];
        bytes[i] = bytes[i + 1L];
        bytes[i + 1L] = saved;
    }
}

void  DisplayCard(int16_t card);

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct HotSpot {
    struct Rect r;
    int16_t id;
};

struct TextRez {
    char name[32];
    int16_t id;
};

struct StyleRun {
    int32_t pos;
    int16_t height;
    int16_t ascent;
    int16_t font;
    int16_t face;
    int16_t size;
    int16_t color[3];
};

static struct HotSpot  fd_4EE5_0000[64];
static struct HotSpot  fd_4EE5_0280[64];
struct TextRez  fd_4EE5_0500[] = {
    { "HIGHLIGHTED", 901 },
    { "CHITIN", 910 },
    { "MAXILLAE", 911 },
    { "OCELLI", 912 },
    { "INFRABUCCAL", 913 },
    { "CROP", 914 },
    { "MIDGUT", 915 },
    { "TROPHALLAXIS", 916 },
    { "CASTE", 917 },
    { "LARVAE", 918 },
    { "PUPATE", 919 },
    { "CASTES", 920 },
    { "PUPAE", 921 },
    { "ECLOSE", 922 },
    { "CALLOWS", 923 },
    { "PHEROMONES", 924 },
    { "BROOD", 925 },
    { "HONEYDEW", 926 },
    { "APHIDS", 927 },
    { "BREEDERS", 928 },
    { "RECRUIT", 929 },
    { "FORAGE", 963 },
    { "FORAGING", 964 },
    { "QUEENCHAMBER", 965 },
    { "NURSERIES", 966 },
    { "EGGS", 967 },
    { "NOP", 0 }
};

void  win_DrawInfoWindow(int16_t flags)
{
    if (flags & 2)
        DisplayCard(g_2E26);
}

static int16_t g_8C22;
static int16_t g_8C24;

extern void  f_24AB_02AD(int16_t font);
extern int16_t  f_24AB_030B(void);
extern void  Punt(char  *format, ...);

extern int16_t  WinPrintf(char  *format, ...);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);


extern int16_t  f_24AB_0367(int16_t c);

/* SCAFFOLD BEGIN: (split from a shared block by autosearch) */
void  win_PrintStyleTextInRect(char  *text, int16_t  *styl, struct Rect  *rect,
                                  int16_t firstLine, int16_t font1, int16_t font2, int16_t record)
{
    char buf[120];
    int16_t end;
    int16_t n;
    int16_t x;
    int16_t start;
    int16_t brk;
    int16_t done;
    int16_t w;
    int16_t line;
    int16_t maxLines;
    int16_t lineH;
    int16_t y;
    int16_t width;
    int16_t len;
    int16_t pos;
    int16_t styleIdx;
    struct StyleRun  *styles;

    styleIdx = 0;
    pos = 0;
    styles = styl ? (struct StyleRun  *)(styl + 1) : 0;
    len = _fstrlen(text);
    width = rect->right - rect->left;
    y = rect->top + 4;
    f_24AB_02AD(font1);
    lineH = f_24AB_030B();
    f_24AB_02AD(font2);
    if (f_24AB_030B() > lineH)
        lineH = f_24AB_030B();
    maxLines = (rect->bottom - rect->top) / lineH;
    if (record)
        g_8C24 = 0;
    if (styl && styles->face == 0x100)
        f_24AB_02AD(font2);
    else
        f_24AB_02AD(font1);
    for (line = 0; pos < len && line < firstLine + maxLines; line++) {
        w = 0;
        done = 0;
        brk = 0;
        start = pos;
        x = rect->left + 1;
        while (width > w && done == 0) {
            if (styl && *styl > styleIdx + 1 && styles[styleIdx + 1].pos <= (int32_t)pos) {
                styleIdx++;
                n = pos - start;
                if (n > 0) {
                    if (n > 110)
                        Punt("len = %d", n);
                    _fstrncpy(buf, text + start, n);
                    buf[n] = 0;
                    WinPrintf("%d(%d)(%d): [%s]\n", pos, n, styles[styleIdx].face, buf);
                    f_24AB_038D(x, y, buf);
                    if (record && styles[styleIdx - 1].face == 0x100) {
                        start = 0;
                        while (buf[start] == ' ')
                            _fstrcpy(buf + start, buf + start + 1);
                        for (; buf[start]; start++)
                            if (sim_msc_ctype_is_lower_ascii((uint8_t)buf[start]))
                                buf[start] -= 0x20;
                        for (start = 0; fd_4EE5_0500[start].id != 0; start++)
                            if (_fstrcmp(buf, fd_4EE5_0500[start].name) == 0)
                                break;
                        if (fd_4EE5_0500[start].id != 0) {
                            fd_4EE5_0000[g_8C24].r.left = x;
                            fd_4EE5_0000[g_8C24].r.right = rect->left + w;
                            fd_4EE5_0000[g_8C24].r.top = y;
                            fd_4EE5_0000[g_8C24].r.bottom = y + lineH;
                            fd_4EE5_0000[g_8C24].id = fd_4EE5_0500[start].id;
                            g_8C24++;
                        } else {
                            WinPrintf("\nERROR: Cannot file text rez(%s)\n", buf);
                        }
                    }
                }
                x = rect->left + w + 1;
                if (styles[styleIdx].face == 0x100)
                    f_24AB_02AD(font2);
                else
                    f_24AB_02AD(font1);
                start = pos;
            }
            w += f_24AB_0367(text[pos]);
            if (w < width) {
                switch (text[pos]) {
                case 0:
                case '\n':
                case '\r':
                    done = 1;
                case ' ':
                case '(':
                case '[':
                case '{':
                    brk = pos;
                    break;
                case '!':
                case ')':
                case ',':
                case '-':
                case '.':
                case '?':
                case ']':
                case '}':
                    brk = pos + 1;
                    break;
                }
            }
            pos++;
        }
        end = pos;
        if (brk != 0) {
            end = brk;
            if (end < start)
                start = end;
        }
        if (line >= firstLine && (n = end - start) > 0) {
            _fstrncpy(buf, text + start, n);
            buf[n] = 0;
            f_24AB_038D(x, y, buf);
        }
        while (text[end] == ' ')
            end++;
        if (text[end] == '\n' || text[end] == '\r')
            end++;
        pos = end;
        y += lineH;
    }
}
/* SCAFFOLD END */

extern char  *  f_1A53_00F0(int16_t object, int16_t kind, int16_t type);
extern char  *  f_171C_1B84(char  *handle);

int16_t  win_GetStyleTextHeight(char  *text, int16_t  *styl, int16_t width, int16_t font1, int16_t font2)
{
    int16_t w;
    int16_t pos;
    int16_t brk;
    int16_t done;
    int16_t lineH;
    int16_t lines;
    int16_t styleIdx;
    int16_t len;
    struct StyleRun  *styles;

    styleIdx = 0;
    pos = 0;
    lines = 0;
    styles = styl ? (struct StyleRun  *)(styl + 1) : 0;
    len = _fstrlen(text);
    f_24AB_02AD(font1);
    lineH = f_24AB_030B();
    f_24AB_02AD(font2);
    if (f_24AB_030B() > lineH)
        lineH = f_24AB_030B();
    if (styl) {
        if (styles->face == 0x100)
            f_24AB_02AD(font2);
        else
            f_24AB_02AD(font1);
    } else
        f_24AB_02AD(font1);
    while (pos < len) {
        w = 0;
        done = 0;
        brk = 0;
        while (w < width && done == 0) {
            if (styl && styleIdx + 1 < *styl && styles[styleIdx + 1].pos <= (int32_t)pos) {
                styleIdx++;
                if (styles[styleIdx].face == 0x100)
                    f_24AB_02AD(font2);
                else
                    f_24AB_02AD(font1);
            }
            w += f_24AB_0367(text[pos]);
            if (w < width) {
                switch (text[pos]) {
                case 0:
                case '\n':
                case '\r':
                    done = 1;
                case ' ':
                case '(':
                case '[':
                case '{':
                    brk = pos;
                    break;
                case '!':
                case ')':
                case ',':
                case '-':
                case '.':
                case '?':
                case ']':
                case '}':
                    brk = pos + 1;
                    break;
                }
            }
            pos++;
        }
        if (brk != 0)
            pos = brk;
        while (text[pos] == ' ')
            pos++;
        if (text[pos] == '\n' || text[pos] == '\r')
            pos++;
        lines++;
    }
    return lines * lineH;
}


extern void  win_SetObjFormatStr(int16_t obj, char  *text);
extern void  f_171C_1BBA(char  *handle);
extern void  db_PurgeObject(int16_t object, int16_t kind);
extern void  win_DrawTitle(int16_t obj);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  clip_SetWin(int16_t win);
extern void  clip_SubInclude(struct Rect  *rect);
extern int32_t  f_171C_1C1C(char  *handle);
extern void  win_SetColorFromObjNum(int16_t obj);

extern int16_t  win_DrawBitMap(int16_t x, int16_t y, int16_t id);


extern void  f_277D_000B(char  *text);

struct PicRec {
    int16_t id;
    int16_t top;
    int16_t left;
    int16_t bottom;
    int16_t right;
    int16_t nLinks;
};

struct TextRec {
    struct Rect r;
    int16_t nFrames;
};

/* SCAFFOLD BEGIN: DisplayCard best draft: instruction sequence identical (558 insns), 89 bytes
 * differ, all in stack slot assignment (frame 7A vs 76) plus the operand order of base + off
 * and one loop compare.  Target packs the underscore-loop iterator into size's slot (-6/-8) and
 * the memmove iterator into h2's slot (-1E/-20); MSC 6 packs locals with disjoint live ranges
 * (separate q/q2 variables reproduce the size packing but not the h2 one).
 */
void  DisplayCard(int16_t card)
{
    int32_t off;
    char  *h1;
    char  *h2;
    char  *p;
    char  *q;
    int32_t size;
    char  *base;
    struct Rect r;
    char hdr[4];
    struct PicRec pic;
    struct TextRec tr;
    int16_t i;
    int16_t t;
    int16_t rez;
    char  *hText;
    char  *hStyl;
    int16_t  *styl;
    char  *text;
    int16_t tlen;
    struct StyleRun  *styles;
    char  *nul;
    int16_t k;

    off = 4;
    g_2E26 = card;
    WinPrintf("DisplayCard(cardRez)(%d)\n", card);
    h1 = f_1A53_00F0(card, 0x11, 1);
    if (h1 == 0) {
        WinPrintf("Card Resource not found.\n");
        return;
    }
    h2 = f_1A53_00F0(card, 0x13, 1);
    if (h2 != 0) {
        p = f_171C_1B84(h2);
        for (q = p; *q; q++)
            if (*q == '_')
                *q = ' ';
        win_SetObjFormatStr(0x501, p);
        f_171C_1BBA(h2);
        db_PurgeObject(card, 0x13);
        win_DrawTitle(0x501);
    }
    win_GetObjRect(0x502, &r);
    clip_SetWin(0x500);
    clip_SubInclude(&r);
    size = f_171C_1C1C(h1);
    base = f_171C_1B84(h1);
    win_SetColorFromObjNum(0x502);
    g_8C22 = 0;
    while (off < size) {
        _fmemcpy(hdr, off + base, 4);
        off += 4;
        switch (hdr[0]) {
        case 'P':
            _fmemcpy(&pic, off + base, 12);
            off += 12;
            FlipWords((uint8_t  *)&pic, 12);
            win_DrawBitMap(pic.left + r.left, pic.top + r.top, pic.id);
            win_SetColorFromObjNum(0x502);
            for (i = 0; i < pic.nLinks; i++) {
                _fmemcpy(&fd_4EE5_0280[g_8C22], off + base, 10);
                off += 10;
                FlipWords((uint8_t  *)&fd_4EE5_0280[g_8C22], 10);
                t = fd_4EE5_0280[g_8C22].r.left;
                fd_4EE5_0280[g_8C22].r.left = fd_4EE5_0280[g_8C22].r.top;
                fd_4EE5_0280[g_8C22].r.top = t;
                t = fd_4EE5_0280[g_8C22].r.right;
                fd_4EE5_0280[g_8C22].r.right = fd_4EE5_0280[g_8C22].r.bottom;
                fd_4EE5_0280[g_8C22].r.bottom = t;
                g_8C22++;
            }
            break;
        case 'T':
            _fmemcpy(&tr, off + base, 10);
            off += 10;
            FlipWords((uint8_t  *)&tr, 10);
            WinPrintf("Text: %#x %#x %#x %#x NumOfFrames: %#x\n",
                      tr.r.left, tr.r.top, tr.r.right, tr.r.bottom, tr.nFrames);
            for (k = 0; k < tr.nFrames; k++) {
                _fmemcpy(&rez, off + base, 2);
                off += 2;
                FlipWords((uint8_t  *)&rez, 2);
                t = tr.r.left;
                tr.r.left = tr.r.top;
                tr.r.top = t;
                t = tr.r.right;
                tr.r.right = tr.r.bottom;
                tr.r.bottom = t;
                hText = f_1A53_00F0(rez, 10, 1);
                if (hText == 0)
                    continue;
                hStyl = f_1A53_00F0(rez, 0x15, 1);
                styl = 0;
                text = f_171C_1B84(hText);
                tlen = f_171C_1C1C(hText);
                if (hStyl != 0) {
                    styl = (int16_t  *)f_171C_1B84(hStyl);
                    FlipWords((uint8_t  *)styl, f_171C_1C1C(hStyl));
                    styles = styl ? (struct StyleRun  *)(styl + 1) : 0;
                    for (k = 0; k < *styl; k++)
                        XFlipLong((uint16_t  *)&styles[k]);
                } else {
                    styles = 0;
                }
                while ((nul = _fmemchr(text, 0, tlen - 4)) != 0) {
                    off = nul - text;
                    q = nul;
                    while (*q < ' ' && off < tlen - 4) {
                        q++;
                        off++;
                    }
                    _fmemmove(nul, q, tlen - (int16_t)off);
                    if (styl) {
                        for (i = 0; i < *styl; i++)
                            if (styles[i].pos >= off)
                                styles[i].pos -= q - nul;
                    }
                    tlen += nul - q;
                }
                WinPrintf("\nINFO TEXT REC: %d\n", rez);
                f_277D_000B(text);
                tr.r.left += r.left;
                tr.r.top += r.top;
                tr.r.right += r.left;
                tr.r.bottom += r.top;
                win_PrintStyleTextInRect(text, styl, &tr.r, 0, 2, 5, 1);
                f_24AB_02AD(0);
                f_171C_1BBA(hText);
                db_PurgeObject(rez, 10);
                if (hStyl != 0) {
                    f_171C_1BBA(hStyl);
                    db_PurgeObject(rez, 0x15);
                }
            }
            break;
        default:
            WinPrintf("Unknown Resource.\n");
            off = size;
            break;
        }
    }
    f_171C_1BBA(h1);
    db_PurgeObject(card, 0x11);
}

/* SCAFFOLD END */

struct Point {
    int16_t x;
    int16_t y;
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    struct Point where;
    int16_t code;
    int16_t xE;
};

extern int16_t  win_IsWinOpen(int16_t win);
extern void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) ;
extern int16_t  win_GetEvent(struct Event  *ev);
void  ProcInfoEvent(struct Event  *ev);

void  OpenInfoWindow(void)
{
    struct Event ev;

    if (win_IsWinOpen(0x500) == 0) {
        g_2E26 = 0x80;
        g_2E04[0] = 0x80;
        g_2E24 = 0;
    }
    win_Open(0x500, 0, 0, 0, 0, 0);
    if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140) {
        while (win_IsWinOpen(0x500)) {
            if (win_GetEvent(&ev))
                ProcInfoEvent(&ev);
        }
    }
}

extern void  clip_Push(void);
extern char  *  GSaveRect(struct Rect  *r);

extern void  f_1CE2_0013(int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t width);
extern int16_t  StillDown(void);
extern void  win_Events(void);
extern void  f_1CE2_056C(struct Rect  *r, char  *buf);
extern void  clip_Pop(void);

void  PopUpInfoWindow(int16_t x, int16_t top, int16_t bottom, int16_t rez)
{
    int16_t k;
    int16_t halfW;
    int16_t winH;
    int16_t  *styl;
    struct StyleRun  *styles;
    char  *bits;
    struct Rect wr;
    struct Rect frame;
    struct Rect box;
    char  *hText;
    char  *hStyl;
    char  *text;

    top -= 4;
    bottom += 4;
    win_GetObjRect(0x502, &wr);
    clip_Push();
    clip_SubInclude(&wr);
    halfW = (wr.right - wr.left) / 2;
    winH = wr.bottom - wr.top;
    box.left = wr.left - halfW / 2 + x;
    box.right = halfW / 2 + wr.left + x;
    if (box.left < wr.left + 4) {
        box.left = wr.left + 4;
        box.right = box.left + halfW;
    }
    if (box.right > wr.right - 4) {
        box.right = wr.right - 4;
        box.left = box.right - halfW;
    }
    hText = f_1A53_00F0(rez, 10, 1);
    if (hText != 0) {
        hStyl = f_1A53_00F0(rez, 0x15, 1);
        styl = 0;
        text = f_171C_1B84(hText);
        if (hStyl != 0) {
            styl = (int16_t  *)f_171C_1B84(hStyl);
            FlipWords((uint8_t  *)styl, f_171C_1C1C(hStyl));
            styles = styl ? (struct StyleRun  *)(styl + 1) : 0;
            for (k = 0; k < *styl; k++)
                XFlipLong((uint16_t  *)&styles[k]);
        }
        k = win_GetStyleTextHeight(text, styl, halfW, 2, 5) + 5;
        if (k + bottom > winH - 10) {
            box.top = wr.top - k + top;
            box.bottom = wr.top + top;
        } else {
            box.top = wr.top + bottom;
            box.bottom = box.top + k;
        }
        frame = box;
        frame.left -= 4;
        frame.right += 4;
        frame.bottom += 4;
        frame.top -= 4;
        if (frame.top < wr.top) {
            frame.top = wr.top;
            frame.bottom = wr.top + k + 8;
        } else if (frame.bottom > wr.bottom) {
            frame.bottom = wr.bottom;
            frame.top = wr.bottom - k - 8;
        }
        bits = GSaveRect(&frame);
        win_SetColorFromObjNum(0x502);
        if (((uint8_t)g_5A97) & 1)
            SIM_GRAPHICS_SOURCE_g_3DE0 = 0x80;
        f_1CE2_0013(frame.left, frame.top, frame.right, frame.bottom, 1);
        win_PrintStyleTextInRect(text, styl, &box, 0, 2, 5, 0);
        f_171C_1BBA(hText);
        db_PurgeObject(rez, 10);
        if (hStyl != 0) {
            f_171C_1BBA(hStyl);
            db_PurgeObject(rez, 0x15);
        }
    }
    while (StillDown())
        win_Events();
    f_1CE2_056C(&frame, bits);
    clip_Pop();
}

extern int16_t  f_1FD2_04E5(struct Point  *pt, struct Rect  *rect);
extern void  win_DrawWindow(int16_t win);

void  ProcInfoEvent(struct Event  *ev)
{
    struct Rect wr;
    struct Point pt;
    int16_t i;
    int16_t found;
    int16_t prev;

    win_GetObjRect(0x502, &wr);
    if (ev->code != 0x502)
        return;
    found = i = 0;
    pt.x = ev->where.x - wr.left;
    pt.y = ev->where.y - wr.top;
    for (; i < g_8C22 && found == 0; i++) {
        if (f_1FD2_04E5(&pt, &fd_4EE5_0280[i].r)) {
            if (fd_4EE5_0280[i].id == 1) {
                prev = g_2E04[(g_2E24 - 1) & 0xf];
                if (prev) {
                    g_2E26 = prev;
                    win_DrawWindow(0x500);
                    g_2E24--;
                }
            } else if (fd_4EE5_0280[i].id > 0) {
                g_2E04[++g_2E24 & 0xf] = fd_4EE5_0280[i].id;
                g_2E26 = fd_4EE5_0280[i].id;
                g_2E04[(g_2E24 + 1) & 0xf] = 0;
                win_DrawWindow(0x500);
            } else {
                PopUpInfoWindow((fd_4EE5_0280[i].r.right - fd_4EE5_0280[i].r.left) / 2 + fd_4EE5_0280[i].r.left,
                                fd_4EE5_0280[i].r.top, fd_4EE5_0280[i].r.bottom, -fd_4EE5_0280[i].id);
            }
            found = 1;
        }
    }
    pt = ev->where;
    for (i = 0; i < g_8C24 && found == 0; i++) {
        if (f_1FD2_04E5(&pt, &fd_4EE5_0000[i].r)) {
            PopUpInfoWindow((fd_4EE5_0000[i].r.right - fd_4EE5_0000[i].r.left) / 2 + fd_4EE5_0000[i].r.left - wr.left,
                            fd_4EE5_0000[i].r.top - wr.top, fd_4EE5_0000[i].r.bottom - wr.top, fd_4EE5_0000[i].id);
            found = 1;
        }
    }
}

#pragma pack(pop)
