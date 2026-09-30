extern int far P, far Q, far R, far S, far T, far U;
extern int far g5(int, int, int far *, int far *, int far *, int far *, int far *);
extern int far ab(int);
extern int far g4(int, int, int, int);
extern void far h(void);
int far f0(void)
{
    int ty, tattr, tx, tdir, tstate, dx, dy, d;
    if (g5(P, Q, &tx, &ty, &tattr, &tstate, &tdir) == 0 || ((R ^ tattr) & 0xf0) != 0)
        return -2;
    if (S == P) {
        dx = ab(T - tx);
        dy = ab(U - ty);
        if (dx <= 1 && dy <= 1) {
            d = g4(T, U, tx, ty) - 1;
            if (d >= 0) R = d;
            h();
            return -1;
        }
    }
    S = P = tx;
    Q = R = ty;
    return 0;
}
