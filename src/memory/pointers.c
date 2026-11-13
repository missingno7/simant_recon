/*
 * Allocates and frees pointer style storage using memory manager handles. It dereferences the
 * master pointer and rejects allocations that exceed its pointer size limit.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 078E; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 */

typedef char far * far *Handle;

extern void far Punt(char far *message);
extern Handle far Ralloc(long size, int flags, char far *name);

/*
 * Allocate a hard block and return its data pointer; reject sizes above 65535 bytes.
 */
char far * far mem_alloc_pointer(long size, char far *name)
{
    if (size > 0xffffL)
        Punt("NewPtr argument too large");
    return *Ralloc(size, 0, name);
}

extern void far * far _fmemset(void far *dst, int c, unsigned n);

/*
 * Allocate a hard block and zero the low-word byte count before returning its pointer.
 */
char far * far mem_alloc_zeroed_pointer(long size, char far *name)
{
    Handle h;

    _fmemset(*(h = Ralloc(size, 0, name)), 0, (unsigned)size);
    return *h;
}
