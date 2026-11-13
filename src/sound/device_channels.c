/*
 * Selects sound devices and builds their channel tables. It initializes and dispatches the voice
 * backends used by the sound driver.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 277E; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs.
 */

#include "hardware_ids.h"

#include "chan.h"

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

int (far *snd_driver_init_table[])(void) = {
    f_277E_0179, snd_init_speaker_channels, snd_init_tandy_channels, snd_init_ps1_channels, snd_init_adlib_channels,
    snd_init_regchip_channels, snd_init_blaster_channels, snd_init_lpt_sample_channels, snd_init_midi_channels
};

void (far *snd_driver_stop_table[])(void) = {
    f_277E_0938, snd_disable_pc_speaker, f_277E_0938, f_277E_0938, f_277E_0938,
    snd_shutdown_regchip_output, snd_shutdown_blaster_output, snd_shutdown_opl_output, f_277E_0938
};

extern char opl_modulator_indices[];
extern char opl_carrier_indices[];
extern char opl_operator_register_offsets[];
extern int opl_semitone_f_numbers[];
extern int snd_lpt_dac_port;

extern int (far * far snd_driver_probe_table[])(void);
void far snd_reset_channel_tables(void);
extern void far snd_control_interrupts_disable(void);
extern int far snd_sample_channel_count;
extern int far snd_voice_build_index;
extern void far snd_select_four_channel_timer(int a, int b);
extern void far snd_select_two_channel_timer(int a, int b);
extern void far snd_start_sample_timer(void);
extern void far snd_control_interrupts_enable(void);
extern int far snd_driver_capabilities[];
extern int far snd_expand_sample_resource(char far * far *handle, int far *size, int object, int type);
extern void far db_set_recall_hook(int (far *hook)(char far * far *handle, int far *size, int object, int type));

/*
 * Initialize the selected sound backend, channel tables, timer and sample hook.
 */
int far snd_initialize_device_channels(int mode, int flag)
{
    if (mode != 7 && !snd_driver_probe_table[mode]())
        mode = 1;
    snd_reset_channel_tables();
    snd_control_interrupts_disable();
    snd_sample_channel_count = 2;
    if (mode == 7)
        flag = 1;
    if (flag)
        snd_sample_channel_count = 4;
    snd_voice_build_index = 0;
    snd_driver_init_table[mode]();
    if (flag)
        snd_select_four_channel_timer(0xd6, 0x132);
    else
        snd_select_two_channel_timer(0xd6, 0x132);
    snd_start_sample_timer();
    snd_control_interrupts_enable();
    snd_driver_capabilities[0] = mode;
    db_set_recall_hook(snd_expand_sample_resource);
    return mode;
}

extern struct Chan far snd_voice_slots[];

/*
 * Reset all 33 channel records and clear device channel counts.
 */
void far snd_reset_channel_tables(void)
{
    int i;

    for (i = 0; i < 0x21; i++) {
        snd_voice_slots[i].type = 0;
        snd_voice_slots[i].num = 0;
        snd_voice_slots[i].note = 0;
        snd_voice_slots[i].age = 15;
        snd_voice_slots[i].priority = 0;
        snd_voice_slots[i].instrument = -1;
    }
    snd_driver_capabilities[1] = 0;
    snd_driver_capabilities[2] = 0;
    snd_driver_capabilities[3] = 0;
    snd_driver_capabilities[4] = 0;
    snd_driver_capabilities[5] = 0;
    snd_driver_capabilities[6] = 0;
}

extern struct Voice far snd_instrument_descriptors[];

/*
 * Copy 56 instrument descriptors into the driver's dispatch table.
 */
void far snd_copy_instrument_table(struct Voice far *src)
{
    int i;

    for (i = 0; i < 0x38; i++) {
        snd_instrument_descriptors[i].a = src[i].a;
        snd_instrument_descriptors[i].b = src[i].b;
    }
}

extern void far snd_stop_assigned_voices(void);
extern void far snd_stop_and_release_samples(void);
extern void far snd_restore_bios_timer(int a);

/*
 * Stop sound resources, shut down the selected backend and restore the timer.
 */
void far snd_shutdown_device_channels(void)
{
    snd_stop_assigned_voices();
    snd_stop_and_release_samples();
    snd_driver_stop_table[snd_driver_capabilities[0]]();
    snd_restore_bios_timer(0);
}

int far f_277E_0179(void)
{
    return 1;
}

extern int far snd_speaker_output_pointer;
extern int far snd_sample_output_routine;
extern int far snd_sample_volume_bias;
extern struct Voice far fd_55B3_0C42[];

/*
 * Configure sample channels for PC speaker output and its instrument table.
 */
int far snd_init_speaker_channels(void)
{
    int i;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    snd_sample_output_routine = snd_speaker_output_pointer;
    snd_sample_volume_bias = 0x40;
    snd_copy_instrument_table(fd_55B3_0C42);
    return 1;
}

extern int far fd_50F6_4A4A;
extern int far snd_device_io_base;
extern int far snd_dac_io_base;
extern void far snd_port_write_byte(int port, char value);
extern int far snd_based_dac_output_pointer;

extern struct Voice far fd_55B3_1032[];
extern struct Voice far fd_55B3_1182[];
/*
 * Configure sampled output and three Tandy PSG voices from BIOS information.
 */
int far snd_init_tandy_channels(void)
{
    int i;
    int base;
    char far *bios;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    bios = (char far *)BIOS_MODEL_BYTE_FARPTR;
    fd_50F6_4A4A = snd_sample_volume_bias = 0;
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
    for (i = 0; i < 3; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 5;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    snd_driver_capabilities[4] = 3;
    if (*bios == 0xfc)
        snd_device_io_base = SND_TANDY_AT_IO_BASE;
    else
        snd_device_io_base = 0xc0;
    if (fd_50F6_4A4A) {
        snd_port_write_byte(snd_dac_io_base = base, 3);
        snd_sample_output_routine = snd_based_dac_output_pointer;
        snd_copy_instrument_table(fd_55B3_1182);
    } else {
        snd_sample_output_routine = snd_speaker_output_pointer;
        snd_copy_instrument_table(fd_55B3_1032);
    }
    return 1;
}

extern int far snd_port200_output_pointer;

/*
 * Configure sample output and three PS/1 PSG voices, enabling port 203h.
 */
int far snd_init_ps1_channels(void)
{
    int i;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    for (i = 0; i < 3; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 3;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    snd_driver_capabilities[3] = 3;
    snd_port_write_byte(PORT_PS1_INITIALIZE, 1);
    snd_sample_output_routine = snd_port200_output_pointer;
    snd_sample_volume_bias = 0;
    return 1;
}

extern void far snd_opl_reset_voices(void);
extern void far snd_opl_probe_tone(void);
extern int far snd_adlib_output_pointer;
extern int far snd_opl_volume_bias;

extern struct Voice far fd_55B3_0D92[];
/*
 * Configure AdLib sample output and seven OPL voices.
 */
int far snd_init_adlib_channels(void)
{
    int i;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    for (i = 0; i < 7; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 2;
        snd_voice_slots[snd_voice_build_index].num = i + 1;
    }
    snd_opl_reset_voices();
    snd_driver_capabilities[2] = 7;
    snd_opl_probe_tone();
    snd_control_interrupts_disable();
    snd_sample_output_routine = snd_adlib_output_pointer;
    snd_copy_instrument_table(fd_55B3_0D92);
    snd_opl_volume_bias = -40;
    snd_sample_volume_bias = 0x60;
    return 1;
}

extern unsigned int far snd_sb_io_base;
extern int far snd_find_blaster_dsp_base(void);
extern int far snd_sb_dsp_write_port;
extern unsigned char far snd_port_read_byte(int port);
extern int far snd_sb_output_pointer;

/*
 * Configure Sound Blaster sample output, OPL channels and DSP speaker enable.
 */
int far snd_init_blaster_channels(void)
{
    unsigned i;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    snd_opl_reset_voices();
    for (i = 0; i < 8; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 2;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    snd_driver_capabilities[2] = 8;
    snd_sample_volume_bias = -10;
    if (snd_sb_io_base < SND_BLASTER_FIRST_PROBE_BASE) {
        snd_find_blaster_dsp_base();
        snd_sb_dsp_write_port = snd_sb_io_base + 12;
        while (snd_port_read_byte(snd_sb_dsp_write_port) & 0x80)
            ;
    }
    snd_sb_dsp_write_port = snd_sb_io_base + 12;
    snd_sample_output_routine = snd_sb_output_pointer;
    snd_copy_instrument_table(fd_55B3_0D92);
    snd_port_write_byte(snd_sb_dsp_write_port, 0xd1);
    return 1;
}

extern void far snd_find_regchip_base(void);
extern int far fd_50F6_4A46;
extern int far snd_probe_opl_timer(void);
extern int far snd_port222_output_pointer;
extern void far snd_regchip_initialize(int port);

extern struct Voice far fd_55B3_1572[];
/*
 * Configure register-chip voices and add OPL voices when detected.
 */
int far snd_init_regchip_channels(void)
{
    int i;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    for (i = 0; i < 3; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 4;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    snd_driver_capabilities[5] = 3;
    if (snd_device_io_base == 0)
        snd_find_regchip_base();
    if (snd_device_io_base == 0)
        snd_device_io_base = SND_REGCHIP_DEFAULT_IO_BASE;
    fd_50F6_4A46 = snd_device_io_base + 2;
    if (snd_probe_opl_timer()) {
        snd_copy_instrument_table(fd_55B3_0D92);
        snd_opl_reset_voices();
        for (i = 0; i < 8; i++, snd_voice_build_index++) {
            snd_voice_slots[snd_voice_build_index].type = 2;
            snd_voice_slots[snd_voice_build_index].num = i;
        }
        snd_driver_capabilities[2] = 8;
    } else
        snd_copy_instrument_table(fd_55B3_1572);
    snd_sample_output_routine = snd_port222_output_pointer;
    snd_regchip_initialize(snd_device_io_base);
    snd_sample_volume_bias = 0;
    return 1;
}

extern int far snd_lpt_output_pointer;

extern struct Voice far fd_55B3_0EE2[];
/*
 * Configure sampled output through the BIOS LPT1 port.
 */
int far snd_init_lpt_sample_channels(void)
{
    int i;

    snd_driver_capabilities[1] = snd_sample_channel_count;
    for (i = 0; i < snd_sample_channel_count; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 1;
        snd_voice_slots[snd_voice_build_index].num = i;
    }
    _asm {
        sub bx, bx
        mov es, bx
        mov bx, 408h
        mov ax, es:[bx]
        /*
         * BIOS-selected LPT data port used for sample output.
         */
        mov snd_lpt_dac_port, ax
        mov dx, snd_lpt_dac_port
        add dx, 2
        in al, dx
        and al, 0F7h
        out dx, al
    }
    snd_sample_output_routine = snd_lpt_output_pointer;
    snd_copy_instrument_table(fd_55B3_0EE2);
    snd_sample_volume_bias = 0;
    return 1;
}

extern void far snd_mpu_write_command(int c);
extern void far snd_mpu_write_data(int c);

extern struct Voice far fd_55B3_12D2[];
extern struct Voice far fd_55B3_1422[];
/*
 * Configure MIDI channels and reset their controllers through the MPU interface.
 */
int far snd_init_midi_channels(void)
{
    int i;

    snd_driver_capabilities[6] = 8;
    if (snd_find_blaster_dsp_base()) {
        snd_init_blaster_channels();
        snd_copy_instrument_table(fd_55B3_1422);
    } else {
        snd_init_speaker_channels();
        snd_copy_instrument_table(fd_55B3_12D2);
    }
    snd_sample_volume_bias = 0;
    for (i = 0; i < 8; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 6;
        snd_voice_slots[snd_voice_build_index].num = i + 1;
    }
    for (i = 0; i < 10; i++, snd_voice_build_index++) {
        snd_voice_slots[snd_voice_build_index].type = 7;
        snd_voice_slots[snd_voice_build_index].num = 10;
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

/*
 * Disable the DSP speaker and reset OPL state.
 */
void far snd_shutdown_blaster_output(void)
{
    snd_port_write_byte(snd_sb_dsp_write_port, 0xd3);
    snd_opl_reset_voices();
}

/*
 * Reset OPL state through the backend shutdown hook.
 */
void far snd_shutdown_opl_output(void)
{
    snd_opl_reset_voices();
}

/*
 * Clear the PC speaker gate and enable bits at port 61h.
 */
void far snd_disable_pc_speaker(void)
{
    _asm {
        in al, 61h
        and al, 0FCh
        out 61h, al
    }
}

/*
 * Mask DMA channel 1 and write the register-chip shutdown values at 220h/221h.
 */
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
