/* Root module 075B: startup resources (Win16 unit initStuff / PrepareStrings /
 * LoadStringAnt). */

typedef char far * far *Handle;
typedef char far * far *StrList;

void far PrepareStrings(void);
extern Handle far db_LoadObject(int object, int kind);
extern void far WinPrintf(char far *format, ...);
extern void far o15_384C_0152(char far *message, int code);
extern void far FlipHandleWords(Handle h);
extern char far * far fd_50F6_0B22;
void far f_075B_00A6(void);
extern void far f_00F8_02E7(void);
extern void far OverlayOutsideTiles(void);
extern int far f_00F8_02EF(void);
extern void far InitSimVars(void);
extern void far SeedSRand(void);
extern void far SeedRRand(void);
extern void far SetSimCursor(int cursor);

void far initStuff(void)
{
    Handle handle;
    int resourceError;

    PrepareStrings();
    handle = db_LoadObject(1000, 9);
    if (handle == 0) {
        WinPrintf("Cannot GetResource (HEX, %d), ResErr %d\n", 1000, resourceError);
        o15_384C_0152("MemDeath", 0);
    }
    FlipHandleWords(handle);
    fd_50F6_0B22 = *handle;
    f_075B_00A6();
    f_00F8_02E7();
    OverlayOutsideTiles();
    if (f_00F8_02EF() == 0) {
        InitSimVars();
        SeedSRand();
        SeedRRand();
    }
    SetSimCursor(0);
}

void far f_075B_00A6(void)
{
}

StrList far LoadStringAnt(int object);
extern StrList far MwinTitle;
extern StrList far fd_50F6_0324;
extern StrList far WindPromptStrs;
extern StrList far AdviceStrs;
extern StrList far HistGraphStrs;
extern StrList far fd_50F6_106E;
extern StrList far CasteStr;
extern StrList far fd_50F6_1086;
extern StrList far fd_50F6_1096;
extern StrList far BoyMsgs;
extern StrList far fd_50F6_10B4;
extern StrList far BFightMsgs;
extern StrList far RFightMsgs;
extern StrList far EggMsgs;
extern StrList far QueenMsgs;
extern StrList far RestMsgs;
extern StrList far fd_50F6_0328;
extern StrList far fd_50F6_0368;

void far PrepareStrings(void)
{
    MwinTitle = LoadStringAnt(1000);
    fd_50F6_0324 = LoadStringAnt(1001);
    WindPromptStrs = LoadStringAnt(1010);
    AdviceStrs = LoadStringAnt(1020);
    HistGraphStrs = LoadStringAnt(1050);
    fd_50F6_106E = LoadStringAnt(1100);
    CasteStr = LoadStringAnt(1101);
    fd_50F6_1086 = LoadStringAnt(1102);
    fd_50F6_1096 = LoadStringAnt(1103);
    BoyMsgs = LoadStringAnt(1200);
    fd_50F6_10B4 = LoadStringAnt(1210);
    BFightMsgs = LoadStringAnt(1220);
    RFightMsgs = LoadStringAnt(1230);
    EggMsgs = LoadStringAnt(1240);
    QueenMsgs = LoadStringAnt(1250);
    RestMsgs = LoadStringAnt(1260);
    fd_50F6_0328 = LoadStringAnt(1900);
    fd_50F6_0368 = LoadStringAnt(1800);
}

extern Handle far mem_Alloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern void far * far _fmemmove(void far *dst, void far *src, unsigned n);

StrList far LoadStringAnt(int object)
{
    Handle h;
    unsigned char far *p;
    int count;
    StrList list;
    int i;
    int len;

    h = db_LoadObject(object, 4);
    if (h == 0) {
        WinPrintf("\n\aWarning: Can't load strings: %d", object);
        return 0;
    }
    p = (unsigned char far *)*h + 1;
    count = *p++;
    list = (StrList)mem_Lock(mem_Alloc((long)(count + 1) << 2, 0, "strptrs"));
    for (i = 0; i < count; i++) {
        list[i] = p;
        len = *p;
        _fmemmove(p, p + 1, len);
        p[len] = 0;
        p += len + 1;
    }
    list[i] = 0;
    return list;
}

void far f_075B_0334(void)
{
}
