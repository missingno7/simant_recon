#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module 0CDB: the spider (InitSpider .. SGetDis, Win16 SIMONE_MODULE order). */

extern int16_t  fd_3D57_0C12;
extern int16_t  fd_50F6_0EAC;

void  InitSpider(void)
{
    native_state_SpidBurpCnt.signed_value = 10;
    native_state_EatCnt.signed_value = 0;
    native_state_SCorpseBase.signed_value = 0;
    native_state_Scycle.signed_value = 0;
    native_state_Scycle2.signed_value = 0;
    native_state_SpidRevenge.signed_value = 0;
    native_state_fd_50F6_1004.signed_value = 0;
    fd_3D57_0C12 = 0;
    if (fd_50F6_0EAC)
        native_state_fd_50F6_0F0C.signed_value = 1;
    else
        native_state_fd_50F6_0F0C.signed_value = 0;
    native_state_fd_50F6_0F12.signed_value = 0x400;
    native_state_fd_50F6_0F34.signed_value = 0x200;
    native_state_fd_50F6_06AC.signed_value = native_state_SMode.signed_value = 0;
    native_state_Starg.signed_value = -2;
    native_state_StargLife.signed_value = -1;
    native_state_SuserY.signed_value = native_state_SuserX.signed_value = 64;
}

extern int16_t  fd_50F6_0A06;
int16_t  SFoundAnt(void);
extern uint8_t  AlistT[];
int16_t  SpiderScan(void);
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern uint32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  o25_39C7_0CBD(int16_t plane, int16_t x, int16_t y, int16_t gx, int16_t gy);
extern int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int8_t  TurnTab[][8];
extern int8_t  fd_3D57_0994[];
extern int8_t  fd_3D57_099C[];
extern int16_t  fd_3D57_07A8[];
extern void  GotoMyAnt(void);
extern int16_t  SRand1(int16_t range);
int16_t  ScanForAnts(void);
void  KillSpider(void);
extern void  YellowDeath(int16_t cause);
extern void  PictStrnDialog(int16_t pict, int16_t strn, int16_t flag);
extern int16_t  SRand2(void);
extern int16_t  MePlane;
extern uint8_t  AlistY[];
extern uint8_t  AlistX[];
int16_t  SGetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  DropFoodA(int16_t x, int16_t y);
extern uint8_t  LifeA[128][64];
extern void  MoveMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern int16_t  fd_50F6_04C2;
extern int16_t  fd_50F6_0496;
extern int8_t  fd_3D57_09AC[];
extern int8_t  fd_3D57_09A4[];
extern int16_t  TERRAINset;
extern uint8_t  MapA[128][64];
extern int16_t  SRand4(void);
extern int16_t  SRand256(void);
extern void  DeadAntHere(int16_t x, int16_t y, int16_t type);
extern int16_t  IsValidA(int16_t x, int16_t y);

void  MoveSpider(void)
{
    int16_t x;
    int16_t y;
    int16_t d;
    int16_t r;

    native_state_Scycle2.signed_value = (native_state_Scycle2.signed_value + 1) & 0x3ff;
    x = native_state_fd_50F6_0F12.signed_value >> 4;
    y = native_state_fd_50F6_0F34.signed_value >> 4;
    if (fd_50F6_0A06 == 1 && native_state_SMode.signed_value != 2 && native_state_SMode.signed_value != 3) {
        if (native_state_fd_50F6_06AC.signed_value == 7) {
            native_state_Starg.signed_value = SFoundAnt();
            if (native_state_Starg.signed_value != -2) {
                native_state_SMode.signed_value = 2;
                if (native_state_Starg.signed_value >= 0)
                    native_state_StargLife.signed_value = AlistT[native_state_Starg.signed_value];
                else
                    native_state_StargLife.signed_value = 0xff;
                return;
            }
        } else if (native_state_fd_50F6_06AC.signed_value == 8)
            SpiderScan();
        d = (int16_t)GetDis(MeLocX, MeLocY, native_state_SuserX.signed_value, native_state_SuserY.signed_value);
        if (d < 1) {
            native_state_Scycle.signed_value = 2;
            return;
        }
        r = o25_39C7_0CBD(1, MeLocX, MeLocY, native_state_SuserX.signed_value, native_state_SuserY.signed_value);
        if (r == -1)
            return;
        if (r == -2) {
            r = GetDir(MeLocX, MeLocY, native_state_SuserX.signed_value, native_state_SuserY.signed_value) - 1;
            if (r < 0)
                return;
        }
        native_state_fd_50F6_1004.signed_value = TurnTab[native_state_fd_50F6_1004.signed_value][r];
        if (native_state_fd_50F6_0A8E.signed_value && d > 2) {
            native_state_fd_50F6_0F12.signed_value += 5 * fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value += 5 * fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value + 2) & 0x3ff;
        } else {
            native_state_fd_50F6_0F12.signed_value += fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value += fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value + 1) & 0x3ff;
        }
        MeLocX = native_state_fd_50F6_0F12.signed_value >> 4;
        MeLocY = native_state_fd_50F6_0F34.signed_value >> 4;
        if (fd_3D57_07A8[0])
            GotoMyAnt();
        return;
    }
    if (!native_state_fd_50F6_0F0C.signed_value) {
        if (!fd_50F6_0EAC)
            return;
        if (SRand1(300))
            return;
        native_state_fd_50F6_0F12.signed_value = SRand1(0x400) + 0x200;
        native_state_SMode.signed_value = native_state_fd_50F6_0F0C.signed_value = 1;
        fd_3D57_0C12 = 0;
        if (SRand1(2)) {
            native_state_fd_50F6_0F34.signed_value = 1;
            native_state_fd_50F6_1004.signed_value = 4;
        } else {
            native_state_fd_50F6_0F34.signed_value = 0x3ff;
            native_state_fd_50F6_1004.signed_value = 0;
        }
        return;
    }
    if (!(native_state_Scycle2.signed_value & 3) && native_state_SMode.signed_value < 5) {
        r = ScanForAnts();
        if (r > 8) {
            KillSpider();
            if (fd_50F6_0A06 != 1) {
                PictStrnDialog(0, 0x273e, 0);
                if (native_state_SpidRevenge.signed_value < 5)
                    native_state_SpidRevenge.signed_value++;
                if (native_state_SpidRevenge.signed_value < 3)
                    return;
                if (native_state_SpidRevenge.signed_value >= 5)
                    native_state_fd_50F6_06AC.signed_value = 8;
                else
                    native_state_fd_50F6_06AC.signed_value = 7;
                if (native_state_SpidRevenge.signed_value >= 6 && !SRand2()) {
                    native_state_SpidRevenge.signed_value = 0;
                    native_state_fd_50F6_06AC.signed_value = 0;
                }
                return;
            }
            fd_50F6_0A06 = 0;
            YellowDeath(3);
            return;
        }
        if (r > 4)
            native_state_SMode.signed_value = 4;
    }
    if (native_state_SMode.signed_value < 4 && native_state_fd_50F6_06AC.signed_value == 8)
        SpiderScan();
    switch (native_state_SMode.signed_value) {
    case 0:
        native_state_Scycle.signed_value = 2;
        if (!SRand1(150))
            native_state_SMode.signed_value = 1;
        if ((native_state_Starg.signed_value = SFoundAnt()) != -2) {
            native_state_SMode.signed_value = 2;
            if (native_state_Starg.signed_value >= 0)
                native_state_StargLife.signed_value = AlistT[native_state_Starg.signed_value];
            else
                native_state_StargLife.signed_value = 0xff;
            return;
        }
        if (!SRand1(30))
            native_state_fd_50F6_1004.signed_value = TurnTab[native_state_fd_50F6_1004.signed_value][SRand1(8)];
        if (native_state_fd_50F6_06AC.signed_value == 8)
            SpiderScan();
        break;
    case 1:
        if (fd_3D57_0C12) {
            native_state_fd_50F6_0F12.signed_value -= fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value -= fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value - 1) & 0x3ff;
        } else {
            native_state_fd_50F6_0F12.signed_value += fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value += fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value + 1) & 0x3ff;
        }
        if (!SRand1(20))
            native_state_fd_50F6_1004.signed_value = TurnTab[native_state_fd_50F6_1004.signed_value][SRand1(8)];
        if ((native_state_Starg.signed_value = SFoundAnt()) != -2) {
            native_state_SMode.signed_value = 2;
            if (native_state_Starg.signed_value >= 0)
                native_state_StargLife.signed_value = AlistT[native_state_Starg.signed_value];
            else
                native_state_StargLife.signed_value = 0xff;
            return;
        }
        if (!SRand1(50)) {
            native_state_SMode.signed_value = 0;
            native_state_Scycle.signed_value = 2;
        }
        break;
    case 2:
        if (native_state_Starg.signed_value >= 0) {
            if ((AlistT[native_state_Starg.signed_value] ^ native_state_StargLife.signed_value) & 0xf0) {
                native_state_SMode.signed_value = 0;
                native_state_Starg.signed_value = -2;
                if (fd_50F6_0A06 != 1)
                    return;
                y = native_state_fd_50F6_0F34.signed_value >> 4;
                x = native_state_fd_50F6_0F12.signed_value >> 4;
                native_state_SuserY.signed_value = y;
                native_state_SuserX.signed_value = x;
                MeLocX = x;
                MeLocY = y;
                if (native_state_fd_50F6_06AC.signed_value == 6)
                    native_state_fd_50F6_06AC.signed_value = 0;
                if (fd_3D57_07A8[0])
                    GotoMyAnt();
                return;
            }
        } else if (MePlane > 1) {
            native_state_SMode.signed_value = 0;
            native_state_Starg.signed_value = -2;
            return;
        }
        if (native_state_Starg.signed_value < 0)
            d = SGetDis(x, y, MeLocX, MeLocY);
        else
            d = SGetDis(x, y, AlistX[native_state_Starg.signed_value], AlistY[native_state_Starg.signed_value]);
        if (d > 64 && fd_50F6_0A06 != 1) {
            native_state_SMode.signed_value = 0;
            native_state_Starg.signed_value = -2;
            return;
        }
        if (d < 2) {
            native_state_SMode.signed_value = 3;
            native_state_fd_50F6_0F12.signed_value = (native_state_fd_50F6_0F12.signed_value & 0xfff0) + 8;
            native_state_fd_50F6_0F34.signed_value = (native_state_fd_50F6_0F34.signed_value & 0xfff0) + 8;
            goto eat;
        }
        if (native_state_Starg.signed_value < 0)
            d = GetDir(x, y, MeLocX, MeLocY);
        else
            d = GetDir(x, y, AlistX[native_state_Starg.signed_value], AlistY[native_state_Starg.signed_value]);
        native_state_fd_50F6_1004.signed_value = TurnTab[native_state_fd_50F6_1004.signed_value][d - 1];
        if (native_state_Starg.signed_value < 0)
            myBeginSound(0x2f, 0, 0x7e);
        else
            myBeginSound(0x2f, 0, -5);
        if (fd_3D57_0C12) {
            native_state_fd_50F6_0F12.signed_value -= 5 * fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value -= 5 * fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value - 2) & 0x3ff;
        } else {
            native_state_fd_50F6_0F12.signed_value += 5 * fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value += 5 * fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value + 2) & 0x3ff;
        }
        if (fd_50F6_0A06 == 1) {
            MeLocX = native_state_fd_50F6_0F12.signed_value >> 4;
            MeLocY = native_state_fd_50F6_0F34.signed_value >> 4;
            if (fd_3D57_07A8[0])
                GotoMyAnt();
        }
        break;
    case 3:
    eat:
        if (fd_50F6_0A06 == 1) {
            MeLocX = native_state_fd_50F6_0F12.signed_value >> 4;
            MeLocY = native_state_fd_50F6_0F34.signed_value >> 4;
            if (native_state_fd_50F6_06AC.signed_value == 6)
                native_state_fd_50F6_06AC.signed_value = 0;
            if (fd_3D57_07A8[0])
                GotoMyAnt();
        }
        if (native_state_Starg.signed_value != -2) {
            if (native_state_Starg.signed_value >= 0) {
                if (!(((uint8_t)native_state_StargLife.signed_value ^ AlistT[native_state_Starg.signed_value]) & 0xf0)) {
                    if (native_state_StargLife.signed_value & 0x80) {
                        native_state_RAntsEaten.signed_value++;
                        native_state_SCorpseBase.signed_value = 4;
                    } else {
                        native_state_BAntsEaten.signed_value++;
                        native_state_SCorpseBase.signed_value = 0;
                    }
                    LifeA[AlistX[native_state_Starg.signed_value]][AlistY[native_state_Starg.signed_value]] = 0;
                    AlistT[native_state_Starg.signed_value] = 0;
                } else {
                    native_state_Starg.signed_value = -2;
                    goto done;
                }
            } else {
                MoveMyLife(MePlane, (fd_3D57_09A4[native_state_fd_50F6_1004.signed_value] + x) & 0x7f,
                           (fd_3D57_09AC[native_state_fd_50F6_1004.signed_value] + y) & 0x3f, fd_50F6_04C2, fd_50F6_0496);
                YellowDeath(1);
                native_state_SCorpseBase.signed_value = 0;
            }
            native_state_Starg.signed_value = -2;
            native_state_EatCnt.signed_value = native_state_fd_50F6_06AC.signed_value >= 7 ? 11 : 50;
        }
        d = (fd_3D57_09A4[native_state_fd_50F6_1004.signed_value] + x) & 0x7f;
        r = (fd_3D57_09AC[native_state_fd_50F6_1004.signed_value] + y) & 0x3f;
        if (!TERRAINset && MapA[d][r] < 0x18)
            MapA[d][r] = SRand4() + native_state_SCorpseBase.signed_value + 0x10;
        if (native_state_EatCnt.signed_value > 0) {
            native_state_EatCnt.signed_value--;
            if (native_state_EatCnt.signed_value % 10 == 0 && SRand2())
                myBeginSound(0x2c, (SRand256() << 3) + 0x2777, -5);
            break;
        }
        if (--native_state_SpidBurpCnt.signed_value == 0) {
            native_state_SpidBurpCnt.signed_value = 10;
            if (fd_3D57_07A8[5] && !SRand2())
                myBeginSound(10, 0, 10);
        }
        DeadAntHere(d, r, native_state_SCorpseBase.signed_value);
    done:
        native_state_SMode.signed_value = 0;
        if (fd_50F6_0A06 == 1) {
            if (native_state_fd_50F6_06AC.signed_value == 6)
                native_state_fd_50F6_06AC.signed_value = 0;
            native_state_SuserX.signed_value = x;
            native_state_SuserY.signed_value = y;
        }
        break;
    case 4:
        native_state_fd_50F6_1004.signed_value = TurnTab[native_state_fd_50F6_1004.signed_value][SRand1(8)];
        if (fd_3D57_0C12) {
            native_state_fd_50F6_0F12.signed_value -= 5 * fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value -= 5 * fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value - 2) & 0x3ff;
        } else {
            native_state_fd_50F6_0F12.signed_value += 5 * fd_3D57_0994[native_state_fd_50F6_1004.signed_value];
            native_state_fd_50F6_0F34.signed_value += 5 * fd_3D57_099C[native_state_fd_50F6_1004.signed_value];
            native_state_Scycle.signed_value = (native_state_Scycle.signed_value + 2) & 0x3ff;
        }
        if (!SRand1(50)) {
            native_state_SMode.signed_value = 0;
            native_state_Scycle.signed_value = 2;
        }
        break;
    case 5:
        if (--native_state_DeathCnt.signed_value == 0) {
            native_state_SMode.signed_value = native_state_fd_50F6_0F0C.signed_value = 0;
            DropFoodA(x, y);
            DropFoodA(x, y);
            DropFoodA(x, y);
            return;
        }
        if (SRand1(1000) < native_state_DeathCnt.signed_value) {
            if (native_state_DeathCnt.signed_value > 400)
                native_state_Scycle.signed_value = SRand1(3) + 1;
            else
                native_state_Scycle.signed_value = SRand1(2) + 2;
        }
        break;
    }
    if (!IsValidA(native_state_fd_50F6_0F12.signed_value >> 4, native_state_fd_50F6_0F34.signed_value >> 4)) {
        native_state_fd_50F6_0F0C.signed_value = 0;
        if (fd_50F6_0A06 == 1) {
            fd_50F6_0A06 = 0;
            YellowDeath(4);
        }
    }
    if (TERRAINset && MapA[native_state_fd_50F6_0F12.signed_value >> 4][native_state_fd_50F6_0F34.signed_value >> 4] > 0x90)
        native_state_fd_50F6_0F0C.signed_value = 0;
}

int16_t  ScanForAnts(void)
{
    int16_t x;
    int16_t y;
    int16_t count;
    int16_t i;
    int16_t j;
    int16_t tx;
    int16_t ty;

    x = native_state_fd_50F6_0F12.signed_value >> 4;
    y = native_state_fd_50F6_0F34.signed_value >> 4;
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

void  KillSpider(void)
{
    native_state_SMode.signed_value = 5;
    native_state_DeathCnt.signed_value = 500;
    native_state_Scycle.signed_value = 0;
}

extern int16_t  ListIndexA;
extern int16_t  IsYellowAnt(int16_t value);
extern int16_t  FindAntIndex(int16_t plane, int16_t x, int16_t y, int16_t life);
extern int8_t  Dy8[8];
extern int8_t  Dx8[8];

/* SFoundAnt: the scan loop of the queen-hunt mode reuses i; the walk result goes through n
 * (eliminated, REG-2) so life keeps its own slot. */
int16_t  SFoundAnt(void)
{
    int16_t sx;
    int16_t sy;
    int16_t x;
    int16_t y;
    int16_t i;
    int16_t life;
    int16_t n;

    sx = native_state_fd_50F6_0F12.signed_value >> 4;
    sy = native_state_fd_50F6_0F34.signed_value >> 4;
    x = sx;
    y = sy;
    if (native_state_fd_50F6_06AC.signed_value == 7) {
        for (i = ListIndexA - 1; i >= 0; i--)
            if (AlistT[i] && GetDis(sx, sy, AlistX[i], AlistY[i]) <= 800)
                return i;
        if (fd_50F6_0A06 == 0 && MePlane == 1 && GetDis(sx, sy, MeLocX, MeLocY) <= 800)
            return -1;
        return -2;
    }
    for (i = 0; i < 20; i++) {
        y += Dy8[native_state_fd_50F6_1004.signed_value];
        x += Dx8[native_state_fd_50F6_1004.signed_value];
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

extern int16_t  fracCOS(int16_t angle);
extern int16_t  fracSIN(int16_t angle);
extern void  DoLaserFire(int16_t x1, int16_t y1, int16_t x2, int16_t y2);

/* SCAFFOLD BEGIN: SpiderScan best draft (389 vs 392 bytes).  Only difference: the original keeps
 * the dead store r = 0 (sub ax,ax; mov [bp-2],ax; mov [bp-8],ax before the pass loop); every
 * spelling tried here (statement, chained, initialiser) is dead-store eliminated. */
int16_t  SpiderScan(void)
{
    int16_t dir = ((native_state_fd_50F6_1004.signed_value - 2) & 7) << 5;
    int16_t sx = native_state_fd_50F6_0F12.signed_value >> 4;
    int16_t sy = native_state_fd_50F6_0F34.signed_value >> 4;
    int16_t found = -1;
    int16_t r = 0;
    int16_t pass;
    int16_t a;
    int16_t x;
    int16_t y;
    int16_t life;

    for (pass = 0; pass < 2; pass++) {
        for (a = dir - 32; a < dir + 32; a++) {
            r = SRand1(12) + 1;
            x = (int16_t)(fracCOS(a) * (int32_t)r / 32767L) + sx;
            y = (int16_t)(fracSIN(a) * (int32_t)r / 32767L) + sy;
            if (x >= 0 && x <= 127 && y >= 0 && y <= 63 && (life = LifeA[x][y]) != 0 &&
                (found = FindAntIndex(1, x, y, life)) >= 0) {
                DoLaserFire(native_state_fd_50F6_0F12.signed_value, native_state_fd_50F6_0F34.signed_value, (x << 4) + 7, (y << 4) + 7);
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

int16_t  SGetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    int16_t dx = y2 - y1;
    int16_t dy = x2 - x1;

    if (dy < 0)
        dy = -dy;
    if (dx < 0)
        dx = -dx;
    dx += dy;
    return dx;
}

#pragma pack(pop)
