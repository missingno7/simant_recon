/*
 * Handles cheat key commands. The handler changes game state and reports the selected cheat
 * number.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 7 (S07); segment 35F5; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 */

#include "audio_ids.h"
#include "strings_ids.h"

extern int far cheat_key_count;
extern char far cheat_key_prefix[];
extern char far cheat_code_table[][4];
extern int far QueenStorageR;
extern int far MeLocY;
extern int far MeLocX;
extern char far Dy8[];
extern char far Dx8[];
extern int far HealthB;
extern int far HealthR;
extern int far AlwaysHealthy;
extern int far QueenStorageB;
extern int far Invincible;
extern int far RevSpider;
extern unsigned char far YMapPopB[12][16];
extern int far BColoniesStarted;
extern unsigned char far YMapPopR[12][16];
extern int far RColoniesStarted;
extern int far NeverHungry;
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

    cheat_key_prefix[cheat_key_count] = ~key;
    cheat_key_count++;
    for (i = 0; cheat_code_table[i][0] != 0; i++) {
        p = cheat_code_table[i];
        for (j = 0; j < cheat_key_count; j++)
            if (p[j] != cheat_key_prefix[j])
                break;
        if (j == cheat_key_count)
            break;
    }
    if (cheat_code_table[i][0] == 0) {
        for (k = cheat_key_count = 0; k < 4; k++)
            cheat_key_prefix[k] = 0;
        return;
    }
    if (cheat_key_count < 4)
        return;
    for (k = cheat_key_count = 0; k < 4; k++)
        cheat_key_prefix[k] = 0;
    WinPrintf("CHEAT %d", i);
    switch (i) {
    case 0:
        myBeginSound(SND_FOOD_OR_WALL_ACTION, 0, 0x7e);
        QueenStorageR += 10;
        break;
    case 1:
        myBeginSound(SND_REJECT, 0, 0x7e);
        SetMyHealth(100);
        break;
    case 2:
        myBeginSound(SND_REJECT, 0, 0x7e);
        SetMyHealth(1);
        break;
    case 3:
        o14_384C_0B6A(0, STR_MONEY_IS_WORTHLESS, 0);
        break;
    case 4:
        o14_384C_0B6A(0, STR_GLEN_CAMPBELL_RIDDLE, 0);
        UpdateEverything();
        SetSimCursor(6);
        f_00DF_00E0(0);
        SetSimCursor(0);
        o14_384C_0B6A(0, STR_ELVIS_MINUS_TWO, 0);
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
        AlwaysHealthy = 0;
        HealthB = 0;
        break;
    case 15:
        QueenStorageB += 10;
        InvalQueenStorageDisp();
        myBeginSound(SND_RAIN, 0, 0x7e);
        break;
    case 16:
        Invincible = !Invincible;
        if (Invincible)
            myBeginSound(SND_ACCEPT, 0, 0x7e);
        else
            myBeginSound(SND_REJECT, 0, 0x7e);
        break;
    case 17:
        RevSpider = !RevSpider;
        if (RevSpider)
            myBeginSound(SND_ACCEPT, 0, 0x7e);
        else
            myBeginSound(SND_REJECT, 0, 0x7e);
        break;
    case 18:
        myBeginSound(SND_ACCEPT, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                YMapPopB[i][j] += 4;
                BColoniesStarted++;
            }
        break;
    case 19:
        myBeginSound(SND_REJECT, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                if (SRand2() == 0) {
                    YMapPopB[i][j]++;
                    BColoniesStarted++;
                } else {
                    YMapPopR[i][j]++;
                    RColoniesStarted++;
                }
            }
        break;
    case 20:
        DrawSimPayoff();
        break;
    case 21:
        NeverHungry = !NeverHungry;
        if (NeverHungry) {
            MeHealth = 100;
            myBeginSound(SND_ACCEPT, 0, 0x7e);
        } else
            myBeginSound(SND_REJECT, 0, 0x7e);
        break;
    case 22:
        AlwaysHealthy = !AlwaysHealthy;
        if (AlwaysHealthy) {
            HealthB = 100;
            myBeginSound(SND_ACCEPT, 0, 0x7e);
        } else
            myBeginSound(SND_REJECT, 0, 0x7e);
        break;
    }
}
