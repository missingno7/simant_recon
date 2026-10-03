#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#pragma pack(push, 2)
/* Root module 0000: sampled-sound and song resources (database load hook that
 * unpacks DAC samples, sample free list, song loading and release). */

typedef char  *  *Handle;

#pragma pack(1)

#pragma pack(2)

struct Song {
    int16_t program[14];
    uint16_t bank[14];
    Handle data;
};



int16_t g_181C = 0;

extern Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);
extern char  *  f_171C_1B84(Handle h);
extern char  *f_290D_000E(uint8_t  *src, char  *dst, uint16_t n);
extern Handle  f_171C_1BBA(Handle h);
extern void  f_171C_1C0A(Handle h);

void  f_0000_0000(Handle  *handle, uint16_t  *size, int16_t object, int16_t type)
{
    Handle h;
    uint16_t n;

    if (type == 5) {
        n = (*size - 16) << 1;
        *size = n;
        h = f_171C_13CA((int32_t)n, 0x18, "DACsample");
        f_290D_000E(f_171C_1B84(*handle), *h, n);
        f_171C_1BBA(*handle);
        f_171C_1C0A(*handle);
        *handle = h;
    }
}

extern Handle  f_1A53_00BA(int16_t object, int16_t kind);
extern int32_t  f_171C_1C1C(Handle h);

int16_t  f_0000_0090(PortableWholeAudioSample  *s)
{
    Handle h;

    if (s->loaded != 0)
        return 1;
    h = f_1A53_00BA(s->object, 5);
    s->data = h;
    s->len = f_171C_1C1C(h);
    s->loaded = 1;
    return 0;
}

extern void  f_29F0_000A(void);

extern void  db_ReleaseHandle(Handle h);
extern void  f_29F0_0012(void);

void  f_0000_00DE(void)
{
    int16_t i;
    PortableWholeAudioSample  *s;

    f_29F0_000A();
    for (i = 0; i < g_181C; i++) {
        s = fd_50F6_0150[i];
        if (s->loaded == 1 && s->data != 0) {
            db_ReleaseHandle(s->data);
            s->data = 0;
            s->loaded = 0;
        }
    }
    g_181C = 0;
    f_29F0_0012();
}

extern void  Punt(char  *message);
extern int16_t  g_7574;

void  f_0000_0149(PortableWholeAudioSample  *s)
{
    if (g_181C > 38)
        Punt("FREELIST > 38");
    fd_50F6_0150[g_181C++] = s;
    if (g_7574 == 0)
        f_0000_00DE();
}

extern int16_t  f_284A_0004(void);
extern void  StopSong(void);
extern uint16_t  f_1959_0002(uint16_t value);
extern int16_t  g_7576;
extern int16_t  g_7578;
extern void  db_UnhookObject(int16_t object, int16_t kind);
extern void  f_171C_1E86(Handle h, int16_t flags);
extern int16_t  f_171C_1E9A(Handle h);
extern void  f_171C_13E4(Handle h);


void  f_0000_039B(struct Song  *song, int16_t number);

int16_t  f_0000_0193(struct Song  *song, int16_t number)
{
    Handle h;
    Handle old;
    int16_t  *hdr;
    uint16_t n;
    int16_t i;

    if (f_284A_0004() == 0)
        StopSong();
    h = f_1A53_00BA(number, 0x12);
    if (h == 0)
        return -1;
    hdr = (int16_t  *)f_171C_1B84(h);
    number = f_1959_0002(hdr[0]);
    g_7576 = hdr[3];
    g_7576 = f_1959_0002(g_7576);
    f_171C_1BBA(h);
    db_ReleaseHandle(h);
    g_7578 = number;
    song->data = f_1A53_00BA(number, 0x14);
    db_UnhookObject(number, 0x14);
    f_171C_1E86(song->data, 0x31);
    if (song->data == 0)
        return -1;
    if (f_171C_1E9A(song->data) != 0) {
        old = song->data;
        n = f_171C_1C1C(old);
        song->data = f_171C_13CA((int32_t)n, 0x39, "song");
        if (song->data == 0) {
            f_171C_13E4(old);
            return -1;
        }
        _fmemcpy(*song->data, *old, n);
        f_171C_13E4(old);
    }
    f_171C_1C1C(song->data);
    for (i = 0; i < 14; i++) {
        if (fd_50F6_0000[song->bank[i]].kind == 1) {
            if (f_0000_0090(portable_whole_audio_sample(&fd_50F6_0000[song->bank[i]])) == -1) {
                f_0000_039B(song, number);
                return -1;
            }
            portable_whole_audio_sample(&fd_50F6_0000[song->bank[i]])->loaded = 2;
        }
    }
    return 0;
}

void  f_0000_039B(struct Song  *song, int16_t number)
{
    int16_t i;
    PortableWholeAudioSample  *s;

    if (song->data != 0) {
        f_171C_1C0A(song->data);
        song->data = 0;
    }
    for (i = 0; i < 14; i++) {
        if (fd_50F6_0000[song->bank[i]].kind == 1 && (s = portable_whole_audio_sample(&fd_50F6_0000[song->bank[i]])) != 0) {
            if (s->loaded == 2)
                s->loaded = 1;
            f_0000_0149(s);
        }
    }
}

extern void  f_295C_0391(void);

void  f_0000_0429(void)
{
    int16_t i;

    StopSong();
    f_295C_0391();
    for (i = 0; i < 56; i++)
        if (fd_50F6_0000[i].kind == 1)
            f_0000_0149(portable_whole_audio_sample(&fd_50F6_0000[i]));
}


extern int16_t  g_756E;
extern struct Song  *  fd_55B3_00B4;
extern void  f_295C_0015(void);

void  f_0000_046F(void)
{
    if (fd_50F6_01F0[0] != 0) {
        if (g_756E == 2)
            StopSong();
        if (fd_55B3_00B4->data != 0)
            f_295C_0015();
        f_0000_00DE();
    }
}

#pragma pack(pop)
