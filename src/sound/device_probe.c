/*
 * Probes available sound devices. It performs port tests and selects the hardware capabilities
 * reported to the sound layer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 293A; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Steered functions: snd_probe_mpu_reset.
 */

int far snd_probe_assume_present(void);
int far snd_probe_tandy_sound(void);
int far snd_probe_ps1_sound(void);
int far snd_probe_opl_timer(void);
int far snd_find_blaster_dsp_base(void);
int far snd_find_regchip_base(void);
int far snd_probe_lpt_unavailable(void);
int far snd_probe_mpu_reset(void);

extern int far snd_driver_capabilities[];

int (far *snd_driver_probe_table[])(void) = {
    snd_probe_assume_present, snd_probe_assume_present, snd_probe_tandy_sound, snd_probe_ps1_sound, snd_probe_opl_timer,
    snd_find_regchip_base, snd_find_blaster_dsp_base, snd_probe_lpt_unavailable, snd_probe_mpu_reset
};
/*
 * Pointer to the mode and channel-count report cells.
 */
int far *snd_capabilities_pointer = snd_driver_capabilities;

/*
 * Return the highest numbered successful sound-device probe.
 */
int far snd_probe_preferred_device(void)
{
    int i;
    int found;

    found = 0;
    for (i = 8; i > 0; i--) {
        if (snd_driver_probe_table[i]()) {
            found = i;
            break;
        }
    }
    return found;
}

/*
 * Unconditionally accept the fallback sound probe.
 */
int far snd_probe_assume_present(void)
{
    return 1;
}

/*
 * Test the Tandy sound BIOS response or ROM model byte.
 */
int far snd_probe_tandy_sound(void)
{
    char far *p;
    int base;

    _asm {
        mov ah, 81h
        int 1Ah
        mov base, ax
    }
    p = (char far *)0xFC000000L;
    return *p == 0x21 || base == 0xc4;
}

/*
 * Test the BIOS model word and CMOS sound-enable bit for the PS/1 backend.
 */
int far snd_probe_ps1_sound(void)
{
    _asm {
        push es
        mov ax, 0C000h
        int 15h
        add bx, 2
        mov ax, es:[bx]
        pop es
        cmp ax, 0BFCh
        jne none
        mov al, 2Fh
        cli
        out 70h, al
        jmp short delay
    delay:
        in al, 71h
        sti
        test al, 10h
        je none
    }
    return 1;
none:
    return 0;
}

extern void far snd_opl_write(char reg, char value);
extern unsigned char far snd_port_read_byte(int port);

/*
 * Detect OPL timer operation at port 388h and reset the timers afterwards.
 */
int far snd_probe_opl_timer(void)
{
    int s1;
    unsigned i;

    snd_opl_write(4, 0x60);
    snd_opl_write(4, 0x80);
    s1 = snd_port_read_byte(0x388);
    snd_opl_write(2, 0xff);
    snd_opl_write(4, 0x21);
    for (i = 0; i < 200; i++)
        snd_port_read_byte(0x388);
    i = snd_port_read_byte(0x388);
    snd_opl_write(4, 0x60);
    snd_opl_write(4, 0x80);
    if ((s1 & 0xe0) == 0 && (i & 0xe0) == 0xc0)
        return 1;
    return 0;
}

extern unsigned far snd_sb_io_base;
extern int far snd_probe_dsp_reset_ack(void);

/*
 * Probe DSP bases 210h through 260h and retain the tested base.
 */
int far snd_find_blaster_dsp_base(void)
{
    int found;

    found = 0;
    snd_sb_io_base = 0x200;
    while (!found) {
        if (snd_sb_io_base >= 0x260)
            break;
        snd_sb_io_base += 0x10;
        found = snd_probe_dsp_reset_ack();
    }
    return found;
}

extern int far snd_regchip_detect(void);
extern int far snd_device_io_base;

/*
 * Store the detected register-chip base port and report success.
 */
int far snd_find_regchip_base(void)
{
    int port;

    if ((port = snd_regchip_detect()) == 0)
        return 0;
    snd_device_io_base = port;
    return 1;
}

/*
 * Reject automatic selection of the LPT backend.
 */
int far snd_probe_lpt_unavailable(void)
{
    return 0;
}

extern void far snd_port_write_byte(int port, char value);

/*
 * Probe MPU reset acknowledgement with bounded polling retries.
 */
int far snd_probe_mpu_reset(void)
{
    int i;
    int tries;
    int ok;
    int ready;

    ok = 0;
    ready = 0;
    if (!(snd_port_read_byte(0x331) & 0x80))
        snd_port_read_byte(0x330);
    for (i = 0; i < 5000; i++) {
        if (!(snd_port_read_byte(0x331) & 0x40)) {
            ok = 1;
            goto write_ready;
        }
    }
write_ready:
    if (ok) {
        snd_port_write_byte(0x331, 0xff);
        for (tries = 0; tries < 3 && ((unsigned)ok >= 0); tries++) {
            for (i = 0; i < 5000; i++) {
                if (!(snd_port_read_byte(0x331) & 0x80)) {
                    ready = 1;
                    goto read_ready;
                }
            }
read_ready:
            if (ready) {
                if (snd_port_read_byte(0x330) == 0xfe)
                    return 1;
                ready = 0;
            }
        }
    }
    return 0;
}

/* snd_probe_mpu_reset is STEERED: the folded unsigned flag check retains the original
 * stack homes. The eliminated original expression is unknown; LIFE-1 keeps
 * the whole-module positive and negative controls. The two polling continuation
 * labels are inferred from relocation record boundaries (ZI-2). */
