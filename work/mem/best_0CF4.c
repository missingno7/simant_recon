int far f_171C_0CF4(int emsOnly)
{
    int t;
    unsigned seg;
    long size;
    unsigned paras;
    Block far *n;
    unsigned end;
    Block far *b;
    int moved;

    moved = 0;
    b = g_91A4;
    end = emsOnly ? fd_50F6_3950 : s_8C70;
    for (; (seg = (unsigned)SEG(b)) < end; b = BLK(b->paras + seg)) {
        if (b->type != 0x80)
            continue;
        n = BLK(b->paras + seg);
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
    }
    return moved;
}
