/* Overlay section S23, code frame 39C7: info window and card display. */

int g_2E04[16] = { 0 };
int g_2E24 = 0;
int g_2E26 = 0x80;

void far XFlipLong(unsigned far *words)
{
    unsigned first = words[0];
    words[0] = words[1];
    words[1] = first;
}

void far FlipWords(unsigned char far *bytes, long length)
{
    long i;
    unsigned char saved;

    for (i = 0L; i < length; i += 2L) {
        saved = bytes[i];
        bytes[i] = bytes[i + 1L];
        bytes[i + 1L] = saved;
    }
}

void far DisplayCard(int card);

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct HotSpot {
    struct Rect r;
    int id;
};

struct TextRez {
    char name[32];
    int id;
};

struct StyleRun {
    long pos;
    int height;
    int ascent;
    int font;
    int face;
    int size;
    int color[3];
};

static struct HotSpot far fd_4EE5_0000[64];
static struct HotSpot far fd_4EE5_0280[64];
struct TextRez far fd_4EE5_0500[] = {
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

void far win_DrawInfoWindow(int flags)
{
    if (flags & 2)
        DisplayCard(g_2E26);
}

static int g_8C22;
static int g_8C24;

extern unsigned int far _fstrlen(char far *s);
extern void far f_24AB_02AD(int font);
extern int far f_24AB_030B(void);
extern void far Punt(char far *format, ...);
extern char far * far _fstrncpy(char far *, char far *, unsigned int);
extern int far WinPrintf(char far *format, ...);
extern void far f_24AB_038D(int x, int y, char far *text);
extern char far * far _fstrcpy(char far *dst, char far *src);
extern unsigned char near _ctype[];
extern int far _fstrcmp(char far *a, char far *b);
extern int far f_24AB_0367(int c);

void far win_PrintStyleTextInRect(char far *text, int far *styl, struct Rect far *rect,
                                  int firstLine, int font1, int font2, int record)
{
    char buf[120];
    int end;
    int n;
    int x;
    int start;
    int brk;
    int done;
    int w;
    int line;
    int maxLines;
    int lineH;
    int y;
    int width;
    int len;
    int pos;
    int styleIdx;
    struct StyleRun far *styles;

    styleIdx = 0;
    pos = 0;
    styles = styl ? (struct StyleRun far *)(styl + 1) : 0;
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
            if (styl && *styl > styleIdx + 1 && styles[styleIdx + 1].pos <= (long)pos) {
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
                            if ((_ctype + 1)[buf[start]] & 2)
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

extern char far * far f_1A53_00F0(int object, int kind, int type);
extern char far * far f_171C_1B84(char far *handle);

int far win_GetStyleTextHeight(char far *text, int far *styl, int width, int font1, int font2)
{
    int w;
    int pos;
    int brk;
    int done;
    int lineH;
    int lines;
    int styleIdx;
    int len;
    struct StyleRun far *styles;

    styleIdx = 0;
    pos = 0;
    lines = 0;
    styles = styl ? (struct StyleRun far *)(styl + 1) : 0;
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
            if (styl && styleIdx + 1 < *styl && styles[styleIdx + 1].pos <= (long)pos) {
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


extern void far f_22BF_059A(int obj, char far *text);
extern void far f_171C_1BBA(char far *handle);
extern void far db_PurgeObject(int object, int kind);
extern void _fastcall f_21FA_0AA7(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_SetWin(int win);
extern void far clip_SubInclude(struct Rect far *rect);
extern long far f_171C_1C1C(char far *handle);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned int n);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far * far _fmemchr(void far *buf, int c, unsigned int n);
extern void far * far _fmemmove(void far *dst, void far *src, unsigned int n);
extern void far f_277D_000B(char far *text);

struct PicRec {
    int id;
    int top;
    int left;
    int bottom;
    int right;
    int nLinks;
};

struct TextRec {
    struct Rect r;
    int nFrames;
};

void far DisplayCard(int card)
{
    long off;
    char far *h1;
    char far *h2;
    char far *p;
    char far *q;
    long size;
    char far *base;
    struct Rect r;
    char hdr[4];
    struct PicRec pic;
    struct TextRec tr;
    int i;
    int t;
    int rez;
    char far *hText;
    char far *hStyl;
    int far *styl;
    char far *text;
    int tlen;
    struct StyleRun far *styles;
    char far *nul;
    int k;

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
        f_22BF_059A(0x501, p);
        f_171C_1BBA(h2);
        db_PurgeObject(card, 0x13);
        f_21FA_0AA7(0x501);
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
            FlipWords((unsigned char far *)&pic, 12);
            win_DrawBitMap(pic.left + r.left + 1, pic.top + r.top, pic.id);
            win_SetColorFromObjNum(0x502);
            for (i = 0; i < pic.nLinks; i++) {
                _fmemcpy(&fd_4EE5_0280[g_8C22], off + base, 10);
                off += 10;
                FlipWords((unsigned char far *)&fd_4EE5_0280[g_8C22], 10);
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
            FlipWords((unsigned char far *)&tr, 10);
            WinPrintf("Text: %#x %#x %#x %#x NumOfFrames: %#x\n",
                      tr.r.left, tr.r.top, tr.r.right, tr.r.bottom, tr.nFrames);
            for (k = 0; k < tr.nFrames; k++) {
                _fmemcpy(&rez, off + base, 2);
                off += 2;
                FlipWords((unsigned char far *)&rez, 2);
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
                    styl = (int far *)f_171C_1B84(hStyl);
                    FlipWords((unsigned char far *)styl, f_171C_1C1C(hStyl));
                    styles = styl ? (struct StyleRun far *)(styl + 1) : 0;
                    for (k = 0; k < *styl; k++)
                        XFlipLong((unsigned far *)&styles[k]);
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
                    _fmemmove(nul, q, tlen - (int)off);
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


struct Point {
    int x;
    int y;
};

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    struct Point where;
    int code;
    int xE;
};

extern int _fastcall f_22BF_09B0(int win);
extern void far f_20E8_04B6(int win);
extern int near g_3DB2;
extern int _fastcall f_218D_03F1(struct Event far *ev);
void far ProcInfoEvent(struct Event far *ev);

void far OpenInfoWindow(void)
{
    struct Event ev;

    if (f_22BF_09B0(0x500) == 0) {
        g_2E26 = 0x80;
        g_2E04[0] = 0x80;
        g_2E24 = 0;
    }
    f_20E8_04B6(0x500);
    if (g_3DB2 == 0x140) {
        while (f_22BF_09B0(0x500)) {
            if (f_218D_03F1(&ev))
                ProcInfoEvent(&ev);
        }
    }
}

extern void far clip_Push(void);
extern char far * far GSaveRect(struct Rect far *r);
extern unsigned char near g_5A97;
extern int near g_3DE0;
extern void far f_1CE2_0013(int left, int top, int right, int bottom, int width);
extern int far f_1FD2_0542(void);
extern void far f_218D_03E8(void);
extern void far f_1CE2_056C(struct Rect far *r, char far *buf);
extern void far clip_Pop(void);

void far PopUpInfoWindow(int x, int top, int bottom, int rez)
{
    int k;
    int halfW;
    int winH;
    int far *styl;
    struct StyleRun far *styles;
    char far *bits;
    struct Rect wr;
    struct Rect frame;
    struct Rect box;
    char far *hText;
    char far *hStyl;
    char far *text;

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
            styl = (int far *)f_171C_1B84(hStyl);
            FlipWords((unsigned char far *)styl, f_171C_1C1C(hStyl));
            styles = styl ? (struct StyleRun far *)(styl + 1) : 0;
            for (k = 0; k < *styl; k++)
                XFlipLong((unsigned far *)&styles[k]);
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
        if (g_5A97 & 1)
            g_3DE0 = 0x80;
        f_1CE2_0013(frame.left, frame.top, frame.right, frame.bottom, 1);
        win_PrintStyleTextInRect(text, styl, &box, 0, 2, 5, 0);
        f_171C_1BBA(hText);
        db_PurgeObject(rez, 10);
        if (hStyl != 0) {
            f_171C_1BBA(hStyl);
            db_PurgeObject(rez, 0x15);
        }
    }
    while (f_1FD2_0542())
        f_218D_03E8();
    f_1CE2_056C(&frame, bits);
    clip_Pop();
}

extern int far f_1FD2_04E5(struct Point far *pt, struct Rect far *rect);
extern void _fastcall f_21FA_08E2(int win);

void far ProcInfoEvent(struct Event far *ev)
{
    struct Rect wr;
    struct Point pt;
    int i;
    int found;
    int prev;

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
                    f_21FA_08E2(0x500);
                    g_2E24--;
                }
            } else if (fd_4EE5_0280[i].id > 0) {
                g_2E04[++g_2E24 & 0xf] = fd_4EE5_0280[i].id;
                g_2E26 = fd_4EE5_0280[i].id;
                g_2E04[(g_2E24 + 1) & 0xf] = 0;
                f_21FA_08E2(0x500);
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
