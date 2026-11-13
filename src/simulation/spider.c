/*
 * Initializes and advances the spider and scans for prey. It tracks targets, queen hunting and
 * spider death.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0CDB; complete original translation unit.
 * Windows: SIMONE, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 */

#include "audio_ids.h"
#include "pictures_ids.h"
#include "strings_ids.h"

extern int far SpidBurpCnt;
extern int far EatCnt;
extern int far SCorpseBase;
extern int far Scycle;
extern int far Scycle2;
extern int far SpidRevenge;
extern int far SpidDir;
extern int far RevSpider;
extern int far CurGameType;
extern int far SpidOn;
extern int far SpidX;
extern int far SpidY;
extern int far SMode;
extern int far MeSMode;
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
    SpidDir = 0;
    RevSpider = 0;
    if (CurGameType)
        SpidOn = 1;
    else
        SpidOn = 0;
    SpidX = 0x400;
    SpidY = 0x200;
    MeSMode = SMode = 0;
    Starg = -2;
    StargLife = -1;
    SuserY = SuserX = 64;
}

extern int far MeMode;
int far SFoundAnt(void);
extern unsigned char far AlistT[];
int far SpiderScan(void);
extern int far MeLocY;
extern int far MeLocX;
extern unsigned long far GetDis(int x1, int y1, int x2, int y2);
extern int far GetBestDir(int plane, int x, int y, int gx, int gy);
extern int far GetDir(int x1, int y1, int x2, int y2);
extern signed char far TurnTab[][8];
extern int far MeCmd;
extern signed char far SpX[];
extern signed char far SpY[];
extern int far OptionStates[];
extern void far GotoMyAnt(void);
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
extern void far DropFoodA(int x, int y);
extern long far RAntsEaten;
extern long far BAntsEaten;
extern unsigned char far LifeA[128][64];
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern int far MeType;
extern int far MeDir;
extern signed char far SeatY[];
extern signed char far SeatX[];
extern int far TERRAINset;
extern unsigned char far MapA[128][64];
extern int far SRand4(void);
extern int far SRand256(void);
extern void far DeadAntHere(int x, int y, int type);
extern int far IsValidA(int x, int y);

void far MoveSpider(void)
{
    int x;
    int y;
    int d;
    int r;

    Scycle2 = (Scycle2 + 1) & 0x3ff;
    x = SpidX >> 4;
    y = SpidY >> 4;
    if (MeMode == 1 && SMode != 2 && SMode != 3) {
        if (MeSMode == 7) {
            Starg = SFoundAnt();
            if (Starg != -2) {
                SMode = 2;
                if (Starg >= 0)
                    StargLife = AlistT[Starg];
                else
                    StargLife = 0xff;
                return;
            }
        } else if (MeSMode == 8)
            SpiderScan();
        d = (int)GetDis(MeLocX, MeLocY, SuserX, SuserY);
        if (d < 1) {
            Scycle = 2;
            return;
        }
        r = GetBestDir(1, MeLocX, MeLocY, SuserX, SuserY);
        if (r == -1)
            return;
        if (r == -2) {
            r = GetDir(MeLocX, MeLocY, SuserX, SuserY) - 1;
            if (r < 0)
                return;
        }
        SpidDir = TurnTab[SpidDir][r];
        if (MeCmd && d > 2) {
            SpidX += 5 * SpX[SpidDir];
            SpidY += 5 * SpY[SpidDir];
            Scycle = (Scycle + 2) & 0x3ff;
        } else {
            SpidX += SpX[SpidDir];
            SpidY += SpY[SpidDir];
            Scycle = (Scycle + 1) & 0x3ff;
        }
        MeLocX = SpidX >> 4;
        MeLocY = SpidY >> 4;
        if (OptionStates[0])
            GotoMyAnt();
        return;
    }
    if (!SpidOn) {
        if (!CurGameType)
            return;
        if (SRand1(300))
            return;
        SpidX = SRand1(0x400) + 0x200;
        SMode = SpidOn = 1;
        RevSpider = 0;
        if (SRand1(2)) {
            SpidY = 1;
            SpidDir = 4;
        } else {
            SpidY = 0x3ff;
            SpidDir = 0;
        }
        return;
    }
    if (!(Scycle2 & 3) && SMode < 5) {
        r = ScanForAnts();
        if (r > 8) {
            KillSpider();
            if (MeMode != 1) {
                PictStrnDialog(PIC_NONE, STR_SPIDER_KILLED, 0);
                if (SpidRevenge < 5)
                    SpidRevenge++;
                if (SpidRevenge < 3)
                    return;
                if (SpidRevenge >= 5)
                    MeSMode = 8;
                else
                    MeSMode = 7;
                if (SpidRevenge >= 6 && !SRand2()) {
                    SpidRevenge = 0;
                    MeSMode = 0;
                }
                return;
            }
            MeMode = 0;
            YellowDeath(3);
            return;
        }
        if (r > 4)
            SMode = 4;
    }
    if (SMode < 4 && MeSMode == 8)
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
            SpidDir = TurnTab[SpidDir][SRand1(8)];
        if (MeSMode == 8)
            SpiderScan();
        break;
    case 1:
        if (RevSpider) {
            SpidX -= SpX[SpidDir];
            SpidY -= SpY[SpidDir];
            Scycle = (Scycle - 1) & 0x3ff;
        } else {
            SpidX += SpX[SpidDir];
            SpidY += SpY[SpidDir];
            Scycle = (Scycle + 1) & 0x3ff;
        }
        if (!SRand1(20))
            SpidDir = TurnTab[SpidDir][SRand1(8)];
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
                if (MeMode != 1)
                    return;
                y = SpidY >> 4;
                x = SpidX >> 4;
                SuserY = y;
                SuserX = x;
                MeLocX = x;
                MeLocY = y;
                if (MeSMode == 6)
                    MeSMode = 0;
                if (OptionStates[0])
                    GotoMyAnt();
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
        if (d > 64 && MeMode != 1) {
            SMode = 0;
            Starg = -2;
            return;
        }
        if (d < 2) {
            SMode = 3;
            SpidX = (SpidX & 0xfff0) + 8;
            SpidY = (SpidY & 0xfff0) + 8;
            goto eat;
        }
        if (Starg < 0)
            d = GetDir(x, y, MeLocX, MeLocY);
        else
            d = GetDir(x, y, AlistX[Starg], AlistY[Starg]);
        SpidDir = TurnTab[SpidDir][d - 1];
        if (Starg < 0)
            myBeginSound(SND_SPIDER_MOVE, 0, 0x7e);
        else
            myBeginSound(SND_SPIDER_MOVE, 0, -5);
        if (RevSpider) {
            SpidX -= 5 * SpX[SpidDir];
            SpidY -= 5 * SpY[SpidDir];
            Scycle = (Scycle - 2) & 0x3ff;
        } else {
            SpidX += 5 * SpX[SpidDir];
            SpidY += 5 * SpY[SpidDir];
            Scycle = (Scycle + 2) & 0x3ff;
        }
        if (MeMode == 1) {
            MeLocX = SpidX >> 4;
            MeLocY = SpidY >> 4;
            if (OptionStates[0])
                GotoMyAnt();
        }
        break;
    case 3:
    eat:
        if (MeMode == 1) {
            MeLocX = SpidX >> 4;
            MeLocY = SpidY >> 4;
            if (MeSMode == 6)
                MeSMode = 0;
            if (OptionStates[0])
                GotoMyAnt();
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
                MoveMyLife(MePlane, (SeatX[SpidDir] + x) & 0x7f,
                           (SeatY[SpidDir] + y) & 0x3f, MeType, MeDir);
                YellowDeath(1);
                SCorpseBase = 0;
            }
            Starg = -2;
            EatCnt = MeSMode >= 7 ? 11 : 50;
        }
        d = (SeatX[SpidDir] + x) & 0x7f;
        r = (SeatY[SpidDir] + y) & 0x3f;
        if (!TERRAINset && MapA[d][r] < 0x18)
            MapA[d][r] = SRand4() + SCorpseBase + 0x10;
        if (EatCnt > 0) {
            EatCnt--;
            if (EatCnt % 10 == 0 && SRand2())
                myBeginSound(SND_EAT, (SRand256() << 3) + 0x2777, -5);
            break;
        }
        if (--SpidBurpCnt == 0) {
            SpidBurpCnt = 10;
            if (OptionStates[5] && !SRand2())
                myBeginSound(SND_FOOD_OR_WALL_ACTION, 0, 10);
        }
        DeadAntHere(d, r, SCorpseBase);
    done:
        SMode = 0;
        if (MeMode == 1) {
            if (MeSMode == 6)
                MeSMode = 0;
            SuserX = x;
            SuserY = y;
        }
        break;
    case 4:
        SpidDir = TurnTab[SpidDir][SRand1(8)];
        if (RevSpider) {
            SpidX -= 5 * SpX[SpidDir];
            SpidY -= 5 * SpY[SpidDir];
            Scycle = (Scycle - 2) & 0x3ff;
        } else {
            SpidX += 5 * SpX[SpidDir];
            SpidY += 5 * SpY[SpidDir];
            Scycle = (Scycle + 2) & 0x3ff;
        }
        if (!SRand1(50)) {
            SMode = 0;
            Scycle = 2;
        }
        break;
    case 5:
        if (--DeathCnt == 0) {
            SMode = SpidOn = 0;
            DropFoodA(x, y);
            DropFoodA(x, y);
            DropFoodA(x, y);
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
    if (!IsValidA(SpidX >> 4, SpidY >> 4)) {
        SpidOn = 0;
        if (MeMode == 1) {
            MeMode = 0;
            YellowDeath(4);
        }
    }
    if (TERRAINset && MapA[SpidX >> 4][SpidY >> 4] > 0x90)
        SpidOn = 0;
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

    x = SpidX >> 4;
    y = SpidY >> 4;
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

/* SFoundAnt: the scan loop of the queen-hunt mode reuses i; the walk result goes through n
 * (eliminated, REG-2) so life keeps its own slot. */
int far SFoundAnt(void)
{
    int sx;
    int sy;
    int x;
    int y;
    int i;
    int life;
    int n;

    sx = SpidX >> 4;
    sy = SpidY >> 4;
    x = sx;
    y = sy;
    if (MeSMode == 7) {
        for (i = ListIndexA - 1; i >= 0; i--)
            if (AlistT[i] && GetDis(sx, sy, AlistX[i], AlistY[i]) <= 800)
                return i;
        if (MeMode == 0 && MePlane == 1 && GetDis(sx, sy, MeLocX, MeLocY) <= 800)
            return -1;
        return -2;
    }
    for (i = 0; i < 20; i++) {
        y += Dy8[SpidDir];
        x += Dx8[SpidDir];
        if (!IsValidA(x, y))
            return -2;
        if (GetDis(sx, sy, x, y) > 400)
            return -2;
        life = LifeA[x][y];
        if (life) {
            if (IsYellowAnt(life))
                return -1;
            if ((n = FindAntIndex(1, x, y, life)) >= 0)
                return n;
        }
    }
    return -2;
}

extern int far fracCOS(int angle);
extern int far fracSIN(int angle);
extern void far DoLaserFire(int x1, int y1, int x2, int y2);


/* Mac C12:1B6A retains an independent kill counter, cleared at 1B94 and
 * incremented at 1C9C after DeadAntHere. Its original local name is unknown.
 * Radius has no entry initialization in that witness. */
int far SpiderScan(void)
{
    int dir = ((SpidDir - 2) & 7) << 5;
    int sx = SpidX >> 4;
    int sy = SpidY >> 4;
    int found = -1;
    int r;
    int killed = 0; /* Mac witness: independent kill count; local name is a hypothesis. */
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
                DoLaserFire(SpidX, SpidY, (x << 4) + 7, (y << 4) + 7);
                if (SRand4()) {
                    LifeA[x][y] = 0;
                    AlistT[found] = 0;
                    DeadAntHere(x, y, life & 0x80);
                    killed++;
                }
                return found;
            }
        }
    }
    return found;
}


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
