/* Root module 295C: MIDI (MPU-401) voice allocation and output. */

struct Chan {
    unsigned char type;
    unsigned char num;
    unsigned char c2;
    unsigned char c3;
    unsigned char c4;
    unsigned char c5;
};

struct Drv {
    int count;
    int far *info;
};

struct Slot {
    long busy;
    int w4;
    int w6;
    int w8;
    int wA;
    int wC;
    struct Snd far *snd;
    int w12;
};

struct Snd {
    int w0;
    int w2;
    int w4;
    int w6;
    int w8;
    int wA;
    int state;
};

struct Song {
    int a;
    int b;
    int c;
    int d;
};

void far f_295C_043E(int dev, int a, int b, int c);
void far f_295C_04A2(int dev, int a, int b);
void far f_295C_04FB(int a, int b, int dev);
void far f_295C_053D(int a, int b, int dev);
void far f_295C_0577(void);
void far f_295C_0578(int dev, int a);
extern void far f_290D_0193();
extern void far f_2815_0165();
extern void far f_29D6_000A();
extern void far f_29D6_0082();
extern void far f_29D6_00D9();
extern void far f_290D_026C();
extern void far f_2815_024D();
extern void far f_29D6_0148();
extern void far f_29D6_015D();
extern void far f_29D6_0197();
extern void far f_2815_0275();

unsigned g_7502 = 0x7f;
void (far *g_7504[8])() = {
    0, f_290D_0193, f_2815_0165, f_29D6_000A, f_29D6_0082, f_29D6_00D9, f_295C_043E, f_295C_04A2
};
void (far *g_7524[8])() = {
    0, f_290D_026C, f_2815_024D, f_29D6_0148, f_29D6_015D, f_29D6_0197, f_295C_04FB, f_295C_053D
};
void (far *g_7544[8])() = {
    0, f_295C_0577, f_2815_0275, f_295C_0577, f_295C_0577, f_295C_0577, f_295C_0578, f_295C_0577
};

void far f_295C_000A(int volume)
{
    g_7502 = volume;
}

extern struct Chan far fd_50F6_4A4E[];
extern struct Slot far fd_55B3_6B4E[];
extern void far f_0000_0149(struct Snd far *snd);
int far f_295C_00C9(int type, int prio);

void far f_295C_0015(void)
{
    int i;
    struct Chan far *c;
    struct Snd far *s;

    for (i = 0; (c = &fd_50F6_4A4E[i])->type; i++) {
        if (c->type == 1 && fd_55B3_6B4E[c->num].busy == 0) {
            c->c2 = 0;
            s = fd_55B3_6B4E[c->num].snd;
            if (s && s->state == 1)
                f_0000_0149(s);
            fd_55B3_6B4E[c->num].snd = 0;
        }
    }
}

int far f_295C_00C9(int type, int prio)
{
    int i;
    int bestIdx;
    int bestAge;
    struct Chan far *c;
    int best;
    struct Snd far *s;

    best = 15;
    bestAge = bestIdx = i = 0;
    if (prio < 1)
        return -1;
    for (c = fd_50F6_4A4E; c->type; c = &fd_50F6_4A4E[++i]) {
        if (c->type == 1 && fd_55B3_6B4E[c->num].busy == 0) {
            c->c2 = 0;
            s = fd_55B3_6B4E[c->num].snd;
            if (s && s->state == 1)
                f_0000_0149(s);
            fd_55B3_6B4E[c->num].snd = 0;
        }
        if (c->type == type) {
            if (c->c2 < best || (c->c2 == best && c->c5 > bestAge)) {
                best = c->c2;
                bestIdx = i;
                bestAge = c->c5;
            }
        }
        c->c5++;
    }
    if (prio >= best)
        return bestIdx;
    return -1;
}

extern struct Drv far fd_50F6_0000[];

void far f_295C_01EC(int prio, int dev, int note, int vel)
{
    int v;

    v = f_295C_00C9(fd_50F6_0000[dev].count, prio);
    if (v < 0)
        return;
    vel = (unsigned)vel * g_7502 >> 7;
    (*g_7524[fd_50F6_4A4E[v].type])(fd_50F6_4A4E[v].c4, fd_50F6_4A4E[v].num, dev);
    if (fd_50F6_4A4E[v].c3 != dev)
        (*g_7544[fd_50F6_4A4E[v].type])(dev, fd_50F6_4A4E[v].num);
    (*g_7504[fd_50F6_4A4E[v].type])(dev, note, vel, fd_50F6_4A4E[v].num);
    fd_50F6_4A4E[v].c2 = prio;
    fd_50F6_4A4E[v].c3 = dev;
    fd_50F6_4A4E[v].c4 = note;
    fd_50F6_4A4E[v].c5 = 0;
}

void far f_295C_02E8(int dev, int note)
{
    int i;

    for (i = 0; fd_50F6_4A4E[i].type; i++) {
        if (fd_50F6_4A4E[i].c4 == note && fd_50F6_4A4E[i].c3 == dev) {
            (*g_7524[fd_50F6_0000[dev].count])(note, fd_50F6_4A4E[i].num, dev);
            fd_50F6_4A4E[i].c4 = 0;
            fd_50F6_4A4E[i].c2 = 0;
            fd_50F6_4A4E[i].c5 = 15;
        }
    }
}

extern struct Song far fd_55B3_0A82[];

void far f_295C_0367(int n)
{
    f_295C_01EC(fd_55B3_0A82[n].b, fd_55B3_0A82[n].c, fd_55B3_0A82[n].a, fd_55B3_0A82[n].d);
}

extern unsigned char far f_29F0_0038(int port);
extern void far f_29F0_002A(int port, int value);

void far f_295C_03DC(int value)
{
    while (f_29F0_0038(0x331) & 0x40)
        ;
    f_29F0_002A(0x330, value);
}

void far f_295C_03FF(int value)
{
    while (f_29F0_0038(0x331) & 0x40)
        ;
    f_29F0_002A(0x331, value);
    do {
        while (f_29F0_0038(0x331) & 0x80)
            ;
    } while (f_29F0_0038(0x330) != 0xfe);
}

void far f_295C_043E(int dev, int a, int b, int c)
{
    int far *info;

    if (*(info = fd_50F6_0000[dev].info) != -1) {
        b += info[1];
        f_295C_03FF(0xd7);
        f_295C_03DC(c + 0x90);
        f_295C_03DC(fd_50F6_0000[dev].info[2] + a);
        f_295C_03DC(b);
    }
}

void far f_295C_04A2(int dev, int a, int b)
{
    int far *info;

    info = fd_50F6_0000[dev].info;
    f_295C_03FF(0xd7);
    b += info[1];
    f_295C_03DC(0x99);
    f_295C_03DC(info[0]);
    f_295C_03DC(b);
}

void far f_295C_04FB(int a, int b, int dev)
{
    f_295C_03FF(0xd7);
    f_295C_03DC(b + 0x80);
    f_295C_03DC(fd_50F6_0000[dev].info[2] + a);
    f_295C_03DC(0);
}

void far f_295C_053D(int a, int b, int dev)
{
    f_295C_03FF(0xd7);
    f_295C_03DC(0x89);
    f_295C_03DC(fd_50F6_0000[dev].info[0]);
    f_295C_03DC(0);
}

void far f_295C_0577(void)
{
}

void far f_295C_0578(int dev, int a)
{
    int far *info;

    info = fd_50F6_0000[dev].info;
    if (*info != -1) {
        f_295C_03FF(0xd7);
        f_295C_03DC(a + 0xc0);
        f_295C_03DC(*info);
    }
}

/* SCAFFOLD BEGIN: best draft of f_295C_0391, not exact (original spills the i*6 CSE to [bp-2] and keeps the char at [bp-4]; this draft puts the char at [bp-1] and drops the spill) */
void far f_295C_0391(void)
{
    int i;
    unsigned char dev;

    for (i = 0; fd_50F6_4A4E[i].type; i++) {
        dev = fd_50F6_4A4E[i].c3;
        if (fd_50F6_4A4E[i].c2)
            f_295C_02E8(dev, fd_50F6_4A4E[i].c4);
    }
}
/* SCAFFOLD END */
