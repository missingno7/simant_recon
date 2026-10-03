#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#pragma pack(push, 2)
/* Root module 295C: MIDI (MPU-401) voice allocation and output. */







struct Snd {
    int16_t w0;
    int16_t w2;
    int16_t w4;
    int16_t w6;
    int16_t w8;
    int16_t wA;
    int16_t state;
};

struct Song {
    int16_t a;
    int16_t b;
    int16_t c;
    int16_t d;
};

void  f_295C_043E(int16_t dev, int16_t a, int16_t b, int16_t c);
void  f_295C_04A2(int16_t dev, int16_t a, int16_t b);
void  f_295C_04FB(int16_t a, int16_t b, int16_t dev);
void  f_295C_053D(int16_t a, int16_t b, int16_t dev);
void  f_295C_0577(void);
void  f_295C_0578(int16_t dev, int16_t a);
extern void  f_290D_0193();
extern void  f_2815_0165();
extern void  f_29D6_000A();
extern void  f_29D6_0082();
extern void  f_29D6_00D9();
extern void  f_290D_026C();
extern void  f_2815_024D();
extern void  f_29D6_0148();
extern void  f_29D6_015D();
extern void  f_29D6_0197();
extern void  f_2815_0275();

uint16_t g_7502 = 0x7f;
void ( *g_7504[8])() = {
    0, f_290D_0193, f_2815_0165, f_29D6_000A, f_29D6_0082, f_29D6_00D9, f_295C_043E, f_295C_04A2
};
void ( *g_7524[8])() = {
    0, f_290D_026C, f_2815_024D, f_29D6_0148, f_29D6_015D, f_29D6_0197, f_295C_04FB, f_295C_053D
};
void ( *g_7544[8])() = {
    0, f_295C_0577, f_2815_0275, f_295C_0577, f_295C_0577, f_295C_0577, f_295C_0578, f_295C_0577
};

void  f_295C_000A(int16_t volume)
{
    g_7502 = volume;
}



extern void  f_0000_0149(struct Snd  *snd);
int16_t  f_295C_00C9(int16_t type, int16_t prio);

void  f_295C_0015(void)
{
    int16_t i;
    PortableWholeAudioRuntimeChannel  *c;
    struct Snd  *s;

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

int16_t  f_295C_00C9(int16_t type, int16_t prio)
{
    int16_t i;
    int16_t bestIdx;
    int16_t bestAge;
    PortableWholeAudioRuntimeChannel  *c;
    int16_t best;
    struct Snd  *s;

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



void  f_295C_01EC(int16_t prio, int16_t dev, int16_t note, int16_t vel)
{
    int16_t v;

    v = f_295C_00C9(fd_50F6_0000[dev].kind, prio);
    if (v < 0)
        return;
    vel = (uint16_t)vel * g_7502 >> 7;
    (*g_7524[fd_50F6_4A4E[v].type])(fd_50F6_4A4E[v].c4, fd_50F6_4A4E[v].num, dev);
    if (fd_50F6_4A4E[v].c3 != dev)
        (*g_7544[fd_50F6_4A4E[v].type])(dev, fd_50F6_4A4E[v].num);
    (*g_7504[fd_50F6_4A4E[v].type])(dev, note, vel, fd_50F6_4A4E[v].num);
    fd_50F6_4A4E[v].c2 = prio;
    fd_50F6_4A4E[v].c3 = dev;
    fd_50F6_4A4E[v].c4 = note;
    fd_50F6_4A4E[v].c5 = 0;
}

void  f_295C_02E8(int16_t dev, int16_t note)
{
    int16_t i;

    for (i = 0; fd_50F6_4A4E[i].type; i++) {
        if (fd_50F6_4A4E[i].c4 == note && fd_50F6_4A4E[i].c3 == dev) {
            (*g_7524[fd_50F6_0000[dev].kind])(note, fd_50F6_4A4E[i].num, dev);
            fd_50F6_4A4E[i].c4 = 0;
            fd_50F6_4A4E[i].c2 = 0;
            fd_50F6_4A4E[i].c5 = 15;
        }
    }
}

extern struct Song  fd_55B3_0A82[];

void  f_295C_0367(int16_t n)
{
    f_295C_01EC(fd_55B3_0A82[n].b, fd_55B3_0A82[n].c, fd_55B3_0A82[n].a, fd_55B3_0A82[n].d);
}

extern uint8_t  f_29F0_0038(int16_t port);
extern void  f_29F0_002A(int16_t port, int16_t value);

/* CSE-1: the folded unsigned-byte >= 0 check retains the original byte
 * temporary and index spill. STEERED: original eliminated expression unknown. */
void  f_295C_0391(void)
{
    int16_t i;
    for (i = 0; fd_50F6_4A4E[i].type; i++) {
        if (fd_50F6_4A4E[i].c3 >= 0 && fd_50F6_4A4E[i].c2)
            f_295C_02E8(fd_50F6_4A4E[i].c3, fd_50F6_4A4E[i].c4);
    }
}

void  f_295C_03DC(int16_t value)
{
    while (f_29F0_0038(0x331) & 0x40)
        ;
    f_29F0_002A(0x330, value);
}

void  f_295C_03FF(int16_t value)
{
    while (f_29F0_0038(0x331) & 0x40)
        ;
    f_29F0_002A(0x331, value);
    do {
        while (f_29F0_0038(0x331) & 0x80)
            ;
    } while (f_29F0_0038(0x330) != 0xfe);
}

void  f_295C_043E(int16_t dev, int16_t a, int16_t b, int16_t c)
{
    int16_t  *info;

    if (*(info = portable_whole_audio_driver_info(&fd_50F6_0000[dev])) != -1) {
        b += info[1];
        f_295C_03FF(0xd7);
        f_295C_03DC(c + 0x90);
        f_295C_03DC(portable_whole_audio_driver_info(&fd_50F6_0000[dev])[2] + a);
        f_295C_03DC(b);
    }
}

void  f_295C_04A2(int16_t dev, int16_t a, int16_t b)
{
    int16_t  *info;

    info = portable_whole_audio_driver_info(&fd_50F6_0000[dev]);
    f_295C_03FF(0xd7);
    b += info[1];
    f_295C_03DC(0x99);
    f_295C_03DC(info[0]);
    f_295C_03DC(b);
}

void  f_295C_04FB(int16_t a, int16_t b, int16_t dev)
{
    f_295C_03FF(0xd7);
    f_295C_03DC(b + 0x80);
    f_295C_03DC(portable_whole_audio_driver_info(&fd_50F6_0000[dev])[2] + a);
    f_295C_03DC(0);
}

void  f_295C_053D(int16_t a, int16_t b, int16_t dev)
{
    f_295C_03FF(0xd7);
    f_295C_03DC(0x89);
    f_295C_03DC(portable_whole_audio_driver_info(&fd_50F6_0000[dev])[0]);
    f_295C_03DC(0);
}

void  f_295C_0577(void)
{
}

void  f_295C_0578(int16_t dev, int16_t a)
{
    int16_t  *info;

    info = portable_whole_audio_driver_info(&fd_50F6_0000[dev]);
    if (*info != -1) {
        f_295C_03FF(0xd7);
        f_295C_03DC(a + 0xc0);
        f_295C_03DC(*info);
    }
}

#pragma pack(pop)
