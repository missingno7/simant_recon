#include <stdint.h>
#include <stdio.h>

extern void SetSRandSeed(int16_t);
extern int16_t __real_SRand1(uint16_t);
extern void AddRandAntLion(void);

int16_t __wrap_SRand1(uint16_t range)
{
    printf("%u\n", (unsigned)range);
    return __real_SRand1(range);
}

/* A clear placement ends after one attempt; the production RNG, creature TU,
   map writes and list storage still execute from the native object inventory. */
int16_t __wrap_IsClear3x3(int16_t plane, int16_t x, int16_t y)
{
    (void)plane; (void)x; (void)y;
    return 1;
}

int main(void)
{
    SetSRandSeed(0x3751);
    AddRandAntLion();
    return 0;
}
