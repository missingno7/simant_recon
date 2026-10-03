/* Root module 078E: pointer allocation helpers (memory-manager handles dereferenced). */

typedef char far * far *Handle;

extern void far Punt(char far *message);
extern Handle far f_171C_13CA(long size, int flags, char far *name);

char far * far f_078E_000C(long size, char far *name)
{
    if (size > 0xffffL)
        Punt("NewPtr argument too large");
    return *f_171C_13CA(size, 0, name);
}

extern void far * far _fmemset(void far *dst, int c, unsigned n);

char far * far f_078E_0053(long size, char far *name)
{
    Handle h;

    _fmemset(*(h = f_171C_13CA(size, 0, name)), 0, (unsigned)size);
    return *h;
}
