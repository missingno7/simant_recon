/*
 * Loads and advances MIDI songs and their tracks. It decodes timed events and sends notes
 * through the sound driver channel layer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 284A; partial original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Functions not yet exact: snd_song_read_be16.
 */

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

extern void far snd_service_pending(void);

int far snd_service_and_test_stopped(void)
{
    snd_service_pending();
    return g_756E == 0;
}

void far StopSong(void);
extern struct Song far * far fd_55B3_00B4;
extern int far snd_load_song_resources(struct Song far *song, int number);
extern int far WinPrintf(char far *format, ...);
extern void far snd_control_interrupts_disable(void);
extern char far * far * far fd_50F6_4B28;
static int g_8DD8[18];
static _segment g_8DFC;
extern int far fd_50F6_4B2C;
extern int far mem_Size(char far * far *handle);
void far snd_song_initialize_tracks(void);
void far snd_song_reset_clock(void);
extern int far fd_55B3_6B42;
extern int far fd_50F6_4B8E[];
extern int far fd_50F6_4BAA[];
extern void far snd_control_interrupts_enable(void);

void far snd_load_and_start_song(int number)
{
    int i;

    StopSong();
    if (snd_load_song_resources(fd_55B3_00B4, number) == -1) {
        WinPrintf("music failure\n");
        return;
    }
    snd_control_interrupts_disable();
    g_7572 = 0;
    fd_50F6_4B28 = fd_55B3_00B4->data;
    g_8DFC = ((_segment far *)fd_50F6_4B28)[1];
    WinPrintf("Seg=%x, buf=%p, handle=%p", g_8DFC, *fd_50F6_4B28, fd_50F6_4B28);
    fd_50F6_4B2C = mem_Size(fd_50F6_4B28);
    snd_song_initialize_tracks();
    snd_song_reset_clock();
    g_756E = 1;
    fd_55B3_6B42 = 5;
    for (i = 0; i < 14; i++) {
        fd_50F6_4B8E[i] = fd_55B3_00B4->bank[i];
        fd_50F6_4BAA[i] = fd_55B3_00B4->program[i];
    }
    snd_control_interrupts_enable();
}

extern void far snd_release_song_resources(struct Song far *song, int number);
extern void far snd_stop_assigned_voices(void);

void far StopSong(void)
{
    if (g_756E) {
        g_756E = 0;
        snd_release_song_resources(fd_55B3_00B4, g_7578);
        snd_stop_assigned_voices();
    }
}


extern int far fd_50F6_4B2E;
extern long far fd_50F6_4B42[];
extern unsigned char far fd_50F6_4B30[];
extern long far fd_50F6_4B8A;
extern void far snd_stop_instrument_note(int program, int note);
extern void far snd_start_instrument_note(int bank, int program, int note, int velocity);
int far snd_song_read_be16(int off)
{
    return SONG(off) << 8 | SONG(off + 1);
}


long far snd_song_read_be32(int off)
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

void far snd_song_index_track_chunks(int count, int off)
{
    int i;
    long len;

    for (i = 0; i < count; i++) {
        len = snd_song_read_be32(off + 4);
        g_8DD8[i] = off + 8;
        off += len + 8;
    }
}

static int far *g_8DFE;

long far snd_song_read_varlen(void)
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

void far snd_song_set_volume(unsigned volume)
{
    g_7570 = volume;
}


void far snd_song_initialize_tracks(void)
{
    long len;
    int i;

    len = snd_song_read_be32(4);
    g_7566 = snd_song_read_be16(10);
    fd_50F6_4B2E = snd_song_read_be16(12);
    snd_song_index_track_chunks(g_7566, len + 8);
    for (i = 0; i < g_7566; i++) {
        g_8DFE = &g_8DD8[i];
        fd_50F6_4B42[i] = snd_song_read_varlen();
        fd_50F6_4B30[i] = SONG(*g_8DFE);
    }
}

static unsigned char far *g_8E02;
void far snd_song_set_tempo(unsigned division, long tempo);

void far snd_song_reset_clock(void)
{
    g_7568 = 0;
    g_756C = 0;
    g_8DFE = g_8DD8;
    g_8E02 = fd_50F6_4B30;
    snd_song_set_tempo(0x1e0, 500000L);
    fd_55B3_6B42 = 99;
}

void far f_284A_0324(void)
{
}


void far snd_song_set_tempo(unsigned division, long tempo)
{
    long v;

    if (division == 0)
        v = 0;
    else
        v = tempo / 1000 * 1194 / division;
    fd_50F6_4B8A = v / 13;
}

int far snd_song_schedule_next_track(void)
{
    long delta;
    long t;
    int best;
    int i;

    if (*g_8E02 != 0x2f) {
        delta = snd_song_read_varlen();
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


void far snd_song_dispatch_note(int chan, int note, unsigned velocity)
{
    velocity = g_7570 * velocity >> 7;
    if (velocity == 0)
        snd_stop_instrument_note(fd_50F6_4B8E[chan], note);
    else
        snd_start_instrument_note(fd_50F6_4BAA[chan], fd_50F6_4B8E[chan], note, velocity);
}

void far snd_song_set_channel_instrument(int chan, int program)
{
    fd_50F6_4B8E[chan] = program;
}

int g_75A4[] = { 2, 2, 2, 2, 1, 1, 2 };

void far snd_song_dispatch_channel_event(unsigned status)
{
    int type;
    int chan;

    type = (status & 0x70) >> 4;
    chan = status & 0xf;
    if (chan < 14) {
        switch (type) {
        case 0:
            snd_song_dispatch_note(chan, SONG(*g_8DFE) + g_7576, 0);
            break;
        case 1:
            snd_song_dispatch_note(chan, SONG(*g_8DFE) + g_7576, SONGP(*g_8DFE)[1]);
            break;
        case 12:
            snd_song_set_channel_instrument(chan, SONG(*g_8DFE));
            break;
        }
    }
    *g_8DFE += g_75A4[type];
}

void far snd_song_dispatch_meta_event(void)
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
        snd_song_set_tempo(fd_50F6_4B2E, tempo);
    } else {
        (*g_8DFE)++;
        *g_8DFE += (int)snd_song_read_varlen();
    }
}

void far snd_song_skip_sysex_payload(unsigned char status)
{
    *g_8DFE += (int)snd_song_read_varlen();
}

int far snd_song_process_due_events(void)
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
            snd_song_skip_sysex_payload(*g_8E02);
        else if (*g_8E02 == 0xff)
            snd_song_dispatch_meta_event();
        else
            snd_song_dispatch_channel_event(*g_8E02);
        r = snd_song_schedule_next_track();
    } while (r == 0 && g_756E != 2);
    g_7574 = 0;
    return r ? r : 1;
}
