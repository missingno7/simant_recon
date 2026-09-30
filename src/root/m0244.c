/* Root module 0244: block move, a debug byte-swap dump, and the barrier level setters. */

extern void far * far _fmemcpy(void far *dest, void far *src, unsigned n);

void far f_0244_0000(void far *src, void far *dst, unsigned n)
{
    _fmemcpy(dst, src, n);
}

extern long far f_171C_16EA(void far * far *h);
extern int far WinPrintf(char far *format, ...);

void far f_0244_0022(unsigned far * far *h)
{
    unsigned far *p;
    int n;
    int i;
    unsigned w;

    n = f_171C_16EA(h) / 2L;
    p = *h;
    for (i = 0; i < n; i++, p++) {
        w = *p;
        WinPrintf("\ni=%d, j=%x", i, w);
        *p = (w >> 8) | (w << 8);
        WinPrintf("  = %x", *p);
    }
}

extern int far Barrier;

void far f_0244_00A7(void)
{
    Barrier = 0x50;
}

void far f_0244_00BA(void)
{
    Barrier = 0x90;
}
