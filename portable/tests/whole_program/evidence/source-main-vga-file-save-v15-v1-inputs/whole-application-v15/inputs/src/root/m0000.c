/* Root module 0000: sampled-sound and song resources (database load hook that
 * unpacks DAC samples, sample free list, song loading and release). */

typedef char far * far *Handle;

#pragma pack(1)
struct Sample {
    Handle data;
    unsigned len;
    unsigned loop;
    char looped;
    unsigned char octave;
    int tune;
    int loaded;
    char name[15];
    int object;
};
#pragma pack()

struct Song {
    int program[14];
    unsigned bank[14];
    Handle data;
};

struct Instr {
    int kind;
    struct Sample far *sample;
};

int g_181C = 0;

extern Handle far f_171C_13CA(long size, int flags, char far *name);
extern char far * far f_171C_1B84(Handle h);
extern char far *f_290D_000E(unsigned char far *src, char far *dst, unsigned n);
extern Handle far f_171C_1BBA(Handle h);
extern void far f_171C_1C0A(Handle h);

void far f_0000_0000(Handle far *handle, unsigned far *size, int object, int type)
{
    Handle h;
    unsigned n;

    if (type == 5) {
        n = (*size - 16) << 1;
        *size = n;
        h = f_171C_13CA((long)n, 0x18, "DACsample");
        f_290D_000E(f_171C_1B84(*handle), *h, n);
        f_171C_1BBA(*handle);
        f_171C_1C0A(*handle);
        *handle = h;
    }
}

extern Handle far f_1A53_00BA(int object, int kind);
extern long far f_171C_1C1C(Handle h);

int far f_0000_0090(struct Sample far *s)
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

extern void far f_29F0_000A(void);
extern struct Sample far * far fd_50F6_0150[];
extern void far db_ReleaseHandle(Handle h);
extern void far f_29F0_0012(void);

void far f_0000_00DE(void)
{
    int i;
    struct Sample far *s;

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

extern void far Punt(char far *message);
extern int far g_7574;

void far f_0000_0149(struct Sample far *s)
{
    if (g_181C > 38)
        Punt("FREELIST > 38");
    fd_50F6_0150[g_181C++] = s;
    if (g_7574 == 0)
        f_0000_00DE();
}

extern int far f_284A_0004(void);
extern void far StopSong(void);
extern unsigned far f_1959_0002(unsigned value);
extern int far g_7576;
extern int far g_7578;
extern void far db_UnhookObject(int object, int kind);
extern void far f_171C_1E86(Handle h, int flags);
extern int far f_171C_1E9A(Handle h);
extern void far f_171C_13E4(Handle h);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);
extern struct Instr far fd_50F6_0000[];
void far f_0000_039B(struct Song far *song, int number);

int far f_0000_0193(struct Song far *song, int number)
{
    Handle h;
    Handle old;
    int far *hdr;
    unsigned n;
    int i;

    if (f_284A_0004() == 0)
        StopSong();
    h = f_1A53_00BA(number, 0x12);
    if (h == 0)
        return -1;
    hdr = (int far *)f_171C_1B84(h);
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
        song->data = f_171C_13CA((long)n, 0x39, "song");
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
            if (f_0000_0090(fd_50F6_0000[song->bank[i]].sample) == -1) {
                f_0000_039B(song, number);
                return -1;
            }
            fd_50F6_0000[song->bank[i]].sample->loaded = 2;
        }
    }
    return 0;
}

void far f_0000_039B(struct Song far *song, int number)
{
    int i;
    struct Sample far *s;

    if (song->data != 0) {
        f_171C_1C0A(song->data);
        song->data = 0;
    }
    for (i = 0; i < 14; i++) {
        if (fd_50F6_0000[song->bank[i]].kind == 1 && (s = fd_50F6_0000[song->bank[i]].sample) != 0) {
            if (s->loaded == 2)
                s->loaded = 1;
            f_0000_0149(s);
        }
    }
}

extern void far f_295C_0391(void);

void far f_0000_0429(void)
{
    int i;

    StopSong();
    f_295C_0391();
    for (i = 0; i < 56; i++)
        if (fd_50F6_0000[i].kind == 1)
            f_0000_0149(fd_50F6_0000[i].sample);
}

extern int far fd_50F6_01F0[];
extern int far g_756E;
extern struct Song far * far fd_55B3_00B4;
extern void far f_295C_0015(void);

void far f_0000_046F(void)
{
    if (fd_50F6_01F0[0] != 0) {
        if (g_756E == 2)
            StopSong();
        if (fd_55B3_00B4->data != 0)
            f_295C_0015();
        f_0000_00DE();
    }
}
