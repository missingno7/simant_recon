/*
 * Random numbers (root module, code frame 0093; linear 0x932-0xBA1).
 * Profile: MSC 6.00 /AL /Os /Oe.  /Oe (global register allocation) is required:
 * plain autos land in SI/DI while their unused BP homes remain, which is the
 * frame shape of SGSRand, SeedRRand and RRand.
 *
 * Same translation unit as the Win16 build's SetSRandSeed..SRand256 group
 * (simantw_recon unit simone_1506): an LFSR "S" generator with feedback
 * 0x1BF5 whose state is this module's private seed, and an "R" generator on
 * the C runtime rand().  The DOS module additionally holds three two-draw
 * helpers and a BIOS tick reader.  SRand1..SRand256 are inline assembly in
 * the original (dead "mov dx, 0" and flag-based branch no C form produces).
 */

extern unsigned long far TickCount(void);
extern void far srand(unsigned int seed);
extern int far rand(void);

int far SRand1(unsigned int range);
int far SRand2(void);
int far SRand128(void);

static unsigned int seed;

int far SGIRand(int range)
{
    int first;
    int second;

    first = SRand1(range);
    second = SRand1(range);
    if (second < first)
        return first;
    return second;
}

int far SGRand(int range)
{
    int first;
    int second;

    first = SRand1(range);
    second = SRand1(range);
    if (second > first)
        return first;
    return second;
}

int far SGSRand(int range)
{
    int first;
    int second;

    first = SRand1(range);
    second = SRand1(range);
    if (second > first)
        second = first;
    if (SRand2())
        second = -second;
    return second;
}

void far SetSRandSeed(int value)
{
    seed = value;
}

unsigned long far GetSRandSeed(void)
{
    return seed;
}

void far SetRRandSeed(void)
{
}

unsigned long far GetRRandSeed(void)
{
    return *(unsigned long far *)0x046C0000L;
}

void far SeedSRand(void)
{
    seed = (unsigned int)TickCount() ^ 0x3751;
}

void far SeedRRand(void)
{
    int count;
    int i;

    SeedSRand();
    count = SRand128();
    srand((unsigned int)TickCount());
    for (i = 0; i < count; i++)
        rand();
}

int far RRand(int limit)
{
    int value;

    value = rand();
    if (value < 0)
        value = -value;
    return value % limit;
}

int far SRand1(unsigned int range)
{
    int result;

    _asm {
        mov dx, 0
        mov ax, seed
        shl ax, 1
        jnc done1
        xor ax, 1bf5h
    done1:
        mov seed, ax
        mov bx, range
        div bx
        mov ax, dx
        mov result, ax
    }
    return result;
}

#define SRAND_MASK(name, label, mask) \
int far name(void)                    \
{                                     \
    _asm { mov dx, 0 }                \
    _asm { mov ax, seed }             \
    _asm { shl ax, 1 }                \
    _asm { jnc label }                \
    _asm { xor ax, 1bf5h }            \
    _asm { label: mov seed, ax }      \
    _asm { and ax, mask }             \
}

SRAND_MASK(SRand2, d2, 1)
SRAND_MASK(SRand4, d4, 3)
SRAND_MASK(SRand8, d8, 7)
SRAND_MASK(SRand16, d16, 0fh)
SRAND_MASK(SRand32, d32, 1fh)
SRAND_MASK(SRand64, d64, 3fh)
SRAND_MASK(SRand128, d128, 7fh)
SRAND_MASK(SRand256, d256, 0ffh)
