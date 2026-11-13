/*
 * Allocates MIDI voices and maps instruments to channels. It sends melodic and percussion events
 * through the MPU-401 output interface.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 295C; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Steered functions: snd_stop_assigned_voices.
 */

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

void far snd_midi_note_on(int dev, int a, int b, int c);
void far snd_midi_percussion_on(int dev, int a, int b);
void far snd_midi_note_off(int a, int b, int dev);
void far snd_midi_percussion_off(int a, int b, int dev);
void far f_295C_0577(void);
void far snd_midi_select_program(int dev, int a);
extern void far snd_start_sample_note();
extern void far snd_opl_set_note_level();
extern void far snd_ps1_set_note();
extern void far snd_regchip_set_note();
extern void far snd_tandy_set_note();
extern void far snd_stop_sample_voice();
extern void far snd_opl_clear_voice_pitch();
extern void far snd_ps1_silence_voice();
extern void far snd_regchip_silence_voice();
extern void far snd_tandy_silence_voice();
extern void far snd_opl_select_instrument();

unsigned g_7502 = 0x7f;
void (far *g_7504[8])() = {
    0, snd_start_sample_note, snd_opl_set_note_level, snd_ps1_set_note, snd_regchip_set_note, snd_tandy_set_note, snd_midi_note_on, snd_midi_percussion_on
};
void (far *g_7524[8])() = {
    0, snd_stop_sample_voice, snd_opl_clear_voice_pitch, snd_ps1_silence_voice, snd_regchip_silence_voice, snd_tandy_silence_voice, snd_midi_note_off, snd_midi_percussion_off
};
void (far *g_7544[8])() = {
    0, f_295C_0577, snd_opl_select_instrument, f_295C_0577, f_295C_0577, f_295C_0577, snd_midi_select_program, f_295C_0577
};

void far snd_set_voice_volume_scale(int volume)
{
    g_7502 = volume;
}

extern struct Chan far snd_voice_slots[];
extern struct Slot far fd_55B3_6B4E[];
extern void far snd_queue_sample_release(struct Snd far *snd);
int far snd_choose_voice_by_priority(int type, int prio);

void far snd_reap_finished_sample_voices(void)
{
    int i;
    struct Chan far *c;
    struct Snd far *s;

    for (i = 0; (c = &snd_voice_slots[i])->type; i++) {
        if (c->type == 1 && fd_55B3_6B4E[c->num].busy == 0) {
            c->c2 = 0;
            s = fd_55B3_6B4E[c->num].snd;
            if (s && s->state == 1)
                snd_queue_sample_release(s);
            fd_55B3_6B4E[c->num].snd = 0;
        }
    }
}

int far snd_choose_voice_by_priority(int type, int prio)
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
    for (c = snd_voice_slots; c->type; c = &snd_voice_slots[++i]) {
        if (c->type == 1 && fd_55B3_6B4E[c->num].busy == 0) {
            c->c2 = 0;
            s = fd_55B3_6B4E[c->num].snd;
            if (s && s->state == 1)
                snd_queue_sample_release(s);
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

extern struct Drv far snd_instrument_descriptors[];

void far snd_start_instrument_note(int prio, int dev, int note, int vel)
{
    int v;

    v = snd_choose_voice_by_priority(snd_instrument_descriptors[dev].count, prio);
    if (v < 0)
        return;
    vel = (unsigned)vel * g_7502 >> 7;
    (*g_7524[snd_voice_slots[v].type])(snd_voice_slots[v].c4, snd_voice_slots[v].num, dev);
    if (snd_voice_slots[v].c3 != dev)
        (*g_7544[snd_voice_slots[v].type])(dev, snd_voice_slots[v].num);
    (*g_7504[snd_voice_slots[v].type])(dev, note, vel, snd_voice_slots[v].num);
    snd_voice_slots[v].c2 = prio;
    snd_voice_slots[v].c3 = dev;
    snd_voice_slots[v].c4 = note;
    snd_voice_slots[v].c5 = 0;
}

void far snd_stop_instrument_note(int dev, int note)
{
    int i;

    for (i = 0; snd_voice_slots[i].type; i++) {
        if (snd_voice_slots[i].c4 == note && snd_voice_slots[i].c3 == dev) {
            (*g_7524[snd_instrument_descriptors[dev].count])(note, snd_voice_slots[i].num, dev);
            snd_voice_slots[i].c4 = 0;
            snd_voice_slots[i].c2 = 0;
            snd_voice_slots[i].c5 = 15;
        }
    }
}

extern struct Song far snd_effect_note_table[];

void far snd_start_configured_effect(int n)
{
    snd_start_instrument_note(snd_effect_note_table[n].b, snd_effect_note_table[n].c, snd_effect_note_table[n].a, snd_effect_note_table[n].d);
}

extern unsigned char far snd_port_read_byte(int port);
extern void far snd_port_write_byte(int port, int value);

/* CSE-1: the folded unsigned-byte >= 0 check retains the original byte
 * temporary and index spill. STEERED: original eliminated expression unknown. */
void far snd_stop_assigned_voices(void)
{
    int i;
    for (i = 0; snd_voice_slots[i].type; i++) {
        if (snd_voice_slots[i].c3 >= 0 && snd_voice_slots[i].c2)
            snd_stop_instrument_note(snd_voice_slots[i].c3, snd_voice_slots[i].c4);
    }
}

void far snd_mpu_write_data(int value)
{
    while (snd_port_read_byte(0x331) & 0x40)
        ;
    snd_port_write_byte(0x330, value);
}

void far snd_mpu_write_command(int value)
{
    while (snd_port_read_byte(0x331) & 0x40)
        ;
    snd_port_write_byte(0x331, value);
    do {
        while (snd_port_read_byte(0x331) & 0x80)
            ;
    } while (snd_port_read_byte(0x330) != 0xfe);
}

void far snd_midi_note_on(int dev, int a, int b, int c)
{
    int far *info;

    if (*(info = snd_instrument_descriptors[dev].info) != -1) {
        b += info[1];
        snd_mpu_write_command(0xd7);
        snd_mpu_write_data(c + 0x90);
        snd_mpu_write_data(snd_instrument_descriptors[dev].info[2] + a);
        snd_mpu_write_data(b);
    }
}

void far snd_midi_percussion_on(int dev, int a, int b)
{
    int far *info;

    info = snd_instrument_descriptors[dev].info;
    snd_mpu_write_command(0xd7);
    b += info[1];
    snd_mpu_write_data(0x99);
    snd_mpu_write_data(info[0]);
    snd_mpu_write_data(b);
}

void far snd_midi_note_off(int a, int b, int dev)
{
    snd_mpu_write_command(0xd7);
    snd_mpu_write_data(b + 0x80);
    snd_mpu_write_data(snd_instrument_descriptors[dev].info[2] + a);
    snd_mpu_write_data(0);
}

void far snd_midi_percussion_off(int a, int b, int dev)
{
    snd_mpu_write_command(0xd7);
    snd_mpu_write_data(0x89);
    snd_mpu_write_data(snd_instrument_descriptors[dev].info[0]);
    snd_mpu_write_data(0);
}

void far f_295C_0577(void)
{
}

void far snd_midi_select_program(int dev, int a)
{
    int far *info;

    info = snd_instrument_descriptors[dev].info;
    if (*info != -1) {
        snd_mpu_write_command(0xd7);
        snd_mpu_write_data(a + 0xc0);
        snd_mpu_write_data(*info);
    }
}
