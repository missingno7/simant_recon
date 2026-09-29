/* Root module 20E8: window loading and window-stack operations. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

void far f_20E8_0000(void);

void (far *g_62E0)(int win) = f_20E8_0000;
void (far *g_62E4)(void) = f_20E8_0000;
void (far *g_62E8)(void) = f_20E8_0000;
void (far *g_62EC)(void) = f_20E8_0000;
void (far *g_62F0)(void) = f_20E8_0000;
void (far *g_62F4)(int win) = f_20E8_0000;
int g_62F8 = 0;
int g_62FA = -1;
int g_62FC = 0;
int g_62FE = 0;
int g_6300 = 0;

void far f_20E8_0000(void)
{
}

/* SCAFFOLD BEGIN: f_20E8_0001 (win_LoadWindow) best draft.
   Residue: case 4 of the object loop computes the _fmemset pointer with
   mov ax,bx; mov dx,es; add ax,2Ah - the original reuses DX (obj segment
   from the objs[i] load): mov ax,bx; add ax,2Ah; push dx. 322 vs 320 bytes. */
extern char far * far * far f_1A53_00F0(int object, int kind, int type);
extern void far Punt(char far *format, ...);
extern char far * far * near g_9230[];
extern void _fastcall f_23AE_0377(int win);
extern void _fastcall f_2505_0048(int win);
extern struct Rect far fd_50F6_4892[];
extern void _fastcall f_23AE_01DB(int win);

void far f_20E8_0001(int win)
{
    char far * far *h;
    char far *obj;
    int i;
    char far *w;

    h = f_1A53_00F0((char)(win >> 8), 0, 1);
    if (h == 0)
        Punt("CANNOT LOAD WINDOW %03x", win);
    g_9230[(char)(win >> 8)] = h;
    w = *h;
    f_23AE_0377(win);
    f_2505_0048(win);
    obj = ((char far * far *)(w + 0x2c))[0];
    if (fd_50F6_4892[(char)(win >> 8)].left != (int)0x8000)
        *(struct Rect far *)(obj + 8) = fd_50F6_4892[(char)(win >> 8)];
    else
        fd_50F6_4892[(char)(win >> 8)] = *(struct Rect far *)(obj + 8);
    for (i = 0; i < *(int far *)(w + 0xc); i++) {
        obj = ((char far * far *)(w + 0x2c))[i];
        if (i == 0)
            *(struct Rect far *)w = *(struct Rect far *)obj;
        switch (obj[0x21]) {
        case 4:
            _fmemset(obj + 0x2a, 0, 14);
            break;
        case 16:
        case 17:
        case 18:
            *(char far * far *)(obj + 0x2a) = 0;
            break;
        }
    }
    f_23AE_01DB(win);
}

/* SCAFFOLD END */

struct Rect g_635C = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };

extern void far font_InitFonts(void);
extern void far f_23AE_0022(void);
extern void (far * far fd_50F6_47DE[])(int phase);
extern char near g_5A97;
extern char far * far * far db_LoadObject(int object, int kind);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern void far db_PurgeObject(int object, int kind);
struct Pt {
    int x;
    int y;
};
extern void far f_208F_0419(struct Pt far *size, int id);
extern struct Pt far fd_50F6_47DA;
extern int far fd_50F6_47D8;
extern int far fd_50F6_47D6;
extern int far fd_50F6_47D4;
extern char far fd_50F6_46E2[][6];
extern void far f_1A53_034F(int object, int kind);

int far f_20E8_0141(void)
{
    char purge[0x28];
    int i;
    char far * far *h;
    int far *p;
    char far *q;

    font_InitFonts();
    f_23AE_0022();
    _fmemset(fd_50F6_47DE, 0, 0xb4);
    for (i = 0; i < 45; i++)
        fd_50F6_4892[i] = g_635C;
    h = db_LoadObject(g_5A97, 9);
    if (h) {
        _fmemcpy(fd_50F6_4892, f_171C_1B84(h), 0x140);
        f_171C_1BBA(h);
        db_PurgeObject(g_5A97, 9);
    }
    f_208F_0419(&fd_50F6_47DA, 0x6f);
    h = db_LoadObject(0x80, 0);
    if (h == 0) {
        Punt("Cannot load resource\nplease try another");
    } else {
        p = (int far *)*h;
        fd_50F6_47D8 = p[0];
        fd_50F6_47D6 = p[1];
        fd_50F6_47D4 = p[2];
        db_PurgeObject(0x80, 0);
    }
    h = db_LoadObject(0x81, 0);
    _fmemcpy(fd_50F6_46E2, *h, fd_50F6_47D6 * 6);
    db_PurgeObject(0x81, 0);
    h = db_LoadObject(0x83, 0);
    q = *h;
    if (h == 0)
        Punt("Could not load purge list");
    _fmemcpy(purge, q, 0x28);
    db_PurgeObject(0x83, 0);
    for (i = 0; i < fd_50F6_47D8; i++) {
        if (purge[i] == 0) {
            f_20E8_0001(i << 8);
            f_1A53_034F(i, 0);
        }
    }
    return 1;
}
