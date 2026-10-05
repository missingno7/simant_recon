/* Calls the actual compiled canonical root:m0093 and installed CRT/seed services.
 * TickCount and the physical seed reader are controlled platform inputs. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(_WIN32)
#include <windows.h>
#endif
#include "portable/whole_program/platform/seed_source.h"
#include "portable/whole_program/platform/crt_rng.h"

void SetSRandSeed(int16_t value);
uint32_t GetSRandSeed(void);
uint32_t GetRRandSeed(void);
void SeedRRand(void);
int16_t SRand1(uint16_t range);
int16_t SRand2(void);
int16_t SRand4(void);
int16_t SRand8(void);
int16_t SRand16(void);
int16_t SRand32(void);
int16_t SRand64(void);
int16_t SRand128(void);
int16_t SRand256(void);
int16_t SGIRand(int16_t range);
int16_t SGRand(int16_t range);
int16_t SGSRand(int16_t range);
int16_t RRand(int16_t range);

static uint32_t ticks[2], tick_at;
uint32_t TickCount(void)
{
    if (tick_at >= 2) abort();
    return ticks[tick_at++];
}
static int fixture_read_seed(void *context, uint32_t *value)
{
    *value = *(uint32_t *)context;
    return 1;
}
typedef struct Scenario { uint32_t mode, seed, tick1, tick2; } Scenario;
static const Scenario scenarios[] = {
    {0,0,0,0}, {0,1,0,0}, {0,7,0,0}, {0,0x3751,0,0},
    {0,0x7fff,0,0}, {0,0x8000,0,0}, {0,0xffff,0,0}, {0,0xace1,0,0},
    {1,7,0,0}, {1,7,1,1}, {1,7,65535,65536},
    {1,0x12345678,0x12345678,0x12345679}
};
typedef struct Operation { const char *name; uint16_t arg; } Operation;
static const Operation operations[] = {
    {"SRand1",1}, {"SRand4",0}, {"SRand256",0}, {"SRand1",17},
    {"SRand2",0}, {"SRand128",0}, {"SRand1",65535}, {"SRand1",32768},
    {"SGIRand",127}, {"SGRand",127}, {"SGSRand",31}, {"RRand",32767},
    {"SRand8",0}, {"SRand16",0}, {"SRand32",0}, {"SRand64",0}
};
static int16_t invoke(const Operation *op)
{
    if (!strcmp(op->name,"SRand1")) return SRand1(op->arg);
    if (!strcmp(op->name,"SGIRand")) return SGIRand((int16_t)op->arg);
    if (!strcmp(op->name,"SGRand")) return SGRand((int16_t)op->arg);
    if (!strcmp(op->name,"SGSRand")) return SGSRand((int16_t)op->arg);
    if (!strcmp(op->name,"RRand")) return RRand((int16_t)op->arg);
    if (!strcmp(op->name,"SRand2")) return SRand2();
    if (!strcmp(op->name,"SRand4")) return SRand4();
    if (!strcmp(op->name,"SRand8")) return SRand8();
    if (!strcmp(op->name,"SRand16")) return SRand16();
    if (!strcmp(op->name,"SRand32")) return SRand32();
    if (!strcmp(op->name,"SRand64")) return SRand64();
    if (!strcmp(op->name,"SRand128")) return SRand128();
    if (!strcmp(op->name,"SRand256")) return SRand256();
    abort();
}
int main(int argc, char **argv)
{
    unsigned s, j, r, n;
#if defined(_WIN32)
    /* Keep the deliberate excluded-domain abort unattended in this fixture. */
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    {
        typedef unsigned int (__cdecl *AbortBehavior)(unsigned int,unsigned int);
        HMODULE runtime=GetModuleHandleA("msvcrt.dll");
        AbortBehavior behavior=runtime ? (AbortBehavior)GetProcAddress(runtime,"_set_abort_behavior") : NULL;
        if (behavior) behavior(0,_WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    }
#endif
    /* Existing DOS negative-domain control: zero must reach division failure,
     * after private seed advancement. The installed service aborts that domain. */
    if (argc == 2 && !strcmp(argv[1],"--srand1-zero")) {
        SetSRandSeed((int16_t)0xa55a);
        (void)SRand1(0);
        return 0;
    }
    for (s=0; s<sizeof(scenarios)/sizeof(scenarios[0]); ++s) {
        Scenario c=scenarios[s];
        ticks[0]=c.tick1; ticks[1]=c.tick2; tick_at=0;
        if (!portable_seed_source_bind(fixture_read_seed,&c.seed)) abort();
        dos_crt_srand(1);
        if (c.mode) SeedRRand(); else SetSRandSeed((int16_t)c.seed);
        printf("%u,-1,0,%u,%u\n",s,GetSRandSeed(),tick_at);
        n=0;
        for (r=0; r<16; ++r) for (j=0; j<sizeof(operations)/sizeof(operations[0]); ++j) {
            int16_t value=invoke(&operations[j]);
            printf("%u,%u,%d,%u,%u\n",s,n++,(int)value,GetSRandSeed(),tick_at);
        }
        printf("%u,99999,%u,%u,%u\n",s,GetRRandSeed(),GetSRandSeed(),tick_at);
        portable_seed_source_unbind();
    }
    return 0;
}
