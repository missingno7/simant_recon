/* f_171C_0CF4 near-exact (2 bytes: mov cx,es vs mov dx,es at 0DAC) with --flags /AL /Oeg /Gs /Zi.
   Differences from work/mem/best_0CF4.c: no seg variable (SEG(b) repeated -> CSE temp slot at -1Ah),
   an extra dead counter local (count = 0; count++ after moved = 1) giving the -18h slot and the
   sub ax,ax / mov [bp-16h],ax prologue, and this declaration order (half of all orders give 488 bytes).
   Placing it in m171C.c (outside a scaffold) breaks f_171C_2086 via identifier counts. */
int far f_171C_0CF4(int emsOnly)
{
    int moved;
    Block far *n;
    long size;
    int t;
    int count;
    unsigned paras;
    Block far *b;
    unsigned end;

    moved = 0;
    count = 0;
    b = g_91A4;
    end = emsOnly ? fd_50F6_3950 : s_8C70;
    for (; (unsigned)SEG(b) < end; b = BLK(b->paras + (unsigned)SEG(b))) {
        if (b->type != 0x80)
            continue;
        n = BLK(b->paras + (unsigned)SEG(b));
        if ((unsigned)SEG(n) < end && (t = n->type, !n->lock) && (t == 1 || t == 3) && !(n->attr & 0x10)) {
            f_171C_0ADC(b);
            continue;
        }
        while ((unsigned)SEG(n) < end) {
            if ((t = n->type, !n->lock) && (t == 1 || t == 3) && b->paras >= n->paras)
                goto found;
            n = NEXTBLK(n);
        }
        continue;
found:
        paras = n->paras;
        size = n->size;
        f_171C_068C(b, paras, t);
        _fmemcpy(b->name, n->name, 13);
        b->size = size;
        f_194D_0006((char far *)((long)b + 0x20000L), (char far *)((long)n + 0x20000L), paras - 2);
        b->handle = n->handle;
        b->age = n->age;
        b->attr = n->attr;
        _disable();
        *(Handle)((char far *)s_2F46 + b->handle) = (char far *)((long)b + 0x20000L);
        _enable();
        f_171C_0160(n, 1);
        moved = 1;
        count++;
    }
    return moved;
}



