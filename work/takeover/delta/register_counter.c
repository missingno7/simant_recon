/* Root module 290D (0x290DE-0x293A6): sampled sound (digitised voice) channels. */

struct Sample {
    char far *data;
    unsigned len;
    unsigned loop;
    char looped;
    unsigned char octave;
    int tune;
    int loaded;
};

struct SndChan {
    unsigned pos;
    struct Sample far *snd;
    unsigned end;
    unsigned start;
    unsigned step;
    unsigned voltab;
    unsigned char frac;
    unsigned char flags;
    struct Sample far *owner;
};

struct Instr {
    int a;
    unsigned char far *p;
};

char far *f_290D_000E(unsigned char far *src, char far *dst, unsigned n);
void far f_290D_0098(struct Sample far *s, unsigned step, int vol, int ch);
void far f_290D_0193(int instr, int note, int vol, int ch);
void far f_290D_026C(int a, int ch);

int fd_55B3_74C0 = 0;
unsigned g_74C2[] = { 0x100, 0x10f, 0x11f, 0x130, 0x142, 0x155, 0x169, 0x17f, 0x196, 0x1ae, 0x1c8, 0x1e3 };

char far *f_290D_000E(unsigned char far *src, char far *dst, unsigned n)
{
    char delta[16];
    char acc;
    register unsigned i;
    unsigned j;

    acc = 0x80;
    for (i = 0; i < 16; i++)
        delta[i] = *src++;
    n >>= 1;
    j = i = 0;
    for (; j < n; j++) {
        acc += delta[src[j] >> 4];
        dst[i] = acc;
        acc += delta[src[j] & 0xf];
        i++;
        dst[i] = acc;
        i++;
    }
    return dst;
}

extern int far g_7574;
extern void far f_29F0_000A(void);
extern struct SndChan far fd_55B3_6B4C[];
extern void far f_0000_0090(struct Sample far *s);
extern void far f_29F0_0012(void);
extern unsigned far fd_55B3_6B9E;
extern void far f_28BC_03CC(void);

void far f_290D_0098(struct Sample far *s, unsigned step, int vol, int ch)
{
    struct SndChan far *c;

    if (g_7574 && s->loaded == 0)
        return;
    f_29F0_000A();
    c = &fd_55B3_6B4C[ch];
    if (s->loaded == 0)
        f_0000_0090(s);
    if (s->loaded == 0) {
        f_29F0_0012();
        return;
    }
    c->pos = 0;
    c->start = s->loop + 2;
    c->end = s->len + c->pos - 2;
    c->snd = s;
    c->frac = 0;
    c->step = step;
    c->voltab = (vol << 8) + fd_55B3_6B9E;
    if (s->looped == 0)
        c->flags &= 0x7f;
    else
        c->flags |= 0x80;
    c->owner = s;
    f_29F0_0012();
    f_28BC_03CC();
}

extern void far f_0000_0149(struct Sample far *s);
extern struct Instr far fd_50F6_0000[];

void far f_290D_0193(int instr, int note, int vol, int ch)
{
    struct Sample far *s;
    unsigned step;
    int oct;
    unsigned char base;

    s = fd_55B3_6B4C[ch].owner;
    fd_55B3_6B4C[ch].snd = 0;
    if (s && s->loaded == 1)
        f_0000_0149(s);
    s = (struct Sample far *)fd_50F6_0000[instr].p;
    note += s->tune;
    step = g_74C2[note % 12];
    oct = note / 12;
    base = s->octave;
    vol += fd_55B3_74C0;
    if (vol < 0)
        vol = 0;
    if (vol > 0x7f)
        vol = 0x7f;
    if (base < oct)
        step <<= oct - base;
    else
        step >>= base - oct;
    f_290D_0098(s, step, (0x7f - vol) >> 4, ch);
}

void far f_290D_026C(int a, int ch)
{
    struct Sample far *s;

    f_29F0_000A();
    s = fd_55B3_6B4C[ch].owner;
    if (s && s->loaded == 1)
        f_0000_0149(s);
    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;
    f_29F0_0012();
}
