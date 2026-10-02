/* Root module 284A: MIDI song player. */

struct Song {
    int program[14];
    int bank[14];
    char far * far *data;
};

int g_7566 = 0;
long g_7568 = 0;
int g_756C = 0;
int g_756E = 0;
unsigned g_7570 = 0x7f;
int g_7572 = 0;
int g_7574 = 0;
int g_7576 = 0;
int g_7578 = 0;

#define SONGP(off) ((unsigned char _based(g_8DFC) *)(off))
#define SONG(off) (*SONGP(off))

extern void far f_0000_046F(void);

int far f_284A_0004(void)
{
    f_0000_046F();
    return g_756E == 0;
}

void far StopSong(void);
extern struct Song far * far fd_55B3_00B4;
extern int far f_0000_0193(struct Song far *song, int number);
extern int far WinPrintf(char far *format, ...);
extern void far f_29F0_001A(void);
extern char far * far * far fd_50F6_4B28;
static int g_8DD8[18];
static _segment g_8DFC;
extern int far fd_50F6_4B2C;
extern int far f_171C_1C1C(char far * far *handle);
void far f_284A_0256(void);
void far f_284A_02E4(void);
extern int far fd_55B3_6B42;
extern int far fd_50F6_4B8E[];
extern int far fd_50F6_4BAA[];
extern void far f_29F0_0022(void);

void far f_284A_0013(int number)
{
    int i;

    StopSong();
    if (f_0000_0193(fd_55B3_00B4, number) == -1) {
        WinPrintf("music failure\n");
        return;
    }
    f_29F0_001A();
    g_7572 = 0;
    fd_50F6_4B28 = fd_55B3_00B4->data;
    g_8DFC = ((_segment far *)fd_50F6_4B28)[1];
    WinPrintf("Seg=%x, buf=%p, handle=%p", g_8DFC, *fd_50F6_4B28, fd_50F6_4B28);
    fd_50F6_4B2C = f_171C_1C1C(fd_50F6_4B28);
    f_284A_0256();
    f_284A_02E4();
    g_756E = 1;
    fd_55B3_6B42 = 5;
    for (i = 0; i < 14; i++) {
        fd_50F6_4B8E[i] = fd_55B3_00B4->bank[i];
        fd_50F6_4BAA[i] = fd_55B3_00B4->program[i];
    }
    f_29F0_0022();
}

extern void far f_0000_039B(struct Song far *song, int number);
extern void far f_295C_0391(void);

void far StopSong(void)
{
    if (g_756E) {
        g_756E = 0;
        f_0000_039B(fd_55B3_00B4, g_7578);
        f_295C_0391();
    }
}

int far f_284A_0138(int off)
{
    return SONG(off + 1) << 8 | SONG(off);
}

long far f_284A_0151(int off)
{
    long v;
    int i;

    v = 0;
    for (i = 0; i < 4; i++) {
        v = (v << 8) + SONG(off);
        off++;
    }
    return v;
}

void far f_284A_0199(int count, int off)
{
    int i;
    long len;

    for (i = 0; i < count; i++) {
        len = f_284A_0151(off + 4);
        g_8DD8[i] = off + 8;
        off += len + 8;
    }
}

static int far *g_8DFE;

long far f_284A_01D5(void)
{
    long v;
    unsigned char c;
    int pos;

    pos = *g_8DFE;
    if ((v = SONG(pos++)) & 0x80) {
        v &= 0x7f;
        do {
            c = SONG(pos++);
            v = (v << 7) + (c & 0x7f);
        } while (c & 0x80);
    }
    *g_8DFE = pos;
    return v;
}

void far f_284A_024B(unsigned volume)
{
    g_7570 = volume;
}

extern int far fd_50F6_4B2E;
extern long far fd_50F6_4B42[];
extern unsigned char far fd_50F6_4B30[];

void far f_284A_0256(void)
{
    long len;
    int i;

    len = f_284A_0151(4);
    g_7566 = f_284A_0138(10);
    fd_50F6_4B2E = f_284A_0138(12);
    f_284A_0199(g_7566, len + 8);
    for (i = 0; i < g_7566; i++) {
        g_8DFE = &g_8DD8[i];
        fd_50F6_4B42[i] = f_284A_01D5();
        fd_50F6_4B30[i] = SONG(*g_8DFE);
    }
}

static unsigned char far *g_8E02;
void far f_284A_0325(unsigned division, long tempo);

void far f_284A_02E4(void)
{
    g_7568 = 0;
    g_756C = 0;
    g_8DFE = g_8DD8;
    g_8E02 = fd_50F6_4B30;
    f_284A_0325(0x1e0, 500000L);
    fd_55B3_6B42 = 99;
}

void far f_284A_0324(void)
{
}

extern long far fd_50F6_4B8A;

void far f_284A_0325(unsigned division, long tempo)
{
    long v;

    if (division == 0)
        v = 0;
    else
        v = tempo / 1000 * 1194 / division;
    fd_50F6_4B8A = v / 13;
}

int far f_284A_038F(void)
{
    long delta;
    long t;
    int best;
    int i;

    if (*g_8E02 != 0x2f) {
        delta = f_284A_01D5();
        fd_50F6_4B42[g_756C] += delta;
    } else
        fd_50F6_4B42[g_756C] = 0x7fffffffL;
    best = 0;
    for (i = 1; i < g_7566; i++)
        if (fd_50F6_4B42[best] > fd_50F6_4B42[i] && fd_50F6_4B30[i] != 0x2f)
            best = i;
    if (fd_50F6_4B30[best] != 0x2f) {
        t = fd_50F6_4B42[best];
        if (t != 0x7fffffffL) {
            delta = t - g_7568;
            g_7568 = t;
            g_8DFE = &g_8DD8[best];
            g_8E02 = &fd_50F6_4B30[best];
            g_756C = best;
            return (int)(fd_50F6_4B8A * delta >> 8);
        }
    }
    g_756E = 2;
    f_284A_0324();
    return 0;
}

extern void far f_295C_02E8(int program, int note);
extern void far f_295C_01EC(int bank, int program, int note, int velocity);

void far f_284A_04C9(int chan, int note, unsigned velocity)
{
    velocity = g_7570 * velocity >> 7;
    if (velocity == 0)
        f_295C_02E8(fd_50F6_4B8E[chan], note);
    else
        f_295C_01EC(fd_50F6_4BAA[chan], fd_50F6_4B8E[chan], note, velocity);
}

void far f_284A_0521(int chan, int program)
{
    fd_50F6_4B8E[chan] = program;
}

int g_75A4[] = { 2, 2, 2, 2, 1, 1, 2 };

void far f_284A_0537(unsigned status)
{
    int type;
    int chan;

    type = (status & 0x70) >> 4;
    chan = status & 0xf;
    if (chan < 14) {
        switch (type) {
        case 0:
            f_284A_04C9(chan, SONG(*g_8DFE) + g_7576, 0);
            break;
        case 1:
            f_284A_04C9(chan, SONG(*g_8DFE) + g_7576, SONGP(*g_8DFE)[1]);
            break;
        case 12:
            f_284A_0521(chan, SONG(*g_8DFE));
            break;
        }
    }
    *g_8DFE += g_75A4[type];
}

void far f_284A_05C5(void)
{
    long tempo;
    int pos;

    if (SONG(*g_8DFE) == 0x2f) {
        *g_8E02 = SONG(*g_8DFE);
        (*g_8DFE)--;
    } else if (SONG(*g_8DFE) == 0x51) {
        *g_8DFE += 2;
        pos = *g_8DFE;
        tempo = ((((long)SONGP(pos)[0] << 8) + SONGP(pos)[1]) << 8) + SONGP(pos)[2];
        *g_8DFE += 3;
        f_284A_0325(fd_50F6_4B2E, tempo);
    } else {
        (*g_8DFE)++;
        *g_8DFE += (int)f_284A_01D5();
    }
}

void far f_284A_0673(unsigned char status)
{
    *g_8DFE += (int)f_284A_01D5();
}

int far f_284A_067F(void)
{
    int r;

    if (g_756E != 1)
        return -1;
    g_7574 = 1;
    g_8DFC = ((_segment far *)fd_50F6_4B28)[1];
    do {
        if (SONG(*g_8DFE) & 0x80) {
            *g_8E02 = SONG(*g_8DFE);
            (*g_8DFE)++;
        }
        if (*g_8E02 == 0xf7 || *g_8E02 == 0xf0)
            f_284A_0673(*g_8E02);
        else if (*g_8E02 == 0xff)
            f_284A_05C5();
        else
            f_284A_0537(*g_8E02);
        r = f_284A_038F();
    } while (r == 0 && g_756E != 2);
    g_7574 = 0;
    return r ? r : 1;
}
