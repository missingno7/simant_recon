/*
 * Controls AdLib OPL2 voices and their instrument settings. It converts note, pitch and volume
 * data into chip register writes.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 2815; partial original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Functions not yet exact: f_2815_0165.
 */

struct Instr {
    int a;
    unsigned char far *p;
};

char g_68FE[] = { 0, 1, 2, 6, 7, 8, 12, 13, 14 };
char g_6908[] = { 3, 4, 5, 9, 10, 11, 15, 16, 17 };
char g_6912[] = { 0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21 };
int g_6924[] = { 0x157, 0x16b, 0x181, 0x198, 0x1b0, 0x1ca, 0x1e5, 0x202, 0x220, 0x241, 0x263, 0x287 };

extern void far snd_opl_write(char reg, char value);

void far f_2815_000A(char far *p, int voice)
{
    char op1;
    char op2;

    op1 = g_6912[g_68FE[voice]];
    op2 = g_6912[g_6908[voice]];
    snd_opl_write(op1 + 0x20, p[1]);
    snd_opl_write(op2 + 0x20, p[0]);
    snd_opl_write(op1 + 0x40, p[3]);
    snd_opl_write(op2 + 0x40, p[2]);
    snd_opl_write(op1 + 0x60, p[5]);
    snd_opl_write(op2 + 0x60, p[4]);
    snd_opl_write(op1 + 0x80, p[7]);
    snd_opl_write(op2 + 0x80, p[6]);
    snd_opl_write(op1 + 0xe0, p[10]);
    snd_opl_write(op2 + 0xe0, p[9]);
    snd_opl_write(voice + 0xc0, p[8]);
}

void far f_2815_0118(void)
{
    int i;

    snd_opl_write(1, 0);
    snd_opl_write(4, 0x80);
    snd_opl_write(8, 0);
    snd_opl_write(0xbd, 0xc0);
    for (i = 0; i < 8; i++)
        snd_opl_write(i + 0xb0, 0);
}

extern int far fd_50F6_4B16;
extern struct Instr far fd_50F6_0000[];
extern int far fd_55B3_6BA4[];


void far f_2815_0165(int instr, int note, int vol, int voice)
{
    unsigned char far *p;

    vol += fd_50F6_4B16;
    p = fd_50F6_0000[instr].p;
    vol += *(int far *)(p + 0xd);
    if (vol < 0)
        vol = 0;
    if (vol > 0x7f)
        vol = 0x7f;
    snd_opl_write(g_6912[g_6908[voice]] + 0x40,
                ((unsigned)(0x3f - (unsigned char)fd_55B3_6BA4[vol]) * ((p[2] & 0x3f) ^ 0x3f) >> 6 ^ 0x3f) | (p[2] & 0xc0));
    note += *(int far *)(p + 0xb) * 12;
    if (note >= 0 && note <= 0x7f) {
        snd_opl_write(voice + 0xa0, g_6924[note % 12]);
        snd_opl_write(voice + 0xb0, ((note / 12 + 8) << 2) + (g_6924[note % 12] >> 8));
    }
}


void far f_2815_024D(int a, int voice)
{
    snd_opl_write(voice + 0xa0, 0);
    snd_opl_write(voice + 0xb0, 0);
}

void far f_2815_0275(int instr, int voice)
{
    f_2815_000A(fd_50F6_0000[instr].p, voice);
}
