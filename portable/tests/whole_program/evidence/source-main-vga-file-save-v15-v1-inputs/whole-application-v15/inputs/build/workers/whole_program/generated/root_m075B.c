#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module 075B: startup resources (Win16 unit initStuff / PrepareStrings /
 * LoadStringAnt). */

typedef char  *  *Handle;
typedef char  *  *StrList;

void  PrepareStrings(void);
extern Handle  db_LoadObject(int16_t object, int16_t kind);
extern void  WinPrintf(char  *format, ...);
extern void  o15_384C_0152(char  *message, int16_t code);
extern void  f_0244_0022(Handle h);
extern char  *  fd_50F6_0B22;
void  f_075B_00A6(void);
extern void  f_00F8_02E7(void);
extern void  f_0244_00A7(void);
extern int16_t  f_00F8_02EF(void);
extern void  InitSimVars(void);
extern void  SeedSRand(void);
extern void  SeedRRand(void);
extern void  SetSimCursor(int16_t cursor);

void  initStuff(void)
{
    Handle handle;
    int16_t resourceError;

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

void  f_075B_00A6(void)
{
}

StrList  LoadStringAnt(int16_t object);
extern StrList  fd_50F6_046C;
extern StrList  fd_50F6_0324;
extern StrList  fd_50F6_034C;
extern StrList  AdviceStrs;
extern StrList  fd_50F6_02BA;
extern StrList  fd_50F6_106E;
extern StrList  fd_50F6_1078;
extern StrList  fd_50F6_1086;
extern StrList  fd_50F6_1096;
extern StrList  fd_50F6_10A8;
extern StrList  fd_50F6_10B4;
extern StrList  fd_50F6_020A;
extern StrList  fd_50F6_0218;
extern StrList  fd_50F6_021C;
extern StrList  fd_50F6_0234;
extern StrList  fd_50F6_023A;
extern StrList  fd_50F6_0328;
extern StrList  fd_50F6_0368;

void  PrepareStrings(void)
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

extern Handle  f_171C_1A9E(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(Handle h);


StrList  LoadStringAnt(int16_t object)
{
    Handle h;
    uint8_t  *p;
    int16_t count;
    StrList list;
    int16_t i;
    int16_t len;

    h = db_LoadObject(object, 4);
    if (h == 0) {
        WinPrintf("\n\aWarning: Can't load strings: %d", object);
        return 0;
    }
    p = (uint8_t  *)*h + 1;
    count = *p++;
    list = (StrList)f_171C_1B84(f_171C_1A9E((int32_t)(count + 1) * (int32_t)sizeof(*list), 0, "strptrs"));
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

void  f_075B_0334(void)
{
}

#pragma pack(pop)
