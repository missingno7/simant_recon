/*
 * Outputs notes and controls voices for additional PSG style devices. It uses port 205h and the
 * register interface in the preceding sound chip module.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 29D6; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

int g_75E8[] = {
    0x1ddd, 0x1c31, 0x1a9c, 0x191b, 0x17b4, 0x165e, 0x151f, 0x13ee,
    0x12cf, 0x11c1, 0x10c1, 0xfd1
};
unsigned g_7600[] = {
    0x3574, 0x3274, 0x2f9f, 0x2cf3, 0x2a6d, 0x280b, 0x25cc, 0x23ad,
    0x21ac, 0x1fc8, 0x1e00, 0x1c51, 0x1aba, 0x193a, 0x17cf, 0x1679,
    0x1536, 0x1406, 0x12e6, 0x11d6, 0x10d6, 0xfe4, 0xf00, 0xe28,
    0xd5d, 0xc9d, 0xbe8, 0xb3d, 0xa9b, 0xa03, 0x973, 0x8eb,
    0x86b, 0x7f2, 0x780, 0x714, 0x6ae, 0x64e, 0x5f4, 0x59e,
    0x54e, 0x501, 0x4b9, 0x476, 0x436, 0x3f9, 0x3c0, 0x38a,
    0x357, 0x327, 0x2fa, 0x2cf, 0x2a7, 0x281, 0x25d, 0x23b,
    0x21b, 0x1fd, 0x1e0, 0x1c5, 0x1ac, 0x194, 0x17d, 0x168,
    0x153, 0x140, 0x12e, 0x11d, 0x10d, 0xfe, 0xf0, 0xe3,
    0xd6, 0xca, 0xbe, 0xb4, 0xaa, 0xa0, 0x97, 0x8f,
    0x87, 0x7f, 0x78, 0x71, 0x6b, 0x65, 0x5f, 0x5a,
    0x55, 0x50, 0x4c, 0x47, 0x43, 0x40, 0x3c, 0x39,
    0x35, 0x32, 0x30, 0x2d, 0x2a, 0x28, 0x26, 0x24,
    0x22, 0x20, 0x1e, 0x1c, 0x1b, 0x19, 0x18, 0x16,
    0x15, 0x14, 0x13, 0x12, 0x11, 0x10, 0xf, 0xe,
    0xd, 0xd, 0xc, 0xb, 0xb, 0xa, 0x9, 0x9
};

extern void far snd_port_write_byte(int port, char value);

extern void far snd_regchip_write(int reg, int value);
extern int far snd_device_io_base;
/*
 * Write PSG pitch and attenuation for a PS/1 voice at port 205h.
 */
void far snd_ps1_set_note(int a, int note, int vol, int chan)
{
    int f;

    chan <<= 5;
    f = g_75E8[note % 12] >> note / 12;
    chan += 0x80;
    snd_port_write_byte(0x205, (f & 0xf) + (char)chan);
    snd_port_write_byte(0x205, f >> 4);
    vol >>= 3;
    vol = 0xf - vol;
    snd_port_write_byte(0x205, vol + (char)chan + 0x10);
}


/*
 * Set register-chip pitch one octave down and force level 1Fh, ignoring requested volume.
 */
void far snd_regchip_set_note(int a, int note, int vol, int ch)
{
    int n;
    int f;

    vol = 0x1f;
    note -= 12;
    if (note < 0)
        note = 0;
    f = g_7600[note];
    snd_regchip_write(ch * 2, f & 0xff);
    snd_regchip_write(ch * 2 + 1, f >> 8);
    snd_regchip_write(ch + 8, vol);
}


/*
 * Write Tandy PSG pitch and attenuation to the configured port.
 */
void far snd_tandy_set_note(int a, int note, int vol, int ch)
{
    unsigned freq;
    char reg;
    int port;
    int val;
    int tmp;

    ch <<= 5;
    reg = (char)ch + 0x80 & 0xe0;
    val = ~(vol >> 3) & 0xf;
    tmp = 0;
    port = snd_device_io_base;
    freq = g_7600[note] >> 1;
    _asm {
        mov dx, port
        mov ax, freq
        push ax
        and ax, 0Fh
        add ax, reg
        mov bx, ax
        pop ax
        and ax, 3F0h
        mov cx, 4
        shr ax, cl
        mov ah, al
        mov al, bl
        out dx, ax
        xor ax, ax
        mov ax, reg
        add ax, 10h
        add ax, val
        out dx, al
    }
}

/*
 * Set maximum PSG attenuation for the PS/1 voice.
 */
void far snd_ps1_silence_voice(int note, int ch)
{
    snd_ps1_set_note(0, note, 0, ch);
}

/*
 * Clear the register-chip voice level and pitch registers.
 */
void far snd_regchip_silence_voice(int a, int ch)
{
    snd_regchip_write(ch + 8, 0);
    snd_regchip_write(ch * 2, 0);
    snd_regchip_write(ch * 2 + 1, 0);
}

/*
 * Set maximum PSG attenuation for the Tandy voice.
 */
void far snd_tandy_silence_voice(int a, int ch)
{
    snd_tandy_set_note(0, 0, 0, ch);
}
