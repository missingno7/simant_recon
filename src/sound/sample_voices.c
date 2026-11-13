/*
 * Starts and controls digitized sound voices. It tracks sample playback position and channel
 * state for the interrupt mixer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 290D; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

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

char far *snd_decode_delta_nibbles(unsigned char far *src, char far *dst, unsigned n);
void far snd_start_sample_voice(struct Sample far *s, unsigned step, int vol, int ch);
void far snd_start_sample_note(int instr, int note, int vol, int ch);
void far snd_stop_sample_voice(int a, int ch);

int fd_55B3_74C0 = 0;
unsigned g_74C2[] = { 0x100, 0x10f, 0x11f, 0x130, 0x142, 0x155, 0x169, 0x17f, 0x196, 0x1ae, 0x1c8, 0x1e3 };

char far *snd_decode_delta_nibbles(unsigned char far *src, char far *dst, unsigned n)
{
    char delta[16];
    char acc;
    unsigned i;
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
extern void far snd_sample_interrupts_disable(void);
extern struct SndChan far fd_55B3_6B4C[];
extern void far snd_load_sample_resource(struct Sample far *s);
extern void far snd_sample_interrupts_enable(void);
extern unsigned far fd_55B3_6B9E;
extern void far snd_start_sample_timer(void);

void far snd_start_sample_voice(struct Sample far *s, unsigned step, int vol, int ch)
{
    struct SndChan far *c;

    if (g_7574 && s->loaded == 0)
        return;
    snd_sample_interrupts_disable();
    c = &fd_55B3_6B4C[ch];
    if (s->loaded == 0)
        snd_load_sample_resource(s);
    if (s->loaded == 0) {
        snd_sample_interrupts_enable();
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
    snd_sample_interrupts_enable();
    snd_start_sample_timer();
}

extern void far snd_queue_sample_release(struct Sample far *s);
extern struct Instr far fd_50F6_0000[];

void far snd_start_sample_note(int instr, int note, int vol, int ch)
{
    struct Sample far *s;
    unsigned step;
    int oct;
    unsigned char base;

    s = fd_55B3_6B4C[ch].owner;
    fd_55B3_6B4C[ch].snd = 0;
    if (s && s->loaded == 1)
        snd_queue_sample_release(s);
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
    snd_start_sample_voice(s, step, (0x7f - vol) >> 4, ch);
}

void far snd_stop_sample_voice(int a, int ch)
{
    struct Sample far *s;

    snd_sample_interrupts_disable();
    s = fd_55B3_6B4C[ch].owner;
    if (s && s->loaded == 1)
        snd_queue_sample_release(s);
    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;
    snd_sample_interrupts_enable();
}
