#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/audio_events.h"
#pragma pack(push, 2)

/* Root module 290D (0x290DE-0x293A6): sampled sound (digitised voice) channels. */







char  *f_290D_000E(uint8_t  *src, char  *dst, uint16_t n);
void  f_290D_0098(PortableWholeAudioSample  *s, uint16_t step, int16_t vol, int16_t ch);
void  f_290D_0193(int16_t instr, int16_t note, int16_t vol, int16_t ch);
void  f_290D_026C(int16_t a, int16_t ch);

int16_t fd_55B3_74C0 = 0;
uint16_t g_74C2[] = { 0x100, 0x10f, 0x11f, 0x130, 0x142, 0x155, 0x169, 0x17f, 0x196, 0x1ae, 0x1c8, 0x1e3 };

char  *f_290D_000E(uint8_t  *src, char  *dst, uint16_t n)
{
    char delta[16];
    char acc;
    uint16_t i;
    uint16_t j;

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

extern int16_t  g_7574;
extern void  f_29F0_000A(void);

extern void  f_0000_0090(PortableWholeAudioSample  *s);
extern void  f_29F0_0012(void);
extern uint16_t  fd_55B3_6B9E;
extern void  f_28BC_03CC(void);

void  f_290D_0098(PortableWholeAudioSample  *s, uint16_t step, int16_t vol, int16_t ch)
{
    PortableWholeAudioRuntimeSample  *c;

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
    {
        const uint8_t *sample_pcm =
            (const uint8_t *)(*(char  *  *)s->data);
        PortableWholeAudioEventStatus event_status = portable_whole_audio_sample_start(
            (uint16_t)ch, sample_pcm, (uint16_t)s->len, (uint16_t)s->loop,
            (uint16_t)step, (uint16_t)vol, s->looped != 0);
        if (event_status != PORTABLE_WHOLE_AUDIO_EVENT_OK)
            portable_whole_audio_event_fault(event_status);
    }
    f_29F0_0012();
    f_28BC_03CC();
}

extern void  f_0000_0149(PortableWholeAudioSample  *s);


void  f_290D_0193(int16_t instr, int16_t note, int16_t vol, int16_t ch)
{
    PortableWholeAudioSample  *s;
    uint16_t step;
    int16_t oct;
    uint8_t base;

    s = fd_55B3_6B4C[ch].owner;
    fd_55B3_6B4C[ch].snd = 0;
    if (s && s->loaded == 1)
        f_0000_0149(s);
    s = (PortableWholeAudioSample  *)portable_whole_audio_sample(&fd_50F6_0000[instr]);
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

void  f_290D_026C(int16_t a, int16_t ch)
{
    PortableWholeAudioSample  *s;

    f_29F0_000A();
    s = fd_55B3_6B4C[ch].owner;
    if (s && s->loaded == 1)
        f_0000_0149(s);
    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;
    {
        PortableWholeAudioEventStatus event_status =
            portable_whole_audio_sample_stop((uint16_t)ch);
        if (event_status != PORTABLE_WHOLE_AUDIO_EVENT_OK)
            portable_whole_audio_event_fault(event_status);
    }
    f_29F0_0012();
}

#pragma pack(pop)
