/* Root module 0CDB: the spider (InitSpider .. SGetDis, Win16 SIMONE_MODULE order). */

extern int far SpidBurpCnt;
extern int far EatCnt;
extern int far SCorpseBase;
extern int far Scycle;
extern int far Scycle2;
extern int far SpidRevenge;
extern int far fd_50F6_1004;
extern int far fd_3D57_0C12;
extern int far fd_50F6_0EAC;
extern int far fd_50F6_0F0C;
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;
extern int far SMode;
extern int far fd_50F6_06AC;
extern int far Starg;
extern int far StargLife;
extern int far SuserX;
extern int far SuserY;

void far InitSpider(void)
{
    SpidBurpCnt = 10;
    EatCnt = 0;
    SCorpseBase = 0;
    Scycle = 0;
    Scycle2 = 0;
    SpidRevenge = 0;
    fd_50F6_1004 = 0;
    fd_3D57_0C12 = 0;
    if (fd_50F6_0EAC)
        fd_50F6_0F0C = 1;
    else
        fd_50F6_0F0C = 0;
    fd_50F6_0F12 = 0x400;
    fd_50F6_0F34 = 0x200;
    fd_50F6_06AC = SMode = 0;
    Starg = -2;
    StargLife = -1;
    SuserY = SuserX = 64;
}

extern int far fd_50F6_0A06;
int far SFoundAnt(void);
extern unsigned char far AlistT[];
int far SpiderScan(void);
extern int far MeLocY;
extern int far MeLocX;
extern unsigned long far GetDis(int x1, int y1, int x2, int y2);
extern int far o25_39C7_0CBD(int plane, int x, int y, int gx, int gy);
extern int far GetDir(int x1, int y1, int x2, int y2);
extern signed char far TurnTab[][8];
extern int far fd_50F6_0A8E;
extern signed char far fd_3D57_0994[];
extern signed char far fd_3D57_099C[];
extern int far fd_3D57_07A8[];
extern void far f_015B_06A2(void);
extern int far SRand1(int range);
int far ScanForAnts(void);
void far KillSpider(void);
extern void far YellowDeath(int cause);
extern void far PictStrnDialog(int pict, int strn, int flag);
extern int far SRand2(void);
extern int far MePlane;
extern unsigned char far AlistY[];
extern unsigned char far AlistX[];
int far SGetDis(int x1, int y1, int x2, int y2);
extern void far myBeginSound(int sound, int a, int b);
extern int far DeathCnt;
extern void far f_0BE8_0812(int x, int y);
extern long far RAntsEaten;
extern long far BAntsEaten;
extern unsigned char far LifeA[128][64];
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern int far fd_50F6_04C2;
extern int far fd_50F6_0496;
extern signed char far fd_3D57_09AC[];
extern signed char far fd_3D57_09A4[];
extern int far TERRAINset;
extern unsigned char far MapA[128][64];
extern int far SRand4(void);
extern int far SRand256(void);
extern void far DeadAntHere(int x, int y, int type);
extern int far f_10F7_2867(int x, int y);

void far MoveSpider(void)
{
    int x;
    int y;
    int d;
    int r;

    Scycle2 = (Scycle2 + 1) & 0x3ff;
    x = fd_50F6_0F12 >> 4;
    y = fd_50F6_0F34 >> 4;
    if (fd_50F6_0A06 == 1 && SMode != 2 && SMode != 3) {
        if (fd_50F6_06AC == 7) {
            Starg = SFoundAnt();
            if (Starg != -2) {
                SMode = 2;
                if (Starg >= 0)
                    StargLife = AlistT[Starg];
                else
                    StargLife = 0xff;
                return;
            }
        } else if (fd_50F6_06AC == 8)
            SpiderScan();
        d = (int)GetDis(MeLocX, MeLocY, SuserX, SuserY);
        if (d < 1) {
            Scycle = 2;
            return;
        }
        r = o25_39C7_0CBD(1, MeLocX, MeLocY, SuserX, SuserY);
        if (r == -1)
            return;
        if (r == -2) {
            r = GetDir(MeLocX, MeLocY, SuserX, SuserY) - 1;
            if (r < 0)
                return;
        }
        fd_50F6_1004 = TurnTab[fd_50F6_1004][r];
        if (fd_50F6_0A8E && d > 2) {
            fd_50F6_0F12 += 5 * fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 += 5 * fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle + 2) & 0x3ff;
        } else {
            fd_50F6_0F12 += fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 += fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle + 1) & 0x3ff;
        }
        MeLocX = fd_50F6_0F12 >> 4;
        MeLocY = fd_50F6_0F34 >> 4;
        if (fd_3D57_07A8[0])
            f_015B_06A2();
        return;
    }
    if (!fd_50F6_0F0C) {
        if (!fd_50F6_0EAC)
            return;
        if (SRand1(300))
            return;
        fd_50F6_0F12 = SRand1(0x400) + 0x200;
        SMode = fd_50F6_0F0C = 1;
        fd_3D57_0C12 = 0;
        if (SRand1(2)) {
            fd_50F6_0F34 = 1;
            fd_50F6_1004 = 4;
        } else {
            fd_50F6_0F34 = 0x3ff;
            fd_50F6_1004 = 0;
        }
        return;
    }
    if (!(Scycle2 & 3) && SMode < 5) {
        r = ScanForAnts();
        if (r > 8) {
            KillSpider();
            if (fd_50F6_0A06 != 1) {
                PictStrnDialog(0, 0x273e, 0);
                if (SpidRevenge < 5)
                    SpidRevenge++;
                if (SpidRevenge < 3)
                    return;
                if (SpidRevenge >= 5)
                    fd_50F6_06AC = 8;
                else
                    fd_50F6_06AC = 7;
                if (SpidRevenge >= 6 && !SRand2()) {
                    SpidRevenge = 0;
                    fd_50F6_06AC = 0;
                }
                return;
            }
            fd_50F6_0A06 = 0;
            YellowDeath(3);
            return;
        }
        if (r > 4)
            SMode = 4;
    }
    if (SMode < 4 && fd_50F6_06AC == 8)
        SpiderScan();
    switch (SMode) {
    case 0:
        Scycle = 2;
        if (!SRand1(150))
            SMode = 1;
        if ((Starg = SFoundAnt()) != -2) {
            SMode = 2;
            if (Starg >= 0)
                StargLife = AlistT[Starg];
            else
                StargLife = 0xff;
            return;
        }
        if (!SRand1(30))
            fd_50F6_1004 = TurnTab[fd_50F6_1004][SRand1(8)];
        if (fd_50F6_06AC == 8)
            SpiderScan();
        break;
    case 1:
        if (fd_3D57_0C12) {
            fd_50F6_0F12 -= fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 -= fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle - 1) & 0x3ff;
        } else {
            fd_50F6_0F12 += fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 += fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle + 1) & 0x3ff;
        }
        if (!SRand1(20))
            fd_50F6_1004 = TurnTab[fd_50F6_1004][SRand1(8)];
        if ((Starg = SFoundAnt()) != -2) {
            SMode = 2;
            if (Starg >= 0)
                StargLife = AlistT[Starg];
            else
                StargLife = 0xff;
            return;
        }
        if (!SRand1(50)) {
            SMode = 0;
            Scycle = 2;
        }
        break;
    case 2:
        if (Starg >= 0) {
            if ((AlistT[Starg] ^ StargLife) & 0xf0) {
                SMode = 0;
                Starg = -2;
                if (fd_50F6_0A06 != 1)
                    return;
                y = fd_50F6_0F34 >> 4;
                x = fd_50F6_0F12 >> 4;
                SuserY = y;
                SuserX = x;
                MeLocX = x;
                MeLocY = y;
                if (fd_50F6_06AC == 6)
                    fd_50F6_06AC = 0;
                if (fd_3D57_07A8[0])
                    f_015B_06A2();
                return;
            }
        } else if (MePlane > 1) {
            SMode = 0;
            Starg = -2;
            return;
        }
        if (Starg < 0)
            d = SGetDis(x, y, MeLocX, MeLocY);
        else
            d = SGetDis(x, y, AlistX[Starg], AlistY[Starg]);
        if (d > 64 && fd_50F6_0A06 != 1) {
            SMode = 0;
            Starg = -2;
            return;
        }
        if (d < 2) {
            SMode = 3;
            fd_50F6_0F12 = (fd_50F6_0F12 & 0xfff0) + 8;
            fd_50F6_0F34 = (fd_50F6_0F34 & 0xfff0) + 8;
            goto eat;
        }
        if (Starg < 0)
            d = GetDir(x, y, MeLocX, MeLocY);
        else
            d = GetDir(x, y, AlistX[Starg], AlistY[Starg]);
        fd_50F6_1004 = TurnTab[fd_50F6_1004][d - 1];
        if (Starg < 0)
            myBeginSound(0x2f, 0, 0x7e);
        else
            myBeginSound(0x2f, 0, -5);
        if (fd_3D57_0C12) {
            fd_50F6_0F12 -= 5 * fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 -= 5 * fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle - 2) & 0x3ff;
        } else {
            fd_50F6_0F12 += 5 * fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 += 5 * fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle + 2) & 0x3ff;
        }
        if (fd_50F6_0A06 == 1) {
            MeLocX = fd_50F6_0F12 >> 4;
            MeLocY = fd_50F6_0F34 >> 4;
            if (fd_3D57_07A8[0])
                f_015B_06A2();
        }
        break;
    case 3:
    eat:
        if (fd_50F6_0A06 == 1) {
            MeLocX = fd_50F6_0F12 >> 4;
            MeLocY = fd_50F6_0F34 >> 4;
            if (fd_50F6_06AC == 6)
                fd_50F6_06AC = 0;
            if (fd_3D57_07A8[0])
                f_015B_06A2();
        }
        if (Starg != -2) {
            if (Starg >= 0) {
                if (!(((unsigned char)StargLife ^ AlistT[Starg]) & 0xf0)) {
                    if (StargLife & 0x80) {
                        RAntsEaten++;
                        SCorpseBase = 4;
                    } else {
                        BAntsEaten++;
                        SCorpseBase = 0;
                    }
                    LifeA[AlistX[Starg]][AlistY[Starg]] = 0;
                    AlistT[Starg] = 0;
                } else {
                    Starg = -2;
                    goto done;
                }
            } else {
                MoveMyLife(MePlane, (fd_3D57_09A4[fd_50F6_1004] + x) & 0x7f,
                           (fd_3D57_09AC[fd_50F6_1004] + y) & 0x3f, fd_50F6_04C2, fd_50F6_0496);
                YellowDeath(1);
                SCorpseBase = 0;
            }
            Starg = -2;
            EatCnt = fd_50F6_06AC >= 7 ? 11 : 50;
        }
        d = (fd_3D57_09A4[fd_50F6_1004] + x) & 0x7f;
        r = (fd_3D57_09AC[fd_50F6_1004] + y) & 0x3f;
        if (!TERRAINset && MapA[d][r] < 0x18)
            MapA[d][r] = SRand4() + SCorpseBase + 0x10;
        if (EatCnt > 0) {
            EatCnt--;
            if (EatCnt % 10 == 0 && SRand2())
                myBeginSound(0x2c, (SRand256() << 3) + 0x2777, -5);
            break;
        }
        if (--SpidBurpCnt == 0) {
            SpidBurpCnt = 10;
            if (fd_3D57_07A8[5] && !SRand2())
                myBeginSound(10, 0, 10);
        }
        DeadAntHere(d, r, SCorpseBase);
    done:
        SMode = 0;
        if (fd_50F6_0A06 == 1) {
            if (fd_50F6_06AC == 6)
                fd_50F6_06AC = 0;
            SuserX = x;
            SuserY = y;
        }
        break;
    case 4:
        fd_50F6_1004 = TurnTab[fd_50F6_1004][SRand1(8)];
        if (fd_3D57_0C12) {
            fd_50F6_0F12 -= 5 * fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 -= 5 * fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle - 2) & 0x3ff;
        } else {
            fd_50F6_0F12 += 5 * fd_3D57_0994[fd_50F6_1004];
            fd_50F6_0F34 += 5 * fd_3D57_099C[fd_50F6_1004];
            Scycle = (Scycle + 2) & 0x3ff;
        }
        if (!SRand1(50)) {
            SMode = 0;
            Scycle = 2;
        }
        break;
    case 5:
        if (--DeathCnt == 0) {
            SMode = fd_50F6_0F0C = 0;
            f_0BE8_0812(x, y);
            f_0BE8_0812(x, y);
            f_0BE8_0812(x, y);
            return;
        }
        if (SRand1(1000) < DeathCnt) {
            if (DeathCnt > 400)
                Scycle = SRand1(3) + 1;
            else
                Scycle = SRand1(2) + 2;
        }
        break;
    }
    if (!f_10F7_2867(fd_50F6_0F12 >> 4, fd_50F6_0F34 >> 4)) {
        fd_50F6_0F0C = 0;
        if (fd_50F6_0A06 == 1) {
            fd_50F6_0A06 = 0;
            YellowDeath(4);
        }
    }
    if (TERRAINset && MapA[fd_50F6_0F12 >> 4][fd_50F6_0F34 >> 4] > 0x90)
        fd_50F6_0F0C = 0;
}

int far ScanForAnts(void)
{
    int x;
    int y;
    int count;
    int i;
    int j;
    int tx;
    int ty;

    x = fd_50F6_0F12 >> 4;
    y = fd_50F6_0F34 >> 4;
    count = 0;
    for (i = -1; i < 3; i++)
        for (j = -1; j < 3; j++) {
            ty = y + j;
            tx = x + i;
            if (tx >= 0 && tx <= 127 && ty >= 0 && ty <= 63 && LifeA[tx][ty])
                count++;
        }
    return count;
}

void far KillSpider(void)
{
    SMode = 5;
    DeathCnt = 500;
    Scycle = 0;
}

extern int far ListIndexA;
extern int far IsYellowAnt(int value);
extern int far FindAntIndex(int plane, int x, int y, int life);
extern signed char far Dy8[8];
extern signed char far Dx8[8];

/* SCAFFOLD BEGIN: SFoundAnt best draft (383 vs 391 bytes).  The original computes SY (F34>>4)
 * first into DI and keeps the start-x copy and the walking y in memory ([bp-0Ah], [bp-0Ch],
 * frame 12); here both copies are propagated away (frame 8).  Loop/test shapes otherwise match. */
int far SFoundAnt(void)
{
    int sx;
    int sy;
    int x;
    int y;
    int i;
    int life;

    sy = fd_50F6_0F34 >> 4;
    x = fd_50F6_0F12 >> 4;
    sx = x;
    y = sy;
    if (fd_50F6_06AC == 7) {
        for (x = ListIndexA - 1; x >= 0; x--)
            if (AlistT[x] && GetDis(sx, sy, AlistX[x], AlistY[x]) <= 800)
                return x;
        if (fd_50F6_0A06 == 0 && MePlane == 1 && GetDis(sx, sy, MeLocX, MeLocY) <= 800)
            return -1;
        return -2;
    }
    for (i = 0; i < 20; i++) {
        y += Dy8[fd_50F6_1004];
        x += Dx8[fd_50F6_1004];
        if (!f_10F7_2867(x, y))
            return -2;
        if (GetDis(sx, sy, x, y) > 400)
            return -2;
        life = LifeA[x][y];
        if (life) {
            if (IsYellowAnt(life))
                return -1;
            if ((life = FindAntIndex(1, x, y, life)) >= 0)
                return life;
        }
    }
    return -2;
}
/* SCAFFOLD END */

extern int far fracCOS(int angle);
extern int far fracSIN(int angle);
extern void far DoLaserFire(int x1, int y1, int x2, int y2);

/* SCAFFOLD BEGIN: SpiderScan best draft (389 vs 392 bytes).  Only difference: the original keeps
 * the dead store r = 0 (sub ax,ax; mov [bp-2],ax; mov [bp-8],ax before the pass loop); every
 * spelling tried here (statement, chained, initialiser) is dead-store eliminated. */
int far SpiderScan(void)
{
    int dir = ((fd_50F6_1004 - 2) & 7) << 5;
    int sx = fd_50F6_0F12 >> 4;
    int sy = fd_50F6_0F34 >> 4;
    int found = -1;
    int r = 0;
    int pass;
    int a;
    int x;
    int y;
    int life;

    for (pass = 0; pass < 2; pass++) {
        for (a = dir - 32; a < dir + 32; a++) {
            r = SRand1(12) + 1;
            x = (int)(fracCOS(a) * (long)r / 32767L) + sx;
            y = (int)(fracSIN(a) * (long)r / 32767L) + sy;
            if (x >= 0 && x <= 127 && y >= 0 && y <= 63 && (life = LifeA[x][y]) != 0 &&
                (found = FindAntIndex(1, x, y, life)) >= 0) {
                DoLaserFire(fd_50F6_0F12, fd_50F6_0F34, (x << 4) + 7, (y << 4) + 7);
                if (SRand4()) {
                    LifeA[x][y] = 0;
                    AlistT[found] = 0;
                    DeadAntHere(x, y, life & 0x80);
                }
                return found;
            }
        }
    }
    return found;
}
/* SCAFFOLD END */

int far SGetDis(int x1, int y1, int x2, int y2)
{
    int dx = y2 - y1;
    int dy = x2 - x1;

    if (dy < 0)
        dy = -dy;
    if (dx < 0)
        dx = -dx;
    dx += dy;
    return dx;
}
