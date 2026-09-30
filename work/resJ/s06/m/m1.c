extern int far A, far B, far C, far D, far E, far F, far G, far H, far K;
extern int far L[2];
void far f(void)
{
    E = (A + B - 200) / 28;
    F = (B - 38) / 10;
    if (F != L[1] || L[0] != E)
        return;
    C = 1;
    G = (B - 38) % 10;
    H = (A + B - 200) % 28;
    H = ((H << 2) + 6) & 0x7f;
    G = ((G + 1) * 6) & 0x3f;
}
