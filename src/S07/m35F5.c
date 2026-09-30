/* Overlay section S07, code frame 35F5: cheat key handler. */

extern int far fd_3D57_06DE;
extern char far fd_50F6_0B0A[];
extern char far fd_3D57_067E[][4];
extern int far fd_50F6_0850;
extern int far MeLocY;
extern int far MeLocX;
extern char far Dy8[];
extern char far Dx8[];
extern int far HealthB;
extern int far HealthR;
extern int far fd_3D57_0C18;
extern int far fd_50F6_07C8;
extern int far fd_3D57_0C14;
extern int far fd_3D57_0C12;
extern unsigned char far fd_3D57_00A4[12][16];
extern int far fd_50F6_0A90;
extern unsigned char far fd_3D57_0164[12][16];
extern int far fd_50F6_0AC4;
extern int far fd_3D57_0C16;
extern int far MeHealth;

extern void far WinPrintf(char far *fmt, ...);
extern void far myBeginSound(int sound, int a, int b);
extern void far f_00DF_00E0(int a);
extern void far SetMyHealth(int health);
extern void far o14_384C_0B6A(int a, int b, int c);
extern void far UpdateEverything(void);
extern void far SetSimCursor(int a);
extern void far InvalQueenStorageDisp(void);
extern void far MakeNewHoleB(int x);
extern void far MakeNewHoleR(int x);
extern void far MakeBlkQueen(int x, int y, int dir);
extern void far MakeRedQueen(int x, int y, int dir);
extern int far RRand(int range);
extern int far SRand2(void);
extern int far SRand8(void);
extern void far PlaceEggB(int x, int y, int type);
extern void far PlaceEggR(int x, int y, int type);
extern void far DrawSimPayoff(void);

void far CheatKeys(int key)
{
    int i, j, k;
    char far *p;

    fd_50F6_0B0A[fd_3D57_06DE] = ~key;
    fd_3D57_06DE++;
    for (i = 0; fd_3D57_067E[i][0] != 0; i++) {
        p = fd_3D57_067E[i];
        for (j = 0; j < fd_3D57_06DE; j++)
            if (p[j] != fd_50F6_0B0A[j])
                break;
        if (j == fd_3D57_06DE)
            break;
    }
    if (fd_3D57_067E[i][0] == 0) {
        for (k = fd_3D57_06DE = 0; k < 4; k++)
            fd_50F6_0B0A[k] = 0;
        return;
    }
    if (fd_3D57_06DE < 4)
        return;
    for (k = fd_3D57_06DE = 0; k < 4; k++)
        fd_50F6_0B0A[k] = 0;
    WinPrintf("CHEAT %d", i);
    switch (i) {
    case 0:
        myBeginSound(10, 0, 0x7e);
        fd_50F6_0850 += 10;
        break;
    case 1:
        myBeginSound(1, 0, 0x7e);
        SetMyHealth(100);
        break;
    case 2:
        myBeginSound(1, 0, 0x7e);
        SetMyHealth(1);
        break;
    case 3:
        o14_384C_0B6A(0, 0x2724, 0);
        break;
    case 4:
        o14_384C_0B6A(0, 0x2726, 0);
        UpdateEverything();
        SetSimCursor(6);
        f_00DF_00E0(0);
        SetSimCursor(0);
        o14_384C_0B6A(0, 0x2728, 0);
        break;
    case 5:
        for (i = 0; i < 64; i++)
            MakeNewHoleB(i);
        break;
    case 6:
        for (i = 0; i < 64; i++)
            MakeNewHoleR(i);
        break;
    case 7:
        MakeBlkQueen(MeLocX + 2, MeLocY, 2);
        break;
    case 8:
        MakeRedQueen(MeLocX + 2, MeLocY, 2);
        break;
    case 9:
        for (i = 0; i < 16; i++)
            PlaceEggB(Dx8[SRand8()] + MeLocX, Dy8[SRand8()] + MeLocY, RRand(6) + 1);
        break;
    case 10:
        for (i = 0; i < 16; i++)
            PlaceEggR(Dx8[SRand8()] + MeLocX, Dy8[SRand8()] + MeLocY, RRand(6) + 0x81);
        break;
    case 11:
        HealthB = 100;
        break;
    case 12:
        HealthR = 100;
        break;
    case 13:
        HealthR = 0;
        break;
    case 14:
        fd_3D57_0C18 = 0;
        HealthB = 0;
        break;
    case 15:
        fd_50F6_07C8 += 10;
        InvalQueenStorageDisp();
        myBeginSound(0x29, 0, 0x7e);
        break;
    case 16:
        fd_3D57_0C14 = !fd_3D57_0C14;
        if (fd_3D57_0C14)
            myBeginSound(2, 0, 0x7e);
        else
            myBeginSound(1, 0, 0x7e);
        break;
    case 17:
        fd_3D57_0C12 = !fd_3D57_0C12;
        if (fd_3D57_0C12)
            myBeginSound(2, 0, 0x7e);
        else
            myBeginSound(1, 0, 0x7e);
        break;
    case 18:
        myBeginSound(2, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                fd_3D57_00A4[i][j] += 4;
                fd_50F6_0A90++;
            }
        break;
    case 19:
        myBeginSound(1, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                if (SRand2() == 0) {
                    fd_3D57_00A4[i][j]++;
                    fd_50F6_0A90++;
                } else {
                    fd_3D57_0164[i][j]++;
                    fd_50F6_0AC4++;
                }
            }
        break;
    case 20:
        DrawSimPayoff();
        break;
    case 21:
        fd_3D57_0C16 = !fd_3D57_0C16;
        if (fd_3D57_0C16) {
            MeHealth = 100;
            myBeginSound(2, 0, 0x7e);
        } else
            myBeginSound(1, 0, 0x7e);
        break;
    case 22:
        fd_3D57_0C18 = !fd_3D57_0C18;
        if (fd_3D57_0C18) {
            HealthB = 100;
            myBeginSound(2, 0, 0x7e);
        } else
            myBeginSound(1, 0, 0x7e);
        break;
    }
}
