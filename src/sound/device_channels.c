/*
 * Selects sound devices and builds their channel tables. It initializes and dispatches the voice
 * backends used by the sound driver.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 277E; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs.
 */

struct Chan {
    char type;
    char num;
    char c2;
    char c3;
    char c4;
    char c5;
};

struct Voice {
    int a;
    long b;
};

int far f_277E_0179(void);
int far snd_init_speaker_channels(void);
int far snd_init_tandy_channels(void);
int far snd_init_ps1_channels(void);
int far snd_init_adlib_channels(void);
int far snd_init_blaster_channels(void);
int far snd_init_regchip_channels(void);
int far snd_init_lpt_sample_channels(void);
int far snd_init_midi_channels(void);
void far f_277E_0938(void);
void far snd_shutdown_blaster_output(void);
void far snd_shutdown_opl_output(void);
void far snd_disable_pc_speaker(void);
void far snd_shutdown_regchip_output(void);

int (far *g_68B6[])(void) = {
    f_277E_0179, snd_init_speaker_channels, snd_init_tandy_channels, snd_init_ps1_channels, snd_init_adlib_channels,
    snd_init_regchip_channels, snd_init_blaster_channels, snd_init_lpt_sample_channels, snd_init_midi_channels
};

void (far *g_68DA[])(void) = {
    f_277E_0938, snd_disable_pc_speaker, f_277E_0938, f_277E_0938, f_277E_0938,
    snd_shutdown_regchip_output, snd_shutdown_blaster_output, snd_shutdown_opl_output, f_277E_0938
};

extern char g_68FE[];
extern char g_6908[];
extern char g_6912[];
extern int g_6924[];
extern int g_693C;

extern int (far * far fd_55B3_74DA[])(void);
void far snd_reset_channel_tables(void);
extern void far snd_control_interrupts_disable(void);
extern int far fd_50F6_4A48;
extern int far fd_50F6_4A4C;
extern void far snd_select_four_channel_timer(int a, int b);
extern void far snd_select_two_channel_timer(int a, int b);
extern void far snd_start_sample_timer(void);
extern void far snd_control_interrupts_enable(void);
extern int far fd_50F6_01F0[];
extern int far snd_expand_sample_resource(char far * far *handle, int far *size, int object, int type);
extern void far db_set_recall_hook(int (far *hook)(char far * far *handle, int far *size, int object, int type));

int far snd_initialize_device_channels(int mode, int flag)
{
    if (mode != 7 && !fd_55B3_74DA[mode]())
        mode = 1;
    snd_reset_channel_tables();
    snd_control_interrupts_disable();
    fd_50F6_4A48 = 2;
    if (mode == 7)
        flag = 1;
    if (flag)
        fd_50F6_4A48 = 4;
    fd_50F6_4A4C = 0;
    g_68B6[mode]();
    if (flag)
        snd_select_four_channel_timer(0xd6, 0x132);
    else
        snd_select_two_channel_timer(0xd6, 0x132);
    snd_start_sample_timer();
    snd_control_interrupts_enable();
    fd_50F6_01F0[0] = mode;
    db_set_recall_hook(snd_expand_sample_resource);
    return mode;
}

extern struct Chan far fd_50F6_4A4E[];

void far snd_reset_channel_tables(void)
{
    int i;

    for (i = 0; i < 0x21; i++) {
        fd_50F6_4A4E[i].type = 0;
        fd_50F6_4A4E[i].num = 0;
        fd_50F6_4A4E[i].c4 = 0;
        fd_50F6_4A4E[i].c5 = 15;
        fd_50F6_4A4E[i].c2 = 0;
        fd_50F6_4A4E[i].c3 = -1;
    }
    fd_50F6_01F0[1] = 0;
    fd_50F6_01F0[2] = 0;
    fd_50F6_01F0[3] = 0;
    fd_50F6_01F0[4] = 0;
    fd_50F6_01F0[5] = 0;
    fd_50F6_01F0[6] = 0;
}

extern struct Voice far fd_50F6_0000[];

void far snd_copy_instrument_table(struct Voice far *src)
{
    int i;

    for (i = 0; i < 0x38; i++) {
        fd_50F6_0000[i].a = src[i].a;
        fd_50F6_0000[i].b = src[i].b;
    }
}

extern void far snd_stop_assigned_voices(void);
extern void far snd_stop_and_release_samples(void);
extern void far snd_restore_bios_timer(int a);

void far snd_shutdown_device_channels(void)
{
    snd_stop_assigned_voices();
    snd_stop_and_release_samples();
    g_68DA[fd_50F6_01F0[0]]();
    snd_restore_bios_timer(0);
}

int far f_277E_0179(void)
{
    return 1;
}

extern int far fd_55B3_74AD;
extern int far fd_55B3_6B9C;
extern int far fd_55B3_74C0;
extern struct Voice far fd_55B3_0C42[];

int far snd_init_speaker_channels(void)
{
    int i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_55B3_6B9C = fd_55B3_74AD;
    fd_55B3_74C0 = 0x40;
    snd_copy_instrument_table(fd_55B3_0C42);
    return 1;
}

extern int far fd_50F6_4A4A;
extern int far fd_50F6_4B14;
extern int far fd_55B3_6B4A;
extern void far snd_port_write_byte(int port, char value);
extern int far fd_55B3_74B9;

extern struct Voice far fd_55B3_1032[];
extern struct Voice far fd_55B3_1182[];
int far snd_init_tandy_channels(void)
{
    int i;
    int base;
    char far *bios;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    bios = (char far *)0xF000FFFEL;
    fd_50F6_4A4A = fd_55B3_74C0 = 0;
    base = 0xc4;
    _asm {
        mov ax, 8100h
        int 1Ah
        cmp ax, 0C4h
        jne notandy
        mov base, ax
    }
    fd_50F6_4A4A = 0;
notandy:
    for (i = 0; i < 3; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 5;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[4] = 3;
    if (*bios == 0xfc)
        fd_50F6_4B14 = 0x1e0;
    else
        fd_50F6_4B14 = 0xc0;
    if (fd_50F6_4A4A) {
        snd_port_write_byte(fd_55B3_6B4A = base, 3);
        fd_55B3_6B9C = fd_55B3_74B9;
        snd_copy_instrument_table(fd_55B3_1182);
    } else {
        fd_55B3_6B9C = fd_55B3_74AD;
        snd_copy_instrument_table(fd_55B3_1032);
    }
    return 1;
}

extern int far fd_55B3_74B3;

int far snd_init_ps1_channels(void)
{
    int i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    for (i = 0; i < 3; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 3;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[3] = 3;
    snd_port_write_byte(0x203, 1);
    fd_55B3_6B9C = fd_55B3_74B3;
    fd_55B3_74C0 = 0;
    return 1;
}

extern void far snd_opl_reset_voices(void);
extern void far snd_opl_probe_tone(void);
extern int far fd_55B3_74AF;
extern int far fd_50F6_4B16;

extern struct Voice far fd_55B3_0D92[];
int far snd_init_adlib_channels(void)
{
    int i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    for (i = 0; i < 7; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 2;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i + 1;
    }
    snd_opl_reset_voices();
    fd_50F6_01F0[2] = 7;
    snd_opl_probe_tone();
    snd_control_interrupts_disable();
    fd_55B3_6B9C = fd_55B3_74AF;
    snd_copy_instrument_table(fd_55B3_0D92);
    fd_50F6_4B16 = -40;
    fd_55B3_74C0 = 0x60;
    return 1;
}

extern unsigned int far fd_55B3_7564;
extern int far snd_find_blaster_dsp_base(void);
extern int far fd_55B3_6BA0;
extern unsigned char far snd_port_read_byte(int port);
extern int far fd_55B3_74B5;

int far snd_init_blaster_channels(void)
{
    unsigned i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    snd_opl_reset_voices();
    for (i = 0; i < 8; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 2;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[2] = 8;
    fd_55B3_74C0 = -10;
    if (fd_55B3_7564 < 0x210) {
        snd_find_blaster_dsp_base();
        fd_55B3_6BA0 = fd_55B3_7564 + 12;
        while (snd_port_read_byte(fd_55B3_6BA0) & 0x80)
            ;
    }
    fd_55B3_6BA0 = fd_55B3_7564 + 12;
    fd_55B3_6B9C = fd_55B3_74B5;
    snd_copy_instrument_table(fd_55B3_0D92);
    snd_port_write_byte(fd_55B3_6BA0, 0xd1);
    return 1;
}

extern void far snd_find_regchip_base(void);
extern int far fd_50F6_4A46;
extern int far snd_probe_opl_timer(void);
extern int far fd_55B3_74B7;
extern void far snd_regchip_initialize(int port);

extern struct Voice far fd_55B3_1572[];
int far snd_init_regchip_channels(void)
{
    int i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    for (i = 0; i < 3; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 4;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[5] = 3;
    if (fd_50F6_4B14 == 0)
        snd_find_regchip_base();
    if (fd_50F6_4B14 == 0)
        fd_50F6_4B14 = 0x220;
    fd_50F6_4A46 = fd_50F6_4B14 + 2;
    if (snd_probe_opl_timer()) {
        snd_copy_instrument_table(fd_55B3_0D92);
        snd_opl_reset_voices();
        for (i = 0; i < 8; i++, fd_50F6_4A4C++) {
            fd_50F6_4A4E[fd_50F6_4A4C].type = 2;
            fd_50F6_4A4E[fd_50F6_4A4C].num = i;
        }
        fd_50F6_01F0[2] = 8;
    } else
        snd_copy_instrument_table(fd_55B3_1572);
    fd_55B3_6B9C = fd_55B3_74B7;
    snd_regchip_initialize(fd_50F6_4B14);
    fd_55B3_74C0 = 0;
    return 1;
}

extern int far fd_55B3_74B1;

extern struct Voice far fd_55B3_0EE2[];
int far snd_init_lpt_sample_channels(void)
{
    int i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    _asm {
        sub bx, bx
        mov es, bx
        mov bx, 408h
        mov ax, es:[bx]
        mov g_693C, ax
        mov dx, g_693C
        add dx, 2
        in al, dx
        and al, 0F7h
        out dx, al
    }
    fd_55B3_6B9C = fd_55B3_74B1;
    snd_copy_instrument_table(fd_55B3_0EE2);
    fd_55B3_74C0 = 0;
    return 1;
}

extern void far snd_mpu_write_command(int c);
extern void far snd_mpu_write_data(int c);

extern struct Voice far fd_55B3_12D2[];
extern struct Voice far fd_55B3_1422[];
int far snd_init_midi_channels(void)
{
    int i;

    fd_50F6_01F0[6] = 8;
    if (snd_find_blaster_dsp_base()) {
        snd_init_blaster_channels();
        snd_copy_instrument_table(fd_55B3_1422);
    } else {
        snd_init_speaker_channels();
        snd_copy_instrument_table(fd_55B3_12D2);
    }
    fd_55B3_74C0 = 0;
    for (i = 0; i < 8; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 6;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i + 1;
    }
    for (i = 0; i < 10; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 7;
        fd_50F6_4A4E[fd_50F6_4A4C].num = 10;
    }
    snd_mpu_write_command(0x8a);
    snd_mpu_write_command(0xd7);
    for (i = 0; i < 16; i++) {
        snd_mpu_write_command(0xd7);
        snd_mpu_write_data(i + 0xb0);
        snd_mpu_write_data(0x79);
        snd_mpu_write_data(0);
        snd_mpu_write_data(i + 0xb0);
        snd_mpu_write_data(0x7b);
        snd_mpu_write_data(0);
        snd_mpu_write_data(i + 0xb0);
        snd_mpu_write_data(10);
        snd_mpu_write_data(0x40);
        snd_mpu_write_data(i + 0xb0);
        snd_mpu_write_data(7);
        snd_mpu_write_data(0x7f);
    }
    return 1;
}

void far f_277E_0938(void)
{
}

void far snd_shutdown_blaster_output(void)
{
    snd_port_write_byte(fd_55B3_6BA0, 0xd3);
    snd_opl_reset_voices();
}

void far snd_shutdown_opl_output(void)
{
    snd_opl_reset_voices();
}

void far snd_disable_pc_speaker(void)
{
    _asm {
        in al, 61h
        and al, 0FCh
        out 61h, al
    }
}

void far snd_shutdown_regchip_output(void)
{
    _asm {
        mov al, 5
        out 0Ah, al
        mov al, 0Fh
        mov dx, 220h
        out dx, al
        mov al, 60h
        inc dx
        out dx, al
    }
}
