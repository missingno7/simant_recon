/* Root module 075B: startup resources (Win16 unit initStuff / PrepareStrings /
 * LoadStringAnt). */

typedef char far * far *Handle;
typedef char far * far *StrList;

void far PrepareStrings(void);
extern Handle far db_LoadObject(int object, int kind);
extern void far WinPrintf(char far *format, ...);
extern void far o15_384C_0152(char far *message, int code);
extern void far f_0244_0022(Handle h);
extern char far * far fd_50F6_0B22;
void far f_075B_00A6(void);
extern void far f_00F8_02E7(void);
extern void far f_0244_00A7(void);
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
    f_0244_0022(handle);
    fd_50F6_0B22 = *handle;
    f_075B_00A6();
    f_00F8_02E7();
    f_0244_00A7();
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
extern StrList far fd_50F6_046C;
extern StrList far fd_50F6_0324;
extern StrList far fd_50F6_034C;
extern StrList far AdviceStrs;
extern StrList far fd_50F6_02BA;
extern StrList far fd_50F6_106E;
extern StrList far fd_50F6_1078;
extern StrList far fd_50F6_1086;
extern StrList far fd_50F6_1096;
extern StrList far fd_50F6_10A8;
extern StrList far fd_50F6_10B4;
extern StrList far fd_50F6_020A;
extern StrList far fd_50F6_0218;
extern StrList far fd_50F6_021C;
extern StrList far fd_50F6_0234;
extern StrList far fd_50F6_023A;
extern StrList far fd_50F6_0328;
extern StrList far fd_50F6_0368;

void far PrepareStrings(void)
{
    fd_50F6_046C = LoadStringAnt(1000);
    fd_50F6_0324 = LoadStringAnt(1001);
    fd_50F6_034C = LoadStringAnt(1010);
    AdviceStrs = LoadStringAnt(1020);
    fd_50F6_02BA = LoadStringAnt(1050);
    fd_50F6_106E = LoadStringAnt(1100);
    fd_50F6_1078 = LoadStringAnt(1101);
    fd_50F6_1086 = LoadStringAnt(1102);
    fd_50F6_1096 = LoadStringAnt(1103);
    fd_50F6_10A8 = LoadStringAnt(1200);
    fd_50F6_10B4 = LoadStringAnt(1210);
    fd_50F6_020A = LoadStringAnt(1220);
    fd_50F6_0218 = LoadStringAnt(1230);
    fd_50F6_021C = LoadStringAnt(1240);
    fd_50F6_0234 = LoadStringAnt(1250);
    fd_50F6_023A = LoadStringAnt(1260);
    fd_50F6_0328 = LoadStringAnt(1900);
    fd_50F6_0368 = LoadStringAnt(1800);
}

extern Handle far f_171C_1A9E(long size, int flags, char far *name);
extern char far * far f_171C_1B84(Handle h);
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
    list = (StrList)f_171C_1B84(f_171C_1A9E((long)(count + 1) << 2, 0, "strptrs"));
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
