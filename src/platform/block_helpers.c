/*
 * Contains BlockMove, a debug byte swap dump and barrier level setters. These unrelated small
 * helpers remain together because they share one original code module.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0244; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Zi.
 */

extern void far * far _fmemcpy(void far *dest, void far *src, unsigned n);

void far BlockMove(void far *src, void far *dst, unsigned n)
{
    _fmemcpy(dst, src, n);
}

extern long far RallocSize(void far * far *h);
extern int far WinPrintf(char far *format, ...);

void far FlipHandleWords(unsigned far * far *h)
{
    unsigned far *p;
    int n;
    int i;
    unsigned w;

    n = RallocSize(h) / 2L;
    p = *h;
    for (i = 0; i < n; i++, p++) {
        w = *p;
        WinPrintf("\ni=%d, j=%x", i, w);
        *p = (w >> 8) | (w << 8);
        WinPrintf("  = %x", *p);
    }
}

extern int far Barrier;

void far OverlayOutsideTiles(void)
{
    Barrier = 0x50;
}

void far OverlayInsideTiles(void)
{
    Barrier = 0x90;
}
