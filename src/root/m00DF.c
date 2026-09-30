/* Module at root frame 00DF (large-model code segment): sound driver shell. */

int g_1926 = 0;

extern int far fd_55B3_610A;
extern int far f_293A_0006(void);
extern int far f_277E_0000(int mode, int flag);
extern void far WinPrintf(char *fmt, ...);
extern int far * far fd_55B3_74FE;

void far f_00DF_0004(void)
{
    if (g_1926)
        return;
    if (fd_55B3_610A == -1)
        f_277E_0000(f_293A_0006(), 0);
    else if (fd_55B3_610A == 0)
        return;
    else
        f_277E_0000(fd_55B3_610A, 0);
    WinPrintf("Sound Driver Shell (c) 1991  -- LIB link version\n");
    WinPrintf("Sound Driver reports driver: %d\n%d DAC channels\n%d FM channels\n%d TANDY PSG channels\n%d PS1 PSG channels\n%d COVOX PSG channels\nand %d MIDI channels\n",
              fd_55B3_74FE[0], fd_55B3_74FE[1], fd_55B3_74FE[2], fd_55B3_74FE[4],
              fd_55B3_74FE[3], fd_55B3_74FE[5], fd_55B3_74FE[6]);
    g_1926 = 1;
}

void far f_00DF_0089(void)
{
    WinPrintf("MUSIC INIT!");
}

void far f_00DF_009D(void)
{
    WinPrintf("BEEP");
}

extern int far fd_3D57_07A8[];
extern void far f_0250_01E7(void);
extern void far f_284A_0013(int song);

void far f_00DF_00B1(int song)
{
    if (g_1926 && fd_3D57_07A8[1]) {
        f_0250_01E7();
        f_284A_0013(song);
    }
}

void far f_00DF_00E0(void)
{
}

extern void far f_295C_0367(int sound);

void far myBeginSound(int a, int b, int c)
{
    if (g_1926 && fd_3D57_07A8[2])
        f_295C_0367(a);
}

void far f_00DF_0112(int a, int b, int c)
{
    myBeginSound(a, b, c);
}

int far f_00DF_012D(void)
{
    return 1;
}

extern int far f_284A_0004(void);

int far f_00DF_0138(void)
{
    if (g_1926 && fd_3D57_07A8[1])
        return f_284A_0004();
    return 1;
}

void far f_00DF_015C(void)
{
}

void far f_00DF_0164(void)
{
}

void far f_00DF_016C(void)
{
    if (g_1926 && fd_3D57_07A8[1])
        f_295C_0367(1);
}
