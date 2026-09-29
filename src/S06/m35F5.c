/* Overlay section S06, code frame 35F5: back-yard simulation (SimYard unit). */

extern long far fd_50F6_109C;
extern int far fd_3D57_0C2C;
extern int far fd_3D57_0C2E;
extern int far fd_3D57_0C34;
extern int far fd_3D57_0C2A;
extern long far fd_50F6_107E;
extern long far fd_50F6_0220;
extern int far fd_50F6_04BE;
extern int far fd_50F6_04C6;
extern int far fd_3D57_0C30;
extern int far fd_50F6_0624;
extern int far fd_50F6_10B0;
extern int far fd_50F6_0246;
extern int far fd_50F6_023E;
extern int far fd_3D57_0C32;
extern int far fd_3D57_0C28;
extern int far fd_3D57_0C40;
extern int far fd_3D57_0C46;
extern int far fd_3D57_0C48;
extern int far fd_50F6_10A0;
extern int far fd_50F6_022C;
extern int far fd_50F6_0244;
extern int far fd_50F6_0254;
extern int far fd_50F6_04E4;
extern int far fd_50F6_0506;
extern int far fd_3D57_0C3E;
extern int far fd_3D57_0C42;
extern int far fd_50F6_03E0;
extern int far fd_50F6_046A;
extern int far fd_50F6_0470;
extern int far fd_50F6_047A;
extern int far fd_50F6_0202;
extern int far fd_50F6_0352;
extern int far fd_50F6_105C;
extern int far fd_50F6_1066;
extern int far fd_50F6_108C;
extern int far fd_50F6_0364;
extern int far fd_50F6_036E;
extern int far fd_50F6_10BC;
extern int far fd_50F6_07C2;

/* InitSimYard */
void far o06_35F5_0000(void)
{
    fd_50F6_109C = 0L;          /* BoyMsgCnt */
    fd_3D57_0C2C = 0xb4;        /* BoyX */
    fd_3D57_0C2E = 0x49;        /* BoyY */
    fd_3D57_0C34 = 0xc;         /* BoyTurnCnt */
    fd_3D57_0C2A = 0x14;        /* BoyWait */
    fd_50F6_107E = 0L;          /* BirdDelay */
    fd_50F6_0220 = 0L;          /* CatDelay */
    fd_50F6_04BE = 0xfa;        /* DogX */
    fd_50F6_04C6 = 0x96;        /* DogY */
    fd_3D57_0C30 = 2;           /* BoyDir */
    fd_50F6_0624 = 2;           /* DogTurnCnt */
    fd_50F6_10B0 = 0;           /* BoyMessOn */
    fd_50F6_0246 = 0;           /* BoyPx */
    fd_50F6_023E = 0;           /* BoyPy */
    fd_3D57_0C32 = 0;           /* BoyFrame */
    fd_3D57_0C28 = 0;           /* BoyHere */
    fd_3D57_0C40 = 0;           /* BoyStandCnt */
    fd_3D57_0C46 = 0;           /* NodeCnt */
    fd_3D57_0C48 = 0;           /* NodeNum */
    fd_50F6_10A0 = 0;           /* BirdOn */
    fd_50F6_022C = 0;           /* CatCycle */
    fd_50F6_0244 = 0;           /* CatFrame */
    fd_50F6_0254 = 0;           /* CatOn */
    fd_50F6_04E4 = 0;           /* DogFrame */
    fd_50F6_0506 = 0;           /* DogDir */
    fd_3D57_0C3E = 0;           /* FootHere */
    fd_3D57_0C42 = 0;           /* FootTog */
    fd_50F6_03E0 = 0;           /* FootX */
    fd_50F6_046A = 0;           /* FootY */
    fd_50F6_0470 = 0;           /* MowX */
    fd_50F6_047A = 0;           /* MowY */
    fd_50F6_0202 = 0;           /* BoyIsMowing */
    fd_50F6_0352 = 0;           /* RainOn */
    fd_50F6_105C = 0;           /* SwarmDelayB */
    fd_50F6_1066 = 0;           /* SwarmDelayR */
    fd_50F6_108C = 1;           /* BirdFrame */
    fd_50F6_0364 = 1;           /* LastColonyPopB */
    fd_50F6_036E = 1;           /* LastColonyPopR */
    fd_50F6_10BC = -1;          /* BoyMsgOffset */
    fd_50F6_07C2 = -1;          /* YardCycle */
}

extern int far fd_3D57_0C44;

void far SimKidInside(void);
void far o06_35F5_02B9(void);
void far o06_35F5_11FF(void);
void far o06_35F5_14CC(void);
void far o06_35F5_1803(void);
void far o06_35F5_020C(void);
void far o06_35F5_1E54(void);

/* DoSimYard */
void far o06_35F5_0173(void)
{
    fd_50F6_07C2++;
    if (fd_50F6_07C2 >= 0x400)
        fd_50F6_07C2 = 0;
    if (fd_3D57_0C48 < 0x26)
        SimKidInside();
    else
        o06_35F5_02B9();
    o06_35F5_11FF();
    o06_35F5_14CC();
    if (fd_3D57_0C44 == 0)      /* ForSaleState */
        o06_35F5_1803();
    o06_35F5_020C();
    o06_35F5_1E54();
}

extern long far f_00F8_02BE(void);

/* SendBoyMsg */
void far o06_35F5_01CA(int message)
{
    if (message <= 22) {
        fd_50F6_109C = f_00F8_02BE() + 300L;
        fd_50F6_10B0 = 1;
        fd_50F6_10BC = message;
    }
}

extern int far fd_50F6_0F24;
extern int far fd_50F6_0B20;
extern int far RRand(int range);
extern int far SRand1(int range);
extern int far fd_50F6_0356;
extern void far f_0BE8_063A(void);

/* SimRain */
void far o06_35F5_020C(void)
{
    if (fd_50F6_0F24 != 1) {            /* TERRAINset */
        if (fd_50F6_0352 == 0) {
            if (fd_50F6_0B20 != 0xa8) { /* GlobalKey */
                if (RRand(32) != 0)
                    return;
                if (RRand(128) != 0)
                    return;
            }
            fd_50F6_0352 = 1;
            fd_50F6_0356 = SRand1(150) + 150;   /* RainCnt */
            f_0BE8_063A();                      /* InitWater */
            o06_35F5_01CA(0);
            return;
        }
        if (fd_50F6_0356 > 0)
            fd_50F6_0356--;
        if (fd_50F6_0356 < 1)
            fd_50F6_0352 = 0;
    }
}

/* SCAFFOLD BEGIN: unrecovered same-module functions */
void far o06_35F5_02B9(void) {}
void far SimKidInside(void) {}
void far o06_35F5_11FF(void) {}
void far o06_35F5_14CC(void) {}
void far o06_35F5_1803(void) {}
void far o06_35F5_1E54(void) {}
/* SCAFFOLD END */
