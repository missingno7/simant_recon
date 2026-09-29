/* Overlay section S07, code frame 35F5: cheat key handler. */

extern int far fd_3D57_06DE;
extern char far fd_50F6_0B0A[];
extern char far fd_3D57_067E[][4];
extern int far fd_50F6_0850;
extern int far fd_50F6_048A;
extern int far fd_50F6_047C;
extern char far fd_3D57_0008[];
extern char far fd_3D57_0000[];
extern int far fd_50F6_10BE;
extern int far fd_50F6_01FE;
extern int far fd_3D57_0C18;
extern int far fd_50F6_07C8;
extern int far fd_3D57_0C14;
extern int far fd_3D57_0C12;
extern unsigned char far fd_3D57_00A4[12][16];
extern int far fd_50F6_0A90;
extern unsigned char far fd_3D57_0164[12][16];
extern int far fd_50F6_0AC4;
extern int far fd_3D57_0C16;
extern int far fd_50F6_0F78;

extern void far WinPrintf(char far *fmt, ...);
extern void far f_00DF_00E8(int sound, int a, int b);
extern void far f_00DF_00E0(int a);
extern void far f_10F7_1DD3(int health);
extern void far o14_384C_0B6A(int a, int b, int c);
extern void far f_00F8_059C(void);
extern void far f_00F8_02DF(int a);
extern void far f_00F8_0395(void);
extern void far MakeNewHoleB(int x);
extern void far f_14EE_0367(int x);
extern void far o08_35F5_0C4C(int x, int y, int dir);
extern void far o08_35F5_0DA0(int x, int y, int dir);
extern int far RRand(int range);
extern int far SRand2(void);
extern int far SRand8(void);
extern void far f_0BE8_0A5B(int x, int y, int type);
extern void far f_0BE8_0ABE(int x, int y, int type);
extern void far o16_384C_0000(void);

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
        f_00DF_00E8(10, 0, 0x7e);
        fd_50F6_0850 += 10;
        break;
    case 1:
        f_00DF_00E8(1, 0, 0x7e);
        f_10F7_1DD3(100);
        break;
    case 2:
        f_00DF_00E8(1, 0, 0x7e);
        f_10F7_1DD3(1);
        break;
    case 3:
        o14_384C_0B6A(0, 0x2724, 0);
        break;
    case 4:
        o14_384C_0B6A(0, 0x2726, 0);
        f_00F8_059C();
        f_00F8_02DF(6);
        f_00DF_00E0(0);
        f_00F8_02DF(0);
        o14_384C_0B6A(0, 0x2728, 0);
        break;
    case 5:
        for (i = 0; i < 64; i++)
            MakeNewHoleB(i);
        break;
    case 6:
        for (i = 0; i < 64; i++)
            f_14EE_0367(i);
        break;
    case 7:
        o08_35F5_0C4C(fd_50F6_047C + 2, fd_50F6_048A, 2);
        break;
    case 8:
        o08_35F5_0DA0(fd_50F6_047C + 2, fd_50F6_048A, 2);
        break;
    case 9:
        for (i = 0; i < 16; i++)
            f_0BE8_0A5B(fd_3D57_0000[SRand8()] + fd_50F6_047C, fd_3D57_0008[SRand8()] + fd_50F6_048A, RRand(6) + 1);
        break;
    case 10:
        for (i = 0; i < 16; i++)
            f_0BE8_0ABE(fd_3D57_0000[SRand8()] + fd_50F6_047C, fd_3D57_0008[SRand8()] + fd_50F6_048A, RRand(6) + 0x81);
        break;
    case 11:
        fd_50F6_10BE = 100;
        break;
    case 12:
        fd_50F6_01FE = 100;
        break;
    case 13:
        fd_50F6_01FE = 0;
        break;
    case 14:
        fd_3D57_0C18 = 0;
        fd_50F6_10BE = 0;
        break;
    case 15:
        fd_50F6_07C8 += 10;
        f_00F8_0395();
        f_00DF_00E8(0x29, 0, 0x7e);
        break;
    case 16:
        fd_3D57_0C14 = !fd_3D57_0C14;
        if (fd_3D57_0C14)
            f_00DF_00E8(2, 0, 0x7e);
        else
            f_00DF_00E8(1, 0, 0x7e);
        break;
    case 17:
        fd_3D57_0C12 = !fd_3D57_0C12;
        if (fd_3D57_0C12)
            f_00DF_00E8(2, 0, 0x7e);
        else
            f_00DF_00E8(1, 0, 0x7e);
        break;
    case 18:
        f_00DF_00E8(2, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                fd_3D57_00A4[i][j] += 4;
                fd_50F6_0A90++;
            }
        break;
    case 19:
        f_00DF_00E8(1, 0, 0x7e);
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
        o16_384C_0000();
        break;
    case 21:
        fd_3D57_0C16 = !fd_3D57_0C16;
        if (fd_3D57_0C16) {
            fd_50F6_0F78 = 100;
            f_00DF_00E8(2, 0, 0x7e);
        } else
            f_00DF_00E8(1, 0, 0x7e);
        break;
    case 22:
        fd_3D57_0C18 = !fd_3D57_0C18;
        if (fd_3D57_0C18) {
            fd_50F6_10BE = 100;
            f_00DF_00E8(2, 0, 0x7e);
        } else
            f_00DF_00E8(1, 0, 0x7e);
        break;
    }
}
