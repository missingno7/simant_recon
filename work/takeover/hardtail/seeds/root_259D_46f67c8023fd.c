/* Root module 259D: DOS picture drawing for window objects (partial). */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pic {
    int type;
    char mode;
    char pad[5];
    int width;
    int height;
};

extern char far * far db_LoadObject(int object, int kind);
extern void far db_ReleaseObject(int object, int kind);
extern void far GPutPacked(int x, int y, char far *pic);
extern void far f_1B4E_003B(int x, int y, char far *image);
extern void far f_1B4E_005E(int x, int y, char far *image);
extern char far * far malloc(unsigned int size);
extern void far free(char far *block);
extern int far WinPrintf(char far *format, ...);
extern void far o03_3258_040D(char far *image, char far *buffer, int shift, int flag);
extern void far o01_32B5_000F(char far *image, char far *buffer, int shift, int flag);
extern void far o00_35A6_0007(char far *image, char far *buffer, int shift, int flag);
extern void far f_1CE2_046D(struct Rect far *rect, int color);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_UnlockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern int far f_24AB_030B(void);
extern int far f_24AB_0367(int c);
extern void far f_24AB_038D(int x, int y, char far *text);
extern char far * far _fstrncpy(char far *dst, char far *src, unsigned int n);

extern int near g_3DE0;
extern char near g_3DE4;
extern char near g_5A97;
extern unsigned int (far * near g_9140)(int x0, int y0, int x1, int y1);
extern void (far * near g_9148)(int x0, int y0, int x1, int y1, char far *buffer);

int _fastcall win_DrawBitMap(int x, int y, int id);

int _fastcall win_DrawBitMap(int x, int y, int id)
{
    char far *h;
    struct Pic far *pic;
    int x1;
    int y1;
    unsigned int n;

    h = db_LoadObject(id, 2);
    if (h != 0) {
        pic = *(struct Pic far * far *)h;
        if (pic->type == -1) {
            GPutPacked(x, y, (char far *)pic);
            db_ReleaseObject(id, 2);
            return 1;
        }
        if ((*(struct Pic far * far *)h)->type == (int)0x8000) {
            GPutPacked(x, y, *(char far * far *)h);
            db_ReleaseObject(id, 2);
            return 1;
        }
        if (pic->type == 0) {
            if (pic->mode == 1)
                f_1B4E_005E(x, y, (char far *)pic + 8);
            else
                f_1B4E_003B(x, y, (char far *)pic + 8);
            db_ReleaseObject(id, 2);
            return 1;
        }
        if (pic->type == 3) {
            if (g_5A97 == 2) {
                x1 = ((x & ~1) + pic->width + 3) & ~1;
                y1 = pic->height + y;
                h = malloc((*g_9140)(x & ~1, y, x1, y1));
                (*g_9148)(x & ~1, y, x1, y1, h);
                o03_3258_040D((char far *)pic + 8, h, x & 1, 0);
                f_1B4E_003B(x & ~1, y, h);
                free(h);
            } else {
                x1 = ((x & ~7) + pic->width + 15) & ~7;
                y1 = pic->height + y;
                n = (*g_9140)(x & ~7, y, x1, y1);
                WinPrintf("\nGGetPic - trans @ %d, %d (%d, %d), bytes=%u", x & ~7, y, x1, y1, n);
                h = malloc(n + 1);
                h[n] = 0xf3;
                (*g_9148)(x & ~7, y, x1, y1, h);
                WinPrintf("\nGPutPic size AA %d, %d, tag=%x", *(int far *)h, *(int far *)h + 2, (unsigned char)h[n]);
                if (g_5A97 & 1)
                    o01_32B5_000F((char far *)pic + 8, h, x & 7, 0);
                else
                    o00_35A6_0007((char far *)pic + 8, h, x & 7, 0);
                WinPrintf("\nGPutPic size %d, %d, tag=%x", *(int far *)h, *(int far *)h + 2, (unsigned char)h[n]);
                f_1B4E_003B(x & ~7, y, h);
                free(h);
            }
        }
        db_ReleaseObject(id, 2);
        return 1;
    }
    return 0;
}


void _fastcall win_DrawBitMapAtObj(int id, struct Rect far *rect)
{
    if (!win_DrawBitMap(rect->left, rect->top, id))
        f_1CE2_046D(rect, g_3DE4 | g_3DE0);
}

void _fastcall win_DrawBitMapAtObjNum(int obj, int id)
{
    struct Rect far *rect;

    win_LockWin(obj);
    rect = (struct Rect far *)win_ObjAddr(obj);
    if (!win_DrawBitMap(rect->left, rect->top, id))
        f_1CE2_046D(rect, g_3DE4 | g_3DE0);
    win_UnlockWin(obj);
}

/* `start` (always 0, read only in `brk == start`) and the order of the chained zero
   assignment reproduce the original's two dead stores: MSC keeps the store of a local whose
   only read is later replaced by the propagated constant, and the home of the enregistered i
   receives its own store in chain position (worker resG).  The name is a hypothesis. */
void _fastcall win_PrintTextInRect(int first, char far *text, struct Rect far *rect)
{
    int c;
    int start;
    int pixw;
    int brk;
    int line;
    int done;
    char far *p;
    int y;
    int w;
    int lh;
    int nlines;
    int len;
    char buf[150];
    int i;

    w = rect->right - rect->left;
    y = rect->top;
    lh = f_24AB_030B();
    nlines = (rect->bottom - rect->top) / lh;
    line = 0;
    while (*text) {
        if (first + nlines <= line)
            break;
        p = text;
        done = start = i = brk = pixw = 0;
        while (pixw < w && !done) {
            c = *p++;
            pixw += f_24AB_0367(c);
            if (pixw < w) {
                switch (c) {
                case 0:
                case 10:
                case 13:
                    done = 1;
                case ' ':
                case '(':
                case '[':
                case '{':
                    brk = i - 1;
                    break;
                case '!':
                case ')':
                case ',':
                case '-':
                case '.':
                case '?':
                case ']':
                case '}':
                    brk = i;
                    break;
                }
            }
            i++;
        }
        if (brk == start)
            brk = i - 1;
        if (first <= line) {
            len = brk + 1;
            _fstrncpy(buf, text, len);
            buf[len] = 0;
            f_24AB_038D(rect->left, y, buf);
        }
        text += len;
        while (*text == ' ')
            text++;
        if (*text == 10 || *text == 13)
            text++;
        y += lh;
        line++;
    }
}
